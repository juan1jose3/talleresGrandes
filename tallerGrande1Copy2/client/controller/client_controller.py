import time
from pathlib import Path
import os

from model.peer_table import PeerTable
from model.number_list import NumberList
from view.logger import Logger

from controller.index_client import IndexClient
from controller.peer_server import PeerServer
from controller.trade_manager import TradeManager
from controller.turn_coordinator import TurnCoordinator

# Config desde variables de entorno
INDEX_IP = os.environ.get("INDEX_IP", "192.168.4.4")
INDEX_PORT = int(os.environ.get("INDEX_PORT", "5000"))
CLIENT_NAME = os.environ.get("CLIENT_NAME", "clienteX")
CLIENT_PORT = int(os.environ.get("CLIENT_PORT", "6000"))
DATA_DIR = os.environ.get("CLIENT_DATA_DIR", "/opt/cliente/data")
SERVE_AFTER_JOIN = os.environ.get("SERVE_AFTER_JOIN", "true").lower() in ("1", "true", "yes")


class ClientController:
    def __init__(self):
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        peers_path = Path(DATA_DIR) / "peers.json"
        numbers_path = Path(DATA_DIR) / "numbers.json"

        self.peers = PeerTable(storage_path=peers_path)
        self.numbers = NumberList(storage_path=numbers_path)

        self.index_client = IndexClient(INDEX_IP, INDEX_PORT, CLIENT_NAME, CLIENT_PORT)
        self.trade_manager = TradeManager(
            CLIENT_NAME, self.peers, self.numbers, get_current_turn=self.get_current_turn
        )
        self.peer_server = PeerServer(CLIENT_NAME, self.peers, self.numbers)

        self.turn = 0  # lo asigna el Index
        self.coordinator: TurnCoordinator | None = None
        self.my_turn_completed = False
        
        # Control de finalización
        self.completed_time = None
        self.max_serve_time = 30  # Máximo 30 segundos sirviendo después de completar

    def join_index(self):
        response = self.index_client.join()
        if not response:
            return False

        self.peers.update(response.get("peers", []))
        self.numbers.update(response.get("numbers", []))
        self.turn = response.get("turn", 0)

        # Inicializar TurnCoordinator (nueva versión sin threads)
        self.coordinator = TurnCoordinator(CLIENT_NAME, self.turn, self.peers)

        Logger.info(
            f"Registro OK. Peers recibidos: {len(self.peers.get_all())}; "
            f"Números recibidos: {len(self.numbers.numbers)}; "
            f"Turno asignado: {self.turn}"
        )
        return True

    def show_state(self):
        complete = "SI" if self.numbers.is_complete_set() else "NO"
        current_turn = self.get_current_turn()
        
        status = "Esperando"
        if self.is_my_turn():
            status = "MI TURNO" if not self.my_turn_completed else "Turno completado"

        Logger.info(f"Cliente: {CLIENT_NAME} (#{self.turn}) Puerto: {CLIENT_PORT} [Completo: {complete}]")
        Logger.info(f"Turno actual del sistema: {current_turn} | Mi estado: {status}")
        Logger.info(f"Números: {sorted(self.numbers.numbers)}")
        
        counts = {i: self.numbers.numbers.count(i) for i in range(11)}
        missing = [n for n in range(11) if counts[n] == 0]
        duplicates = [n for n in range(11) if counts[n] > 1]
        
        if missing:
            Logger.info(f"Faltantes: {sorted(missing)}")
        if duplicates:
            Logger.info(f"Duplicados: {sorted(duplicates)}")
        
        if self.numbers.is_complete_set():
            Logger.info("🎉 COLECCIÓN COMPLETA!")

    def is_my_turn(self):
        if not self.coordinator:
            return False
        return self.coordinator.is_my_turn()

    def get_current_turn(self):
        if not self.coordinator:
            return 1
        return self.coordinator.get_current_turn()

    def should_terminate(self):
        """Determina si el cliente debe terminar"""
        # Si completé mi colección
        if self.numbers.is_complete_set():
            if self.completed_time is None:
                self.completed_time = time.time()
                Logger.info(f"🎉 {CLIENT_NAME} COMPLETÓ SU COLECCIÓN! Sirviendo por {self.max_serve_time}s más")
            
            # Servir por un tiempo limitado después de completar
            elapsed = time.time() - self.completed_time
            if elapsed > self.max_serve_time:
                Logger.info(f"🏁 {CLIENT_NAME} terminando después de {elapsed:.1f}s sirviendo")
                return True
        
        return False

    def negotiate_if_needed(self):
        """Negocia solo si no he completado mi colección"""
        if self.numbers.is_complete_set():
            Logger.debug(f"{CLIENT_NAME} ya completó - no necesita negociar")
            return True
            
        Logger.info(f"🔄 {CLIENT_NAME} iniciando negociación en mi turno...")
        success = self.trade_manager.negotiate()
        
        if self.numbers.is_complete_set():
            Logger.info(f"🎊 {CLIENT_NAME} COMPLETÓ su colección durante la negociación!")
            return True
        elif success:
            Logger.info(f"📈 {CLIENT_NAME} hizo trades exitosos")
            return False  # No completé pero hice progreso
        else:
            Logger.info(f"📉 {CLIENT_NAME} no pudo hacer trades")
            return False

    def run(self):
        if SERVE_AFTER_JOIN:
            self.peer_server.start("0.0.0.0", CLIENT_PORT)
            Logger.info("🚀 Servidor de peers iniciado...")

            Logger.info("Sistema de turnos basado en tiempo iniciado...")

            max_rounds = 25  # Máximo 15 rondas de turnos
            round_count = 0

            try:
                while round_count < max_rounds:
                    round_count += 1
                    Logger.info(f"🔄 Ronda {round_count}/{max_rounds}")
                    
                    # Verificar si debo terminar
                    if self.should_terminate():
                        break
                    
                    # Esperar mi turno (procesa conexiones mientras espera)
                    self.coordinator.wait_for_my_turn(self.peer_server)
                    
                    # Ejecutar mi turno
                    if self.coordinator.start_my_turn():
                        turn_start_time = time.time()
                        
                        # Negociar durante mi turno
                        completed = self.negotiate_if_needed()
                        
                        # Completar mi turno
                        if completed and self.numbers.is_complete_set():
                            self.coordinator.complete_my_turn(collection_complete=True)
                            Logger.info(f"✅ Completé mi turno {self.turn} - ¡colección completa!")
                        else:
                            self.coordinator.complete_my_turn(collection_complete=False)
                            Logger.info(f"⏭️ Completé mi turno {self.turn} - pasando al siguiente")
                        
                        # Mostrar estado después de mi turno
                        self.show_state()
                        
                        # Esperar hasta que termine mi tiempo de turno
                        remaining_time = self.coordinator.get_remaining_turn_time()
                        if remaining_time > 1:
                            Logger.info(f"⏱️ Esperando {remaining_time:.1f}s hasta fin de mi turno...")
                            
                            end_time = time.time() + remaining_time
                            while time.time() < end_time:
                                self.peer_server.process_once()
                                time.sleep(0.2)
                        
                        Logger.info(f"✅ Mi turno {self.turn} completado")
                    
                    # Si ya completé, seguir sirviendo pero informar menos frecuentemente
                    if self.numbers.is_complete_set() and round_count % 3 == 0:
                        Logger.info(f"🎊 Colección completa, continuaré sirviendo a otros... (ronda {round_count})")

                Logger.info(f"🏁 {CLIENT_NAME} terminó después de {round_count} rondas")
                
                # Estado final
                self.show_state()
                if self.numbers.is_complete_set():
                    Logger.info(f"🎊 {CLIENT_NAME} TERMINÓ CON ÉXITO - Colección completa!")
                else:
                    missing = [n for n in range(11) if self.numbers.numbers.count(n) == 0]
                    Logger.info(f"⚠️ {CLIENT_NAME} terminó incompleto - Faltaban: {missing}")

            except KeyboardInterrupt:
                Logger.info("⛔ Cliente detenido manualmente.")
            finally:
                if self.coordinator:
                    self.coordinator.cleanup()
                self.peer_server.close()
        else:
            Logger.info("Fin (no se inició servidor de peers).")