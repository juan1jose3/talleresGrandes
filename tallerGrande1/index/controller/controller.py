# controlador.py
import socket
import json
import os
from model.client_registry import ClientRegistry
from model.number_pool import NumberPool
from view.logger import Logger

HOST = '0.0.0.0'
PORT = int(os.environ.get('INDEX_PORT', '5000'))
TOTAL_CLIENTS = int(os.environ.get('TOTAL_CLIENTS', '5'))

class IndexController:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.registry = ClientRegistry()
        self.pool = NumberPool(total_clients=TOTAL_CLIENTS)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._running = False

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        Logger.info(f"Index escuchando en {self.host}:{self.port}")
        self._running = True

        try:
            while self._running:
                conn, addr = self.sock.accept()
                self._handle_client(conn, addr)  # 👈 directo, sin threads
        except KeyboardInterrupt:
            Logger.info("Interrumpido por teclado, cerrando.")
        finally:
            self.sock.close()

    def _handle_client(self, conn, addr):
        Logger.info(f"Conexión entrante desde {addr}")
        try:
            f = conn.makefile('rwb')
            line = f.readline()
            if not line:
                return
            try:
                data = json.loads(line.decode().strip())
            except Exception as e:
                Logger.error(f"JSON inválido de {addr}: {e}")
                conn.sendall(b'{"status":"error","reason":"invalid_json"}\n')
                return

            if data.get('action') != 'join':
                conn.sendall(b'{"status":"error","reason":"unsupported_action"}\n')
                return

            name = data.get('name')
            client_port = data.get('port')
            client_ip = addr[0]

            peers = self.registry.add_client(name, client_ip, client_port)
            Logger.info(f"Cliente registrado: {name} @ {client_ip}:{client_port}")

            numbers = self.pool.assign_list(length=11)
            Logger.info(f"Números asignados a {name}: {numbers}")

            response = {
                'status': 'ok',
                'peers': peers,
                'numbers': numbers,
            }
            conn.sendall((json.dumps(response) + '\n').encode())
        except Exception as e:
            Logger.error(f"Error manejando cliente {addr}: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

