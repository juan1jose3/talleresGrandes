import random
import threading

class NumberPool:
    """
    Mantiene un pool de números compuesto por N copias de cada dígito 0..10.
    """
    def __init__(self, total_clients):
        self.total_clients = total_clients
        self._lock = threading.Lock()
        self._pool = {i: total_clients for i in range(11)}

    def remaining_counts(self):
        with self._lock:
            return dict(self._pool)

    def assign_list(self, length=11):
        with self._lock:
            available = [n for n, cnt in self._pool.items() for _ in range(cnt)]
            if not available:
                return []
            chosen = []
            for _ in range(min(length, len(available))):
                pick = random.choice(available)
                chosen.append(pick)
                self._pool[pick] -= 1
                available.remove(pick)
            random.shuffle(chosen)
            return chosen