import os
import random
from threading import Lock

TOTAL_CLIENTS = int(os.environ.get('TOTAL_CLIENTS', '5'))


class ClientRegistry:
    def __init__(self):
        self._clients = [] 
        self._lock = Lock()
    def add_client(self, name, ip, port):
        with self._lock:

            existing = next((c for c in self._clients if c['name'] == name), None)
            if existing:
                self._clients.remove(existing)
            client = {'name': name, 'ip': ip, 'port': port}
            self._clients.append(client)
            return list(self._clients)
        
    def get_all(self):
        with self._lock:
            return list(self._clients)

    def count(self):
        with self._lock:
            return len(self._clients)