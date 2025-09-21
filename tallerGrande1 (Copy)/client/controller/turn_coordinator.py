import json
import time
from pathlib import Path
from view.logger import Logger

class TurnCoordinator:
    def __init__(self, client_name, my_turn, peers, data_dir):
        self.client_name = client_name
        self.my_turn = my_turn
        self.peers = peers
        self.data_dir = Path(data_dir)
        self.turn_file = self.data_dir / "current_turn.json"
        self.status_file = self.data_dir / f"status_{client_name}.json"
        
        # Estado interno
        self.my_turn_completed = False
        self.start_time = time.time()
        
        # Inicializar archivos de coordinación
        self._initialize_coordination_files()
    
    def _initialize_coordination_files(self):
        """Inicializa los archivos de coordinación si no existen"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Archivo de turno actual (solo el cliente 1 lo inicializa)
            if self.my_turn == 1 and not self.turn_file.exists():
                self._write_json(self.turn_file, {
                    "current_turn": 1,
                    "last_update": time.time(),
                    "active_client": None
                })
            
            # Archivo de estado propio
            self._write_json(self.status_file, {
                "client_name": self.client_name,
                "turn": self.my_turn,
                "completed": False,
                "collection_complete": False,
                "last_update": time.time()
            })
            
        except Exception as e:
            Logger.error(f"Error inicializando archivos de coordinación: {e}")
    
    def _read_json(self, file_path):
        """Lee un archivo JSON de forma segura"""
        try:
            if file_path.exists():
                return json.loads(file_path.read_text())
        except Exception as e:
            Logger.debug(f"Error leyendo {file_path}: {e}")
        return {}
    
    def _write_json(self, file_path, data):
        """Escribe un archivo JSON de forma segura con retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Escribir a archivo temporal primero para atomicidad
                temp_file = file_path.with_suffix('.tmp')
                temp_file.write_text(json.dumps(data, indent=2))
                temp_file.replace(file_path)  # Operación atómica
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    Logger.error(f"Error escribiendo {file_path}: {e}")
                else:
                    time.sleep(0.1)  # Breve pausa antes de reintentar
    
    def is_my_turn(self):
        """Determina si es mi turno basado en coordinación distribuida"""
        if self.my_turn_completed:
            return False
        
        turn_data = self._read_json(self.turn_file)
        current_turn = turn_data.get("current_turn", 1)
        
        return self.my_turn == current_turn
    
    def get_current_turn(self):
        """Obtiene el turno actual del sistema"""
        turn_data = self._read_json(self.turn_file)
        return turn_data.get("current_turn", 1)
    
    def start_my_turn(self):
        """Marca el inicio de mi turno"""
        if self.my_turn_completed:
            return False
            
        turn_data = self._read_json(self.turn_file)
        if turn_data.get("current_turn") == self.my_turn:
            turn_data["active_client"] = self.client_name
            turn_data["last_update"] = time.time()
            self._write_json(self.turn_file, turn_data)
            
            Logger.info(f"🎯 {self.client_name} iniciando turno {self.my_turn}")
            return True
        return False
    
    def complete_my_turn(self, collection_complete=False):
        """Marca mi turno como completado y pasa al siguiente"""
        if self.my_turn_completed:
            return
            
        self.my_turn_completed = True
        
        # Actualizar mi estado
        status_data = {
            "client_name": self.client_name,
            "turn": self.my_turn,
            "completed": True,
            "collection_complete": collection_complete,
            "last_update": time.time()
        }
        self._write_json(self.status_file, status_data)
        
        # Avanzar al siguiente turno
        turn_data = self._read_json(self.turn_file)
        total_clients = len(self.peers.get_all())
        next_turn = (turn_data.get("current_turn", 1) % total_clients) + 1
        
        turn_data.update({
            "current_turn": next_turn,
            "active_client": None,
            "last_update": time.time()
        })
        self._write_json(self.turn_file, turn_data)
        
        reason = "colección completa" if collection_complete else "no pude negociar más"
        Logger.info(f"✅ {self.client_name} completó turno {self.my_turn} ({reason})")
        Logger.info(f"➡️  Siguiente turno: {next_turn}")
    
    def update_status(self, collection_complete):
        """Actualiza el estado sin completar el turno"""
        status_data = {
            "client_name": self.client_name,
            "turn": self.my_turn,
            "completed": self.my_turn_completed,
            "collection_complete": collection_complete,
            "last_update": time.time()
        }
        self._write_json(self.status_file, status_data)
    
    def get_system_status(self):
        """Obtiene el estado de todos los clientes"""
        status = {
            "current_turn": self.get_current_turn(),
            "clients": {}
        }
        
        for peer in self.peers.get_all():
            client_name = peer.get("name")
            status_file = self.data_dir / f"status_{client_name}.json"
            client_status = self._read_json(status_file)
            status["clients"][client_name] = client_status
        
        return status
    
    def all_clients_completed(self):
        """Verifica si todos los clientes han completado sus colecciones"""
        system_status = self.get_system_status()
        
        for client_name, client_data in system_status["clients"].items():
            if not client_data.get("collection_complete", False):
                return False
        
        return len(system_status["clients"]) == len(self.peers.get_all())
    
    def cleanup(self):
        """Limpia archivos de coordinación al terminar"""
        try:
            if self.status_file.exists():
                self.status_file.unlink()
        except Exception as e:
            Logger.debug(f"Error limpiando archivos: {e}")

    