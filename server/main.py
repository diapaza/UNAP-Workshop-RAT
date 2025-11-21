import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import os
import json
from server_controller import ControladorServidor
from server_socket import ServidorSocket
from custom_controller import CustomControlador

class ServidorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Servidor")
        self.root.geometry("1500x800")
        self.root.minsize(1400, 800)
        
        self.servidor_socket = None
        self.controlador = None
        self.hilo_servidor = None
        self.ejecutando = False
        
        self.host_var = tk.StringVar(value="0.0.0.0")
        self.puerto_var = tk.IntVar(value=5555)
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        main_frame.columnconfigure(0, weight=1, minsize=250)
        main_frame.columnconfigure(1, weight=1, minsize=750)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        self._crear_panel_izquierdo(main_frame)
        self._crear_panel_central(main_frame)
        self._crear_panel_derecho(main_frame)
    
    def _crear_panel_izquierdo(self, parent):
        panel_izquierdo = ttk.Frame(parent)
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Configuración del servidor
        frame_config = ttk.LabelFrame(panel_izquierdo, text="Configuración del Servidor")
        frame_config.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame_config, text="Host:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Entry(frame_config, textvariable=self.host_var).grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        
        ttk.Label(frame_config, text="Puerto:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Entry(frame_config, textvariable=self.puerto_var).grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        
        btn_frame = ttk.Frame(frame_config)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        self.btn_iniciar = ttk.Button(btn_frame, text="Iniciar Servidor", command=self.iniciar_servidor)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)
        
        self.btn_detener = ttk.Button(btn_frame, text="Detener Servidor", command=self.detener_servidor, state=tk.DISABLED)
        self.btn_detener.pack(side=tk.LEFT, padx=5)
        
        frame_config.columnconfigure(1, weight=1)
        
        # Lista de clientes
        frame_clientes = ttk.LabelFrame(panel_izquierdo, text="Clientes Conectados")
        frame_clientes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree_clientes = ttk.Treeview(frame_clientes, columns=("IP", "Puerto"), show="headings")
        self.tree_clientes.heading("IP", text="Dirección IP")
        self.tree_clientes.heading("Puerto", text="Puerto")
        self.tree_clientes.column("IP", width=120)
        self.tree_clientes.column("Puerto", width=80)
        self.tree_clientes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _crear_panel_central(self, parent):
        panel_central = ttk.Frame(parent)
        panel_central.grid(row=0, column=1, sticky="nsew", padx=5)
        
        frame_acciones = ttk.LabelFrame(panel_central, text="Acciones Rápidas")
        frame_acciones.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._crear_seccion_codigo(frame_acciones)
        self._crear_seccion_archivos(frame_acciones)
        self._crear_seccion_eliminacion(frame_acciones)
        self._crear_seccion_captura(frame_acciones)
        self._crear_seccion_firewall(frame_acciones)
    
    def _crear_seccion_codigo(self, parent):
        frame_codigo = ttk.Frame(parent)
        frame_codigo.pack(fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Label(frame_codigo, text="Ejecutar código Python:").pack(anchor=tk.W)
        self.text_codigo = scrolledtext.ScrolledText(frame_codigo, height=5)
        self.text_codigo.pack(fill=tk.BOTH, expand=True, pady=2)
        
        ttk.Button(frame_codigo, text="Ejecutar", command=self.ejecutar_codigo).pack(anchor=tk.E, pady=2)
    
    def _crear_seccion_archivos(self, parent):
        frame_archivos = ttk.LabelFrame(parent, text="Transferencia de Archivos")
        frame_archivos.pack(fill=tk.X, padx=5, pady=5)
        
        # Enviar archivo
        self._crear_enviar_archivo(frame_archivos)
        
        # Solicitar archivo
        self._crear_solicitar_archivo(frame_archivos)
        
        # Solicitar directorio completo
        self._crear_solicitar_directorio(frame_archivos)
        
        # Listar directorios
        self._crear_listar_directorio(frame_archivos)
        
        self._crear_solicitar_archivos_extension(frame_archivos)
    
    def _crear_enviar_archivo(self, parent):
        frame_enviar = ttk.Frame(parent)
        frame_enviar.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_enviar, text="Enviar archivo:").grid(row=0, column=0, sticky=tk.W)
        self.entry_archivo = ttk.Entry(frame_enviar)
        self.entry_archivo.grid(row=0, column=1, padx=2, sticky=tk.EW)
        ttk.Button(frame_enviar, text="Buscar", command=self.buscar_archivo).grid(row=0, column=2, padx=2)
        
        ttk.Label(frame_enviar, text="Destino:").grid(row=1, column=0, sticky=tk.W)
        self.entry_destino = ttk.Entry(frame_enviar)
        self.entry_destino.grid(row=1, column=1, padx=2, sticky=tk.EW)
        self.entry_destino.insert(0, "/descargas/")
        
        ttk.Button(frame_enviar, text="Enviar a Clientes", command=self.enviar_archivo).grid(row=1, column=2, padx=2)

        frame_enviar.columnconfigure(1, weight=1)
    
    def _crear_solicitar_archivo(self, parent):
        frame_solicitar = ttk.Frame(parent)
        frame_solicitar.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_solicitar, text="Solicitar archivo (ruta en cliente):").grid(row=0, column=0, sticky=tk.W)
        self.entry_solicitar = ttk.Entry(frame_solicitar)
        self.entry_solicitar.grid(row=0, column=1, padx=2, sticky=tk.EW)
        
        ttk.Label(frame_solicitar, text="Guardar en:").grid(row=1, column=0, sticky=tk.W)
        self.entry_guardar = ttk.Entry(frame_solicitar)
        self.entry_guardar.grid(row=1, column=1, padx=2, sticky=tk.EW)
        self.entry_guardar.insert(0, "./archivos_recibidos/")
        
        ttk.Button(frame_solicitar, text="Solicitar Archivo", command=self.solicitar_archivo).grid(row=2, column=0, columnspan=2, pady=5)
        frame_solicitar.columnconfigure(1, weight=1)
    
    def _crear_solicitar_directorio(self, parent):
        frame_directorio = ttk.Frame(parent)
        frame_directorio.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame_directorio, text="Solicitar directorio completo (ruta en cliente):").grid(row=0, column=0, sticky=tk.W)
        self.entry_directorio_origen = ttk.Entry(frame_directorio)
        self.entry_directorio_origen.grid(row=0, column=1, padx=2, sticky=tk.EW)
        
        ttk.Label(frame_directorio, text="Guardar en servidor:").grid(row=1, column=0, sticky=tk.W)
        self.entry_directorio_destino = ttk.Entry(frame_directorio)
        self.entry_directorio_destino.grid(row=1, column=1, padx=2, sticky=tk.EW)
        self.entry_directorio_destino.insert(0, "./directorios_recibidos/")
        
        ttk.Button(frame_directorio, text="Solicitar Directorio", command=self.solicitar_directorio_completo).grid(row=2, column=0, columnspan=2, pady=5)
        frame_directorio.columnconfigure(1, weight=1)
    
    def _crear_listar_directorio(self, parent):
        frame_listar = ttk.Frame(parent)
        frame_listar.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame_listar, text="Listar directorio (ruta en cliente):").grid(row=0, column=0, sticky=tk.W)
        
        self.entry_directorio = ttk.Entry(frame_listar)
        self.entry_directorio.grid(row=0, column=1, padx=2, sticky=tk.EW)
        
        self.incluir_archivos_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_listar, text="Incluir archivos", variable=self.incluir_archivos_var).grid(row=0, column=2, padx=5, sticky=tk.W)
        
        ttk.Button(frame_listar, text="Listar Directorio", command=self.listar_directorio).grid(row=1, column=0, columnspan=3, pady=5)

        frame_listar.columnconfigure(1, weight=1)
    
    def _crear_seccion_eliminacion(self, parent):
        frame_eliminar = ttk.LabelFrame(parent, text="Eliminación de Archivos/Directorios")
        frame_eliminar.pack(fill=tk.X, padx=5, pady=5)
        
        frame_eliminar_auto = ttk.Frame(frame_eliminar)
        frame_eliminar_auto.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame_eliminar_auto, text="Eliminación automática (ruta en cliente):").grid(row=0, column=0, sticky=tk.W)
        self.entry_eliminar_auto = ttk.Entry(frame_eliminar_auto)
        self.entry_eliminar_auto.grid(row=0, column=1, padx=2, sticky=tk.EW)
        
        ttk.Button(frame_eliminar_auto, text="Eliminar (Auto)", command=self.eliminar_automatico).grid(row=1, column=0, columnspan=2, pady=5)
        frame_eliminar_auto.columnconfigure(1, weight=1)
    
    def _crear_seccion_captura(self, parent):
        frame_captura = ttk.LabelFrame(parent, text="Captura de Pantalla")
        frame_captura.pack(fill=tk.X, padx=5, pady=5)
        
        frame_captura_pantalla = ttk.Frame(frame_captura)
        frame_captura_pantalla.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame_captura_pantalla, text="Directorio de destino:").grid(row=0, column=0, sticky=tk.W)
        self.entry_captura_destino = ttk.Entry(frame_captura_pantalla)
        self.entry_captura_destino.grid(row=0, column=1, columnspan=2, padx=2, sticky=tk.EW)
        self.entry_captura_destino.insert(0, "./capturas/")
        
        ttk.Label(frame_captura_pantalla, text="Nombre de archivo (opcional):").grid(row=1, column=0, sticky=tk.W)
        self.entry_captura_nombre = ttk.Entry(frame_captura_pantalla)
        self.entry_captura_nombre.grid(row=1, column=1, padx=2, sticky=tk.EW)
        self.entry_captura_nombre.insert(0, "captura.png")
        
        self.usar_timestamp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_captura_pantalla, text="Usar timestamp automático", 
                        variable=self.usar_timestamp_var).grid(row=1, column=2, padx=5, sticky=tk.W)
        
        ttk.Button(frame_captura_pantalla, text="Tomar Captura", 
                command=self.tomar_captura_pantalla).grid(row=2, column=0, columnspan=3, pady=5)

        frame_captura_pantalla.columnconfigure(1, weight=1)
        
    def _crear_seccion_firewall(self, parent):
        frame_firewall = ttk.LabelFrame(parent, text="Reglas de Firewall")
        frame_firewall.pack(fill=tk.X, padx=5, pady=5)
        
        frame_firewall_form = ttk.Frame(frame_firewall)
        frame_firewall_form.pack(fill=tk.X, pady=2)
        
        # Primera fila: Nombre y Puerto
        ttk.Label(frame_firewall_form, text="Nombre de regla:").grid(row=0, column=0, sticky=tk.W)
        self.entry_firewall_nombre = ttk.Entry(frame_firewall_form)
        self.entry_firewall_nombre.grid(row=0, column=1, padx=2, sticky=tk.EW)
        
        ttk.Label(frame_firewall_form, text="Puerto:").grid(row=0, column=2, sticky=tk.W)
        self.entry_firewall_puerto = ttk.Entry(frame_firewall_form)
        self.entry_firewall_puerto.grid(row=0, column=3, padx=2, sticky=tk.EW)
        
        # Segunda fila: Acción y botón
        ttk.Label(frame_firewall_form, text="Acción:").grid(row=1, column=0, sticky=tk.W)
        self.combo_firewall_accion = ttk.Combobox(frame_firewall_form, values=["block", "allow"], state="readonly")
        self.combo_firewall_accion.grid(row=1, column=1, padx=2, sticky=tk.EW)
        self.combo_firewall_accion.set("block")
        
        ttk.Button(frame_firewall_form, text="Agregar Regla de Firewall", 
                command=self.agregar_regla_firewall).grid(row=1, column=2, columnspan=2, padx=2, sticky=tk.E)
        
        # Configurar el crecimiento de las columnas de entrada
        frame_firewall_form.columnconfigure(1, weight=1)
        frame_firewall_form.columnconfigure(3, weight=1)
    
    def _crear_solicitar_archivos_extension(self, parent):
        frame_extension = ttk.Frame(parent)
        frame_extension.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame_extension, text="Directorio origen (ruta en cliente):").grid(row=0, column=0, sticky=tk.W)
        self.entry_extension_directorio = ttk.Entry(frame_extension)
        self.entry_extension_directorio.grid(row=0, column=1, padx=2, sticky=tk.EW)
        
        ttk.Label(frame_extension, text="Extensión (ej: .txt, .pdf):").grid(row=0, column=2, sticky=tk.W)
        self.entry_extension = ttk.Entry(frame_extension)
        self.entry_extension.grid(row=0, column=3, padx=2, sticky=tk.EW)
        
        ttk.Label(frame_extension, text="Guardar en servidor:").grid(row=1, column=0, sticky=tk.W)
        self.entry_extension_destino = ttk.Entry(frame_extension)
        self.entry_extension_destino.grid(row=1, column=1, padx=2, sticky=tk.EW)
        self.entry_extension_destino.insert(0, "./archivos_por_extension/")
        
        ttk.Button(frame_extension, text="Solicitar Archivos por Extensión", 
                command=self.solicitar_archivos_por_extension).grid(row=1, column=2, pady=5)
        frame_extension.columnconfigure(1, weight=1)
    
    def _crear_panel_derecho(self, parent):
        panel_derecho = ttk.Frame(parent)
        panel_derecho.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        frame_logs = ttk.LabelFrame(panel_derecho, text="Logs del Servidor")
        frame_logs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_logs = scrolledtext.ScrolledText(frame_logs, wrap=tk.WORD, state=tk.DISABLED)
        self.text_logs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(frame_logs, text="Limpiar Logs", command=self.limpiar_logs).pack(pady=5)
    
    def log(self, mensaje):
        self.text_logs.config(state=tk.NORMAL)
        self.text_logs.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {mensaje}\n")
        self.text_logs.see(tk.END)
        self.text_logs.config(state=tk.DISABLED)
    
    def limpiar_logs(self):
        self.text_logs.config(state=tk.NORMAL)
        self.text_logs.delete("1.0", tk.END)
        self.text_logs.config(state=tk.DISABLED)
        self.log("Logs limpiados")
    
    def actualizar_clientes(self):
        while self.ejecutando:
            if self.servidor_socket and hasattr(self.servidor_socket, "clientes"):
                for item in self.tree_clientes.get_children():
                    self.tree_clientes.delete(item)
                
                for cliente in self.servidor_socket.clientes:
                    self.tree_clientes.insert("", tk.END, values=(cliente["direccion"][0], cliente["direccion"][1]))
            
            time.sleep(2)
    
    def iniciar_servidor(self):
        if self.ejecutando:
            return
            
        try:
            host = self.host_var.get()
            puerto = self.puerto_var.get()
            
            self.servidor_socket = ServidorSocket(host, puerto)
            self.controlador = CustomControlador(self.servidor_socket, self)
            
            self.hilo_servidor = threading.Thread(target=self.ejecutar_servidor, daemon=True)
            self.hilo_servidor.start()
            
            self.ejecutando = True
            self.hilo_clientes = threading.Thread(target=self.actualizar_clientes, daemon=True)
            self.hilo_clientes.start()
            
            self.btn_iniciar.config(state=tk.DISABLED)
            self.btn_detener.config(state=tk.NORMAL)
            
            self.log(f"Servidor iniciado en {host}:{puerto}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar el servidor: {str(e)}")
            self.log(f"Error al iniciar el servidor: {str(e)}")
    
    def ejecutar_servidor(self):
        try:
            self.servidor_socket.iniciar()
            while self.ejecutando:
                time.sleep(1)
        except Exception as e:
            self.log(f"Error en el servidor: {str(e)}")
            messagebox.showerror("Error", f"Error en el servidor: {str(e)}")
    
    def detener_servidor(self):
        if not self.ejecutando:
            return
            
        self.ejecutando = False
        
        if self.servidor_socket:
            self.servidor_socket.cerrar()
        
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_detener.config(state=tk.DISABLED)
        
        self.log("Servidor detenido")
    
    def _validar_servidor_activo(self):
        if not self.ejecutando or not self.servidor_socket:
            messagebox.showwarning("Advertencia", "El servidor no está iniciado")
            return False
            
        num_clientes = len(self.servidor_socket.clientes)
        if num_clientes == 0:
            messagebox.showinfo("Info", "No hay clientes conectados")
            return False
        
        return True
    
    def ejecutar_codigo(self):
        if not self._validar_servidor_activo():
            return
            
        codigo = self.text_codigo.get("1.0", tk.END).strip()
        if not codigo:
            messagebox.showwarning("Advertencia", "Ingrese código para ejecutar")
            return
        
        self.controlador.enviar_comando_ejecutar(codigo)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Código enviado a {num_clientes} cliente(s)")
    
    def buscar_archivo(self):
        archivo = filedialog.askopenfilename(title="Seleccionar archivo")
        if archivo:
            self.entry_archivo.delete(0, tk.END)
            self.entry_archivo.insert(0, archivo)
    
    def enviar_archivo(self):
        if not self._validar_servidor_activo():
            return
            
        ruta_origen = self.entry_archivo.get().strip()
        ruta_destino = self.entry_destino.get().strip()
        
        if not ruta_origen or not ruta_destino:
            messagebox.showwarning("Advertencia", "Ingrese rutas de origen y destino")
            return
            
        if not os.path.isfile(ruta_origen):
            messagebox.showerror("Error", f"El archivo no existe: {ruta_origen}")
            return
            
        try:
            num_clientes = len(self.servidor_socket.clientes)
            self.controlador.enviar_archivo_a_clientes(ruta_origen, ruta_destino)
            self.log(f"Archivo {os.path.basename(ruta_origen)} enviado a {num_clientes} cliente(s)")
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar archivo: {str(e)}")
            self.log(f"Error al enviar archivo: {str(e)}")
    
    def solicitar_archivo(self):
        if not self._validar_servidor_activo():
            return
            
        ruta_origen = self.entry_solicitar.get().strip()
        ruta_destino = self.entry_guardar.get().strip()
        
        if not ruta_origen or not ruta_destino:
            messagebox.showwarning("Advertencia", "Ingrese rutas de origen y destino")
            return
        
        self.controlador.enviar_comando_solicitar_archivo(ruta_origen, ruta_destino)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Solicitud de archivo enviada a {num_clientes} cliente(s)")
    
    def listar_directorio(self):
        if not self._validar_servidor_activo():
            return
            
        ruta = self.entry_directorio.get().strip()
        if not ruta:
            messagebox.showwarning("Advertencia", "Ingrese una ruta para listar")
            return
        
        self.controlador.enviar_comando_listar_directorio(ruta, self.incluir_archivos_var.get())
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Solicitud de listado de directorio enviada a {num_clientes} cliente(s)")

    def solicitar_directorio_completo(self):
        if not self._validar_servidor_activo():
            return
            
        ruta_origen = self.entry_directorio_origen.get().strip()
        ruta_destino = self.entry_directorio_destino.get().strip()
        
        if not ruta_origen or not ruta_destino:
            messagebox.showwarning("Advertencia", "Ingrese rutas de origen y destino")
            return
        
        self.controlador.enviar_comando_solicitar_directorio(ruta_origen, ruta_destino)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Solicitud de directorio completo enviada a {num_clientes} cliente(s)")
        self.log(f"Origen: {ruta_origen} -> Destino: {ruta_destino}")
        
    def solicitar_archivos_por_extension(self):
        if not self._validar_servidor_activo():
            return
            
        ruta_directorio = self.entry_extension_directorio.get().strip()
        extension = self.entry_extension.get().strip()
        ruta_destino = self.entry_extension_destino.get().strip()
        
        if not ruta_directorio or not extension or not ruta_destino:
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        self.controlador.enviar_comando_solicitar_archivos_por_extension(ruta_directorio, extension, ruta_destino)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Solicitud de archivos por extensión enviada a {num_clientes} cliente(s)")
        self.log(f"Directorio: {ruta_directorio} | Extensión: {extension}")
    
    def eliminar_automatico(self):
        if not self._validar_servidor_activo():
            return
            
        ruta = self.entry_eliminar_auto.get().strip()
        if not ruta:
            messagebox.showwarning("Advertencia", "Ingrese la ruta del archivo o directorio a eliminar")
            return
            
        respuesta = messagebox.askyesno(
            "Confirmar eliminación automática", 
            f"¿Está seguro de que desea eliminar?\n\nRuta: {ruta}\n\nEl sistema detectará automáticamente si es un archivo o directorio.\n\n⚠️ Si es un directorio, se eliminará TODO su contenido.\n\n¿Continuar?"
        )
        
        if not respuesta:
            return
        
        self.controlador.enviar_comando_eliminar(ruta)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Solicitud de eliminación automática enviada a {num_clientes} cliente(s)")
        self.log(f"Ruta a eliminar: {ruta}")
        
    def tomar_captura_pantalla(self):
        if not self._validar_servidor_activo():
            return
            
        ruta_destino = self.entry_captura_destino.get().strip()
        nombre_archivo = self.entry_captura_nombre.get().strip()
        usar_timestamp = self.usar_timestamp_var.get()
        
        if not ruta_destino:
            messagebox.showwarning("Advertencia", "Ingrese el directorio de destino")
            return
            
        # Generar nombre de archivo
        if usar_timestamp or not nombre_archivo:
            nombre_archivo = f"captura_{int(time.time())}.png"
        elif not nombre_archivo.endswith('.png'):
            nombre_archivo += '.png'
        
        self.controlador.enviar_comando_captura_pantalla(ruta_destino, nombre_archivo)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Solicitud de captura de pantalla enviada a {num_clientes} cliente(s)")
        self.log(f"Archivo: {nombre_archivo}")

    def agregar_regla_firewall(self):
        if not self._validar_servidor_activo():
            return
            
        nombre_regla = self.entry_firewall_nombre.get().strip()
        puerto = self.entry_firewall_puerto.get().strip()
        accion = self.combo_firewall_accion.get()
        
        if not nombre_regla or not puerto:
            messagebox.showwarning("Advertencia", "Ingrese nombre de regla y puerto")
            return
        
        try:
            puerto_num = int(puerto)
            if not (1 <= puerto_num <= 65535):
                raise ValueError("Puerto fuera de rango")
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número entre 1 y 65535")
            return
        
        self.controlador.enviar_comando_agregar_firewall(nombre_regla, "any", puerto, accion)
        num_clientes = len(self.servidor_socket.clientes)
        self.log(f"Regla de firewall enviada a {num_clientes} cliente(s)")
        self.log(f"Regla: {nombre_regla} | Puerto: {puerto} | Acción: {accion}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ServidorGUI(root)
    root.mainloop()