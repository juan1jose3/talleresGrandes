import time
from view.logger import Logger

class TurnCoordinator:
    def __init__(self, client_name, my_turn, peers, data_dir=None, port=None, broadcast_ip=None):
        self.client_name = client_name
        self.my_turn = my_turn
        self.peers = peers
        
        # OPTIMIZACIÓN PARA 5+ NODOS: Duración dinámica basada en cantidad de clientes
        self.total_clients = len(peers.get_all())
        
        if self.total_clients <= 3:
            self.turn_duration = 10  # 10s para 3 nodos o menos
        elif self.total_clients == 4:
            self.turn_duration = 12  # 12s para 4 nodos  
        elif self.total_clients == 5:
            self.turn_duration = 15  # 15s para 5 nodos
        else:
            self.turn_duration = 18  # 18s para 6+ nodos
        
        self.system_start_time = None
        self.my_turn_completed = False
        
        Logger.info(f"[{self.client_name}] TurnCoordinator inicializado. Mi turno: {self.my_turn}")
        Logger.info(f"[{self.client_name}] Total clientes: {self.total_clients}, Duración por turno: {self.turn_duration}s")
        
        # Inicializar tiempo del sistema con sincronización más larga para 5+ nodos
        sync_delay = 5 if self.total_clients <= 3 else 8
        self._initialize_system_time(sync_delay)

    def _initialize_system_time(self, sync_delay):
        """Inicializa el tiempo base del sistema con sincronización"""
        Logger.info(f"[{self.client_name}] Sincronizando sistema de turnos en {sync_delay}s...")
        time.sleep(sync_delay)
        
        self.system_start_time = time.time()
        Logger.info(f"[{self.client_name}] Sistema de turnos iniciado")

    def get_current_turn(self):
        """Calcula qué cliente debe estar negociando ahora"""
        if not self.system_start_time:
            return 1
        
        elapsed = time.time() - self.system_start_time
        turn_cycles = int(elapsed / self.turn_duration)
        current_turn = (turn_cycles % self.total_clients) + 1
        return current_turn

    def is_my_turn(self):
        """Verifica si es mi turno y no lo he completado"""
        current = self.get_current_turn()
        return current == self.my_turn and not self.my_turn_completed

    def start_my_turn(self):
        """Marca el inicio de mi turno"""
        if self.is_my_turn() and not self.my_turn_completed:
            Logger.info(f"[{self.client_name}] INICIANDO MI TURNO {self.my_turn} (Duración: {self.turn_duration}s)")
            return True
        return False

    def complete_my_turn(self, collection_complete=False):
        """Marca mi turno como completado"""
        if self.my_turn_completed:
            Logger.debug(f"[{self.client_name}] Turno ya completado, ignorando")
            return

        self.my_turn_completed = True
        reason = "colección completa" if collection_complete else "sin más trades posibles"
        Logger.info(f"[{self.client_name}] TURNO {self.my_turn} COMPLETADO ({reason})")
        
        next_turn = (self.my_turn % self.total_clients) + 1
        Logger.info(f"[{self.client_name}] Siguiente turno será: {next_turn}")

    def update_status(self, collection_complete):
        """Actualiza estado interno"""
        Logger.debug(f"[{self.client_name}] Estado actualizado: completa={collection_complete}")

    def get_system_status(self):
        """Retorna estado del sistema"""
        current_turn = self.get_current_turn()
        return {
            "current_turn": current_turn,
            "my_turn": self.my_turn,
            "completed": self.my_turn_completed,
            "clients": [p.get("name") for p in self.peers.get_all()]
        }

    def all_clients_completed(self):
        """Siempre retorna False para compatibilidad"""
        return False

    def cleanup(self):
        """Limpia recursos"""
        Logger.info(f"[{self.client_name}] TurnCoordinator limpiado")

    def wait_for_my_turn(self, peer_server=None):
        """Espera hasta que sea mi turno, con mejor manejo para 5+ nodos"""
        while not self.is_my_turn():
            current_turn = self.get_current_turn()
            
            if self.system_start_time:
                elapsed = time.time() - self.system_start_time
                current_turn_start = ((current_turn - 1) * self.turn_duration)
                my_turn_start = ((self.my_turn - 1) * self.turn_duration)
                
                # Calcular siguiente ciclo si mi turno ya pasó
                if my_turn_start <= elapsed:
                    cycle_duration = self.total_clients * self.turn_duration
                    current_cycle = int(elapsed / cycle_duration)
                    next_cycle_start = (current_cycle + 1) * cycle_duration
                    my_turn_start = next_cycle_start + ((self.my_turn - 1) * self.turn_duration)
                
                time_to_my_turn = my_turn_start - elapsed
                
                # Solo mostrar log cada 5 segundos para reducir spam
                if time_to_my_turn > 1 and int(time_to_my_turn) % 5 == 0:
                    Logger.info(f"[{self.client_name}] Esperando mi turno ({self.my_turn}). "
                              f"Turno actual: {current_turn}, Tiempo restante: {time_to_my_turn:.1f}s")
            
            # Procesar conexiones mientras espero (más frecuentemente)
            if peer_server:
                for _ in range(10):  # Procesar 10 veces por segundo
                    peer_server.process_once()
                    time.sleep(0.1)
            else:
                time.sleep(1)
        
        # Reset completion status cuando empiece mi turno
        if self.is_my_turn():
            self.my_turn_completed = False
            Logger.info(f"[{self.client_name}] ¡Es MI TURNO! (Turno {self.my_turn})")

    def get_remaining_turn_time(self):
        """Calcula tiempo restante del turno actual"""
        if not self.system_start_time:
            return self.turn_duration
        
        elapsed = time.time() - self.system_start_time
        current_turn = self.get_current_turn()
        cycle_duration = self.total_clients * self.turn_duration
        current_cycle_start = int(elapsed / cycle_duration) * cycle_duration
        turn_start_in_cycle = ((current_turn - 1) * self.turn_duration)
        turn_start_absolute = current_cycle_start + turn_start_in_cycle
        turn_elapsed = elapsed - turn_start_absolute
        remaining = max(0, self.turn_duration - turn_elapsed)
        return remaining