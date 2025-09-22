# controller/controller.py
import socket
import json
import os
import time
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
        # {conn: {"name":..., "numbers":..., "turn":...}}
        self.connections = {}

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        Logger.info(f"Index escuchando en {self.host}:{self.port}")
        self._running = True

        try:
            while self._running:
                conn, addr = self.sock.accept()
                self._handle_client(conn, addr)

                # Cuando se alcanzan todos los clientes, enviamos estado final
                if len(self.connections) >= TOTAL_CLIENTS:
                    Logger.info(f"Se alcanzó TOTAL_CLIENTS={TOTAL_CLIENTS}, enviando tabla final...")
                    self._send_final_state()
                    break
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

            # Turno = orden de registro
            turn = len(peers)

            # Guardamos conexión, números y turno
            self.connections[conn] = {"name": name, "numbers": numbers, "turn": turn}

            # Mientras no se complete el grupo, enviamos estado de espera
            if len(peers) < TOTAL_CLIENTS:
                conn.sendall(b'{"status":"waiting"}\n')

        except Exception as e:
            Logger.error(f"Error manejando cliente {addr}: {e}")

    def _send_final_state(self):
        """Cuando todos los clientes están conectados, enviamos estado completo a cada uno"""
        state_peers = self.registry.get_all()

        for conn, info in list(self.connections.items()):
            try:
                response = {
                    "status": "ok",
                    "peers": state_peers,
                    "numbers": info["numbers"],
                    "turn": info["turn"]  # 👈 agregamos turno al mensaje
                }
                conn.sendall((json.dumps(response) + "\n").encode())
                conn.sendall(b'{"status":"done"}\n')
                conn.close()
            except Exception as e:
                Logger.error(f"No pude enviar estado final a {info['name']}: {e}")
            finally:
                del self.connections[conn]

        self._running = False
        Logger.info("Todos los clientes recibieron la tabla, números y turnos. Index terminado.")


    def _send_final_state(self):
        """Cuando todos los clientes están conectados, esperamos un delay y enviamos estado completo a cada uno"""
        start_delay = int(os.environ.get("START_DELAY", "5"))  # 👈 delay configurable
        Logger.info(f"Todos los clientes registrados. Esperando {start_delay}s antes de enviar estado final...")
        time.sleep(start_delay)

        state_peers = self.registry.get_all()

        for conn, info in list(self.connections.items()):
            try:
                response = {
                    "status": "ok",
                    "peers": state_peers,
                    "numbers": info["numbers"],
                    "turn": info["turn"]  # 👈 ya lo tenías
                }
                conn.sendall((json.dumps(response) + "\n").encode())
                conn.sendall(b'{"status":"done"}\n')
                conn.close()
            except Exception as e:
                Logger.error(f"No pude enviar estado final a {info['name']}: {e}")
            finally:
                del self.connections[conn]

        self._running = False
        Logger.info("Todos los clientes recibieron la tabla, números y turnos. Index terminado.")
