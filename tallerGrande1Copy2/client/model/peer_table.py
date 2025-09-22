import json
from pathlib import Path

class PeerTable:
    def __init__(self, storage_path=None):
        self.peers = []  # lista de dicts {name, ip, port}
        self.storage_path = Path(storage_path) if storage_path else Path("peers.json")
        self.load()

    def update(self, peers):
        """Reemplaza la tabla de peers y la persiste."""
        self.peers = peers or []
        self.save()

    def add_or_replace(self, peer):
        """Agrega o reemplaza un peer por name."""
        existing = next((p for p in self.peers if p.get("name") == peer.get("name")), None)
        if existing:
            self.peers = [p for p in self.peers if p.get("name") != peer.get("name")]
        self.peers.append(peer)
        self.save()

    def get_all(self):
        return list(self.peers)

    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(json.dumps(self.peers, indent=2))
        except Exception:
            # no queremos que falle por persistencia en disco
            pass

    def load(self):
        if self.storage_path.exists():
            try:
                self.peers = json.loads(self.storage_path.read_text())
            except Exception:
                self.peers = []
        else:
            self.peers = []
