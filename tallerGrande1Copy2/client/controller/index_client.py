import socket
import json
import time
from view.logger import Logger

class IndexClient:
    def __init__(self, index_ip, index_port, client_name, client_port, retries=3, timeout=None):
        self.index_ip = index_ip
        self.index_port = index_port
        self.client_name = client_name
        self.client_port = client_port
        self.retries = retries
        self.timeout = timeout

    def join(self):
        """Conecta al Index, manda payload 'join' y espera hasta recibir 'ok'."""
        payload = {"action": "join", "name": self.client_name, "port": self.client_port}
        try:
            Logger.info(f"Conectando al Index {self.index_ip}:{self.index_port}")
            s = socket.create_connection((self.index_ip, self.index_port), timeout=self.timeout)
            s.sendall((json.dumps(payload) + "\n").encode())

            f = s.makefile('r')
            while True:
                line = f.readline()
                if not line:
                    Logger.info("Index cerró la conexión antes de enviar estado final.")
                    return None

                try:
                    response = json.loads(line.strip())
                except Exception as e:
                    Logger.error(f"Respuesta inválida JSON: {e}")
                    return None

                if response.get("status") == "waiting":
                    Logger.info("Esperando a que todos los clientes se registren...")
                    
                    continue
                elif response.get("status") == "ok":
                    Logger.info("Todos los clientes listos, recibido estado final.")
                    s.close()
                    return response
                elif response.get("status") == "done":
                    Logger.info("Index cerró la conexión después de enviar el estado final.")
                    break
                else:
                    Logger.error(f"Respuesta inesperada del Index: {response}")
                    return None

        except Exception as e:
            Logger.error(f"Error en join: {e}")
            return None

        return None
