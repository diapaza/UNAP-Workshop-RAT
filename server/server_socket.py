import socket
import threading
import time
import json

class ServidorSocket:
    def __init__(self, host='0.0.0.0', puerto=5555):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = None
        self.clientes = []
        self.clientes_lock = threading.Lock()
        self.ejecutando = True
        self.controlador = None
        self.next_id = 1

    def establecer_controlador(self, controlador):
        self.controlador = controlador

    def iniciar(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.puerto))
            self.socket_servidor.listen(5)
            self.socket_servidor.settimeout(1.0)
            print(f"[+] Servidor iniciado en {self.host}:{self.puerto}")
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
        except Exception as e:
            print(f"[!] Error al iniciar el servidor: {e}")
            raise

    def aceptar_conexiones(self):
        while self.ejecutando:
            try:
                sock, direccion = self.socket_servidor.accept()
                print(f"[+] Nueva conexión desde {direccion[0]}:{direccion[1]}")
                sock.settimeout(1.0)
                with self.clientes_lock:
                    cliente = {
                        "id": self.next_id,
                        "socket": sock,
                        "direccion": direccion,
                        "ultimo_contacto": time.time()
                    }
                    self.next_id += 1
                    self.clientes.append(cliente)
                threading.Thread(target=self.manejar_cliente, args=(cliente,), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[!] Error al aceptar conexión: {e}")

    def manejar_cliente(self, cliente):
        sock = cliente["socket"]
        try:
            while self.ejecutando:
                datos = self.recibir_mensaje(sock)
                if datos is None:
                    print(f"[!] Cliente {cliente['id']}, {cliente['direccion'][0]} desconectado")
                    break
                if datos == "":
                    continue
                if self.controlador:
                    try:
                        self.controlador.procesar_respuesta_cliente(datos, cliente)
                    except Exception as e:
                        print(f"[!] Error en controlador al procesar cliente {cliente['id']}: {e}")
                cliente["ultimo_contacto"] = time.time()
        except ConnectionResetError:
            print(f"[!] Cliente desconectó abruptamente {cliente['direccion']}")
        except Exception as e:
            print(f"[!] Error con cliente {cliente['direccion']}: {e}")
        finally:
            self.remover_cliente(cliente)

    def remover_cliente(self, cliente):
        with self.clientes_lock:
            if cliente in self.clientes:
                try:
                    self.clientes.remove(cliente)
                except ValueError:
                    pass
                try:
                    cliente["socket"].close()
                except:
                    pass
                print(f"[-] Cliente {cliente['id']} desconectado ({cliente['direccion']})")
                if cliente["id"] == self.next_id - 1:
                    self.next_id -= 1

    def enviar_mensaje(self, socket_cliente, mensaje):
        try:
            if isinstance(mensaje, dict):
                mensaje = json.dumps(mensaje)
            data = mensaje.encode()
            socket_cliente.sendall(len(data).to_bytes(4, "big"))
            socket_cliente.sendall(data)
            return True
        except Exception as e:
            return False

    def recibir_mensaje(self, sock):
        try:
            header = sock.recv(4)
            if header == b'':
                return None
            if not header:
                return ""
            longitud = int.from_bytes(header, "big")
            data = b""
            while len(data) < longitud:
                try:
                    chunk = sock.recv(min(4096, longitud - len(data)))
                except socket.timeout:
                    continue
                if chunk == b'':
                    return None
                if not chunk:
                    return ""
                data += chunk
            return data.decode()
        except socket.timeout:
            return ""
        except Exception:
            return None

    def enviar_comando_todos(self, comando):
        desconectados = []
        with self.clientes_lock:
            for cliente in list(self.clientes):
                if not self.enviar_mensaje(cliente["socket"], comando):
                    desconectados.append(cliente)
        for c in desconectados:
            self.remover_cliente(c)

    def enviar_a_cliente(self, id_cliente, comando):
        with self.clientes_lock:
            for cliente in self.clientes:
                if cliente["id"] == id_cliente:
                    return self.enviar_mensaje(cliente["socket"], comando)
        print(f"[!] Cliente con ID {id_cliente} no encontrado")
        return False

    def cerrar(self):
        self.ejecutando = False
        try:
            self.socket_servidor.close()
        except:
            pass
        with self.clientes_lock:
            for cliente in list(self.clientes):
                try:
                    cliente["socket"].close()
                except:
                    pass
            self.clientes.clear()
        print("[+] Servidor cerrado")
