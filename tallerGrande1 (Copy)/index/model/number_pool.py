import random

class NumberPool:
 
    def __init__(self, total_clients):
        self.total_clients = total_clients
        # Cada número de 0 a 10 aparece total_clients veces
        self._pool = {i: total_clients for i in range(11)}

    def remaining_counts(self):
        # Devuelve cuántos quedan de cada número
        return dict(self._pool)

    def assign_list(self, length=11):
        # Construir una lista con los números disponibles (con repeticiones)
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
