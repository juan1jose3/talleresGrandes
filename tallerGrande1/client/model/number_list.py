import json
from pathlib import Path
from collections import Counter

class NumberList:
    def __init__(self, storage_path=None):
        self.numbers = []  # lista de enteros
        self.storage_path = Path(storage_path) if storage_path else Path("numbers.json")
        self.load()

    def update(self, numbers):
        self.numbers = numbers or []
        self.save()

    def counts(self):
        return dict(Counter(self.numbers))

    def is_complete_set(self):
        """¿Contiene al menos una vez cada dígito 0..10?"""
        return set(range(11)).issubset(set(self.numbers))

    def duplicates(self):
        c = self.counts()
        return {n: cnt for n, cnt in c.items() if cnt > 1}

    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(json.dumps(self.numbers, indent=2))
        except Exception:
            pass

    def load(self):
        if self.storage_path.exists():
            try:
                self.numbers = json.loads(self.storage_path.read_text())
            except Exception:
                self.numbers = []
        else:
            self.numbers = []
