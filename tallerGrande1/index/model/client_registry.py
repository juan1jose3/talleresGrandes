import os

TOTAL_CLIENTS = int(os.environ.get('TOTAL_CLIENTS', '5'))

class ClientRegistry:
    def __init__(self):
        self._clients = [] 

    def add_client(self, name, ip, port):
       
        existing = next((c for c in self._clients if c['name'] == name), None)
        if existing:
            self._clients.remove(existing)
        
        client = {'name': name, 'ip': ip, 'port': port}
        self._clients.append(client)
        return list(self._clients)
        
    def get_all(self):
        return list(self._clients)

    def count(self):
        return len(self._clients)
