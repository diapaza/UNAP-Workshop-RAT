# 🛡️ Herramienta Educativa para Simulación de Ataques de Ransomware tipo RAT (Remote Access Tool) en Windows

> **⚠️ Aviso Importante**
> Este proyecto se proporciona **exclusivamente con fines educativos**, para prácticas de laboratorio, análisis de seguridad y formación en ciberseguridad.
> **No debe utilizarse en sistemas sin autorización expresa.**
> El uso indebido de este software puede constituir un delito.

## 📦 Instalación

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/diapaza/UNAP-Workshop-RAT.git
   ```

2. **Ingresar al directorio del proyecto**

   ```bash
   cd UNAP-Workshop-RAT
   ```

3. **Instalar las dependencias**

   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Uso del Builder (cliente)

1. Acceder a la carpeta del cliente:

   ```bash
   cd client
   ```

2. Ejecutar el builder:

   ```bash
   python builder.py
   ```

   o

   ```bash
   py builder.py
   ```

3. En la interfaz del builder:

   * Selecciona tu **IP LAN**. Para obtenerla:

     * Abrir `cmd`
     * Ejecutar:
       ```bash
       ipconfig
       ```
     * Localizar **Adaptador de LAN inalámbrica Wi‑Fi** → *Dirección IPv4 (ej: 192.168.1.x)*
   * Definir un **puerto** (por defecto `5555`).
   * Elegir un ejecutable base (`.exe`).
   * Seleccionar un icono (`.ico`).
   * Presionar **Generar EXE**.
   * Esperar a que finalice el proceso.

---

## 🧪 Configuración de Entorno Virtual (Oracle VirtualBox)

Para realizar prácticas de forma segura, se recomienda usar una máquina virtual:

1. **Instalar Oracle VirtualBox**
   (Disponible en el sitio oficial de VirtualBox)

2. **Descargar una ISO de Windows**
   Puedes usar imágenes de evaluación desde Microsoft (Windows 10 preferible).

3. **Crear una máquina virtual Windows**

   * Asignar los recursos recomendados.
   * Desactivar **Hyper‑V** en el host si genera conflictos (usar este comando en PowerShell `bcdedit /set hypervisorlaunchtype off`).


4. **Configurar el adaptador de red**

   * Ajustar a **Puente (Bridged Adapter)** para permitir comunicación LAN entre servidor y cliente simulado.

---

## 🖥️ Ejecución del Servidor

1. Ingresar a la carpeta del servidor:

   ```bash
   cd server
   ```

2. Iniciar el servidor:

   ```bash
   python gui.py
   ```

   o

   ```bash
   py gui.py
   ```

3. En la interfaz gráfica:

   * Presionar el botón **Iniciar servidor**.

---

## 🧩 Ejecución del Agente en la Máquina Virtual (Víctima Simulada)

1. Transferir el archivo generado por el builder:
   `client/dist/<archivo_generado>.exe`

2. Ejecutarlo dentro de la máquina virtual.

---

## 🕹️ Control desde el Servidor

Una vez establecida la conexión, desde el servidor podrás realizar las acciones habilitadas dentro del entorno controlado de laboratorio.

---

## 📘 Notas Finales

* Este proyecto está orientado a talleres y cursos de seguridad informática.
* Se recomienda ejecutar **todo exclusivamente en entornos aislados**.
* No se debe usar en equipos reales o de terceros, ya que hacerlo infringe normas educativas y legales.
