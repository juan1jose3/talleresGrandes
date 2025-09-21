import time
from pathlib import Path
import os

from client.model.peer_table import PeerTable
from client.model.number_list import NumberList
from view.logger import Logger

from controller.index_client import IndexClient
from controller.peer_server import PeerServer
from controller.trade_manager import TradeManager

INDEX_IP = os.environ.get("INDEX_IP", "192.168.4.4")
INDEX_PORT = int(os.environ.get("INDEX_PORT", "5000"))
CLIENT_NAME = os.environ.get("CLIENT_NAME", "clienteX")
CLIENT_PORT = int(os.environ.get("CLIENT_PORT", "6000"))
DATA_DIR = os.environ.get("CLIENT_DATA_DIR", "/opt/cliente/data")
SERVE_AFTER_JOIN = os.environ.get("SERVE_AFTER_JOIN", "true").lower() in ("1", "true", "yes")
TURN_DURATION = int(os.environ.get("TURN_DURATION", "30"))  # Duración de cada turno en segundos

class ClientController:
    def __init__(self):
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        peers_path = Path(DATA_DIR) / "peers.json"
        numbers_path = Path(DATA_DIR) / "numbers.json"

        self.peers = PeerTable(storage_path=peers_path)
        self.numbers = NumberList(storage_path=numbers_path)

        self.index_client = IndexClient(INDEX_IP, INDEX_PORT, CLIENT_NAME, CLIENT_PORT)
        self.trade_manager = TradeManager(CLIENT_NAME, self.peers, self.numbers)
        self.peer_server = PeerServer(CLIENT_NAME, self.peers, self.numbers)
        self.turn = 0  # valor por defecto hasta que el Index lo asigne
        self.start_time = None  # tiempo de inicio de negociaciones
        self.my_turn_completed = False  # flag para saber si ya completé mi turno

    def join_index(self):
        response = self.index_client.join()
        if not response:
            return False

        self.peers.update(response.get("peers", []))
        self.numbers.update(response.get("numbers", []))
        self.turn = response.get("turn", 0)  # guardamos turno que manda el Index

        Logger.info(
            f"Registro OK. Peers recibidos: {len(self.peers.get_all())}; "
            f"Números recibidos: {len(self.numbers.numbers)}; "
            f"Turno asignado: {self.turn}"
        )
        return True

    def show_state(self):
        complete = "✓" if self.numbers.is_complete_set() else "✗"
        turn_status = "✅ Completado" if self.my_turn_completed else ("🔄 Activo" if self.is_my_turn() else "⏳ Esperando")
    
        Logger.info(f"Nombre: {CLIENT_NAME}  Puerto: {CLIENT_PORT} [Completo: {complete}]")
        Logger.info(f"Números: {sorted(self.numbers.numbers)}")
        Logger.info(f"Conteos: {self.numbers.counts()}")
        Logger.info(f"Duplicados: {self.numbers.duplicates()}")
        Logger.info(f"Turno asignado: {self.turn} | Turno actual: {self.get_current_turn()} | Estado: {turn_status}")
        if self.numbers.is_complete_set():
            Logger.info("🎉 ¡COLECCIÓN COMPLETA!")

    def is_my_turn(self):
        """Determina si es el turno de este cliente para negociar"""
        # Solo dejar de negociar si realmente completé la colección
        if self.my_turn_completed and self.numbers.is_complete_set():
            return False
        
        current_turn = self.get_current_turn()
        return self.turn == current_turn

    def get_current_turn(self):
        """Calcula qué turno está activo basado en el tiempo transcurrido"""
        if self.start_time is None:
            return 1  # Por defecto, turno 1
        
        elapsed_time = time.time() - self.start_time
        total_clients = len(self.peers.get_all())
        current_turn = int(elapsed_time // TURN_DURATION) % total_clients + 1
        return current_turn

    def run(self, negotiate_interval=3):
        if SERVE_AFTER_JOIN:
            self.peer_server.start("0.0.0.0", CLIENT_PORT)
            Logger.info("Servidor de peers iniciado...")

            # Esperar un momento inicial para que todos los servidores estén listos
            initial_wait = 5
            Logger.info(f"Esperando {initial_wait}s para que todos los servidores estén listos...")
            time.sleep(initial_wait)
            
            # Marcar tiempo de inicio de negociaciones
            self.start_time = time.time()
            Logger.info("Iniciando sistema de turnos para negociación...")

            cycles_without_activity = 0
            max_idle_cycles = 20

            try:
                while True:
                    # Siempre atender conexiones entrantes
                    self.peer_server.process_once()
                    
                    activity_detected = False
                    
                    # Solo negociar si es mi turno Y no estoy completo
                    if self.is_my_turn() and not self.numbers.is_complete_set():
                        Logger.info(f"🔄 Es mi turno ({self.turn}), iniciando negociación...")
                        success = self.trade_manager.negotiate()
                        activity_detected = True
                        
                        # Solo marcar como completado si realmente completé la colección
                        if self.numbers.is_complete_set():
                            self.my_turn_completed = True
                            Logger.info(f"🎉 ¡Completé mi colección en el turno {self.turn}!")
                        elif not success:
                            # Si no pude negociar, esperar al siguiente ciclo de turnos
                            Logger.info(f"⏭️ No pude negociar en turno {self.turn}, esperaré siguiente ronda")
                    
                    elif self.is_my_turn() and self.numbers.is_complete_set():
                        # Si es mi turno pero ya estoy completo, marco como completado
                        if not self.my_turn_completed:
                            self.my_turn_completed = True
                            Logger.info(f"✅ Ya tengo colección completa, salto mi turno {self.turn}")
                            activity_detected = True
                    
                    # Si completé mi colección, terminar el cliente
                    if self.numbers.is_complete_set():
                        Logger.info("🎊 ¡Colección completa! Terminando cliente.")
                        break
                    
                    # Contador de inactividad
                    if activity_detected:
                        cycles_without_activity = 0
                    else:
                        cycles_without_activity += 1
                    
                    # Si todos han completado sus turnos y no hay actividad, terminar
                    if cycles_without_activity >= max_idle_cycles:
                        total_clients = len(self.peers.get_all())
                        elapsed_time = time.time() - self.start_time
                        completed_rounds = int(elapsed_time // TURN_DURATION)
                        
                        if completed_rounds >= total_clients:  # Al menos una ronda completa
                            Logger.info(f"🏁 Sin actividad por {cycles_without_activity} ciclos. Terminando...")
                            break
                    
                    self.show_state()
                    time.sleep(negotiate_interval)
                    
            except KeyboardInterrupt:
                Logger.info("Cliente detenido manualmente.")
        else:
            Logger.info("Fin (no se inició servidor de peers).")