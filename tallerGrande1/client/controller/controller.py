import os
import socket
import json
import time
from pathlib import Path

from model.peer_table import PeerTable
from model.number_list import NumberList
from view.logger import Logger

INDEX_IP = os.environ.get("INDEX_IP", "192.168.4.4")
INDEX_PORT = int(os.environ.get("INDEX_PORT", "5000"))
CLIENT_NAME = os.environ.get("CLIENT_NAME", "clienteX")
CLIENT_PORT = int(os.environ.get("CLIENT_PORT", "6000"))
DATA_DIR = os.environ.get("CLIENT_DATA_DIR", "/opt/cliente/data")
JOIN_RETRIES = int(os.environ.get("JOIN_RETRIES", "3"))
JOIN_TIMEOUT = float(os.environ.get("JOIN_TIMEOUT", "5.0"))
SERVE_AFTER_JOIN = os.environ.get("SERVE_AFTER_JOIN", "false").lower() in ("1", "true", "yes")

class ClientController:
    def __init__(self):
        # rutas de persistencia
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        peers_path = Path(DATA_DIR) / "peers.json"
        numbers_path = Path(DATA_DIR) / "numbers.json"

        self.peers = PeerTable(storage_path=peers_path)
        self.numbers = NumberList(storage_path=numbers_path)

    def join_index(self):
        """Conecta al Index, manda payload 'join' y procesa la respuesta."""
        payload = {"action": "join", "name": CLIENT_NAME, "port": CLIENT_PORT}
        attempts = 0
        while attempts < JOIN_RETRIES:
            attempts += 1
            try:
                Logger.info(f"Conectando al Index {INDEX_IP}:{INDEX_PORT} (intento {attempts}/{JOIN_RETRIES})")
                s = socket.create_connection((INDEX_IP, INDEX_PORT), timeout=JOIN_TIMEOUT)
                
                s.sendall((json.dumps(payload) + "\n").encode())
                f = s.makefile('r')
                line = f.readline()
                if not line:
                    raise RuntimeError("No se recibió respuesta del Index")
                try:
                    response = json.loads(line.strip())
                except Exception as e:
                    raise RuntimeError(f"Respuesta inválida JSON: {e}")

                
                if response.get("status") != "ok":
                    raise RuntimeError(f"Index respondió error: {response}")

                self.peers.update(response.get("peers", []))
                self.numbers.update(response.get("numbers", []))

                Logger.info(f"Registro OK. Peers recibidos: {len(self.peers.get_all())}; Números recibidos: {len(self.numbers.numbers)}")
                s.close()
                return True
            except (socket.timeout, ConnectionRefusedError) as e:
                Logger.error(f"No se pudo conectar al Index: {e}")
                time.sleep(1 + attempts)  
            except Exception as e:
                Logger.error(f"Error en join_index: {e}")
                return False
        Logger.error("Agotados intentos de conexión al Index.")
        return False

    def show_state(self):
        Logger.info(f"Nombre: {CLIENT_NAME}  Puerto: {CLIENT_PORT}")
        Logger.info(f"{self.peers.get_all()}")
        Logger.info(f"Números: {self.numbers.numbers}")
        Logger.info(f"Conteos: {self.numbers.counts()}")
        Logger.info(f"Duplicados: {self.numbers.duplicates()}")

    def start_peer_server(self, host="0.0.0.0", port=CLIENT_PORT):

        Logger.info(f"Iniciando servidor de peers en {host}:{port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen()
            try:
                while True:
                    conn, addr = s.accept()
                    Logger.info(f"Conexión entrante de peer {addr}")
                    with conn:
                        try:
                            f = conn.makefile('r')
                            line = f.readline()
                            if not line:
                                continue
                            try:
                                req = json.loads(line.strip())
                            except Exception:
                                conn.sendall(b'{"status":"error","reason":"invalid_json"}\n')
                                continue

                            action = req.get("action")
                            if action == "ping":
                                conn.sendall((json.dumps({"status":"ok","name": CLIENT_NAME}) + "\n").encode())
                            elif action == "get_state":
                                resp = {"status":"ok", "name": CLIENT_NAME, "numbers": self.numbers.numbers, "peers": self.peers.get_all()}
                                conn.sendall((json.dumps(resp) + "\n").encode())
                            else:
                                conn.sendall(b'{"status":"error","reason":"unknown_action"}\n')
                        except Exception as e:
                            Logger.error(f"Error atendiendo peer: {e}")
            except KeyboardInterrupt:
                Logger.info("Servidor de peers detenido por teclado.")
