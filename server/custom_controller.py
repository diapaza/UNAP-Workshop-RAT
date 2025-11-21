from server_controller import ControladorServidor
import json
import os

class CustomControlador(ControladorServidor):
    def __init__(self, servidor_socket, gui):
        super().__init__(servidor_socket)
        self.gui = gui
        
    def procesar_respuesta_cliente(self, datos, cliente):
        super().procesar_respuesta_cliente(datos, cliente)
        
        try:
            datos_dict = json.loads(datos)
            accion = datos_dict.get("accion")
            cliente_ip = cliente['direccion'][0]
            
            if accion == "respuesta_ejecucion":
                self.gui.log(f"[Cliente {cliente_ip}] Resultado de ejecución:")
                self.gui.log(datos_dict.get("resultado", "Sin resultado"))
                
            elif accion == "archivo_recibido":
                self.gui.log(f"[Cliente {cliente_ip}] Archivo guardado: {datos_dict.get('ruta_destino')}")
                
            elif accion == "respuesta_listado":
                self.gui.log(f"[Cliente {cliente_ip}] Estructura del directorio '{datos_dict.get('ruta')}':")
                self.gui.log(datos_dict.get("estructura"))
                
            elif accion == "archivo_enviado":
                self.gui.log(f"[Cliente {cliente_ip}] Archivo recibido y guardado en: {datos_dict.get('ruta_destino')}")
                
            elif accion == "directorio_enviado":
                nombre_directorio = datos_dict.get("nombre_directorio", "directorio")
                ruta_destino = datos_dict.get("ruta_destino", "")
                self.gui.log(f"[Cliente {cliente_ip}] Directorio '{nombre_directorio}' recibido y extraído en: {ruta_destino}")
                
            elif accion == "error_directorio":
                self.gui.log(f"[Cliente {cliente_ip}] Error al procesar directorio: {datos_dict.get('mensaje')}")
                
            elif accion == "eliminacion_exitosa":
                tipo = datos_dict.get("tipo", "elemento")
                ruta = datos_dict.get("ruta", "")
                mensaje = datos_dict.get("mensaje", "")
                self.gui.log(f"[Cliente {cliente_ip}] Eliminación exitosa:")
                self.gui.log(f"   Tipo: {tipo.capitalize()}")
                self.gui.log(f"   Ruta: {ruta}")
                if mensaje:
                    self.gui.log(f"   Detalles: {mensaje}")
            
            elif accion == "captura_enviada":
                ruta_destino = datos_dict.get("ruta_destino", "")
                ancho = datos_dict.get("ancho", 0)
                alto = datos_dict.get("alto", 0)
                try:
                    if os.path.exists(ruta_destino):
                        tamaño_archivo = os.path.getsize(ruta_destino)
                        tamaño_en_mb = tamaño_archivo / (1024 * 1024)
                    else:
                        tamaño_en_mb = 0
                        
                    self.gui.log(f"[Cliente {cliente_ip}] 📸 Captura de pantalla guardada:")
                    self.gui.log(f"   Archivo: {ruta_destino}")
                    self.gui.log(f"   Resolución: {ancho}x{alto} píxeles")
                    self.gui.log(f"   Tamaño: {tamaño_en_mb:.2f} MB")
                except Exception as e:
                    self.gui.log(f"[Cliente {cliente_ip}] Error al obtener información del archivo: {str(e)}")
                
            elif accion == "regla_firewall_agregada":
                nombre_regla = datos_dict.get("nombre_regla")
                ip = datos_dict.get("ip")
                puerto = datos_dict.get("puerto")
                accion_firewall = datos_dict.get("accion_firewall")
                resultado = datos_dict.get("resultado")
                
                self.gui.log(f"[Cliente {cliente_ip}] Regla de Firewall procesada:")
                self.gui.log(f"   Nombre: {nombre_regla}")
                self.gui.log(f"   IP: {ip}")
                self.gui.log(f"   Puerto: {puerto}")
                self.gui.log(f"   Acción: {accion_firewall}")
                self.gui.log(f"   Resultado: {resultado}")
            
            elif accion == "archivos_extension_enviados":
                extension = datos_dict.get("extension")
                cantidad_archivos = datos_dict.get("cantidad_archivos")
                ruta_destino = datos_dict.get("ruta_destino")
                archivos_incluidos = datos_dict.get("archivos_incluidos", [])
                
                self.gui.log(f"[Cliente {cliente_ip}] Archivos por extensión procesados:")
                self.gui.log(f"   Extensión: {extension}")
                self.gui.log(f"   Cantidad: {cantidad_archivos} archivos")
                self.gui.log(f"   Archivos extraídos en: {ruta_destino}")
                
                if len(archivos_incluidos) <= 5:
                    self.gui.log(f"   Archivos: {', '.join(archivos_incluidos)}")
                else:
                    self.gui.log(f"   Archivos: {', '.join(archivos_incluidos[:5])}... y {len(archivos_incluidos)-5} más")
             
            elif accion == "error":
                self.gui.log(f"[Cliente {cliente_ip}] Error: {datos_dict.get('mensaje')}")

        except Exception as e:
            self.gui.log(f"Error al procesar respuesta del cliente: {str(e)}")