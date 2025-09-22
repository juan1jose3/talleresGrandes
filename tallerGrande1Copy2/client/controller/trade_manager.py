import socket
import json
import time
import random
from view.logger import Logger


class TradeManager:
    def __init__(self, client_name, peers, numbers, get_current_turn=None):
        self.client_name = client_name
        self.peers = peers
        self.numbers = numbers
        self.get_current_turn = get_current_turn
        
        # Configuración dinámica basada en cantidad de peers
        self.total_peers = len(peers.get_all()) - 1  # -1 porque no cuento a mí mismo
        
        # Timeouts más agresivos para 5+ nodos
        if self.total_peers >= 4:
            self.connection_timeout = 1.5  # Timeout más corto
            self.max_attempts_per_peer = 2  # Menos intentos por peer
        else:
            self.connection_timeout = 2.0
            self.max_attempts_per_peer = 3

    def attempt_trade(self, peer, offer, want):
        """Intenta un trade específico con timeout optimizado"""
        try:
            with socket.create_connection((peer["ip"], peer["port"]), timeout=self.connection_timeout) as s:
                payload = {
                    "action": "trade",
                    "offer": offer,
                    "want": want,
                    "from": self.client_name
                }
                s.sendall((json.dumps(payload) + "\n").encode())

                f = s.makefile("r")
                line = f.readline()
                if not line:
                    return False

                resp = json.loads(line.strip())
                if resp.get("status") == "accepted":
                    self.numbers.numbers.remove(offer)
                    self.numbers.numbers.append(resp["given"])
                    self.numbers.save()
                    
                    Logger.info(f"✅ Trade exitoso con {peer['name']}: di {offer} ← recibí {resp['given']}")
                    Logger.info(f"📊 Nueva lista: {sorted(self.numbers.numbers)}")
                    return True
                else:
                    Logger.debug(f"❌ Trade rechazado por {peer['name']}: {resp.get('reason', 'sin razón')}")
                    return False
                    
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            Logger.debug(f"🔌 No conecté con {peer.get('name', '??')}: {type(e).__name__}")
            return False
        except Exception as e:
            Logger.debug(f"🔌 Error inesperado con {peer.get('name', '??')}: {e}")
            return False

    def get_trade_opportunities(self):
        """Calcula qué números puedo ofrecer y cuáles necesito"""
        counts = {i: self.numbers.numbers.count(i) for i in range(11)}
        duplicates = [n for n in range(11) if counts[n] > 1]
        missing = [n for n in range(11) if counts[n] == 0]
        return duplicates, missing

    def negotiate_with_peer(self, peer):
        """Intenta trades con un peer específico - optimizado para 5+ nodos"""
        if peer.get("name") == self.client_name:
            return False
            
        Logger.info(f"🤝 Negociando con {peer['name']} ({peer['ip']}:{peer['port']})")
        
        trades_made = 0
        
        for attempt in range(self.max_attempts_per_peer):
            # Si ya completé, no seguir
            if self.numbers.is_complete_set():
                Logger.info(f"🎉 Colección completa durante negociación con {peer['name']}")
                return True
            
            duplicates, missing = self.get_trade_opportunities()
            
            if not duplicates or not missing:
                Logger.debug(f"💤 Sin oportunidades de trade con {peer['name']}")
                break
            
            # OPTIMIZACIÓN: Priorizar trades más inteligentemente
            # Ordenar missing por prioridad (números más bajos primero)
            missing_prioritized = sorted(missing)[:3]  # Solo los 3 más importantes
            
            # Shuffle duplicates para evitar patrones
            duplicates_shuffled = duplicates.copy()
            random.shuffle(duplicates_shuffled)
            
            trade_made = False
            
            for want in missing_prioritized:
                for offer in duplicates_shuffled[:2]:  # Solo probar los primeros 2 duplicados
                    Logger.debug(f"Intentando con {peer['name']}: ofrezco {offer}, quiero {want}")
                    
                    if self.attempt_trade(peer, offer, want):
                        trades_made += 1
                        trade_made = True
                        
                        # Verificar si completé colección
                        if self.numbers.is_complete_set():
                            Logger.info(f"🎉 Completé colección negociando con {peer['name']}!")
                            return True
                        
                        break  # Un trade exitoso, ir al siguiente número needed
                        
                if trade_made:
                    break  # Ya hice un trade en este intento
            
            if not trade_made:
                Logger.debug(f"No hice trades con {peer['name']} en intento {attempt + 1}")
                break  # No pude hacer trades, no seguir intentando
                
            # Pausa corta entre intentos con el mismo peer
            time.sleep(0.2)
        
        if trades_made > 0:
            Logger.info(f"📈 Trades realizados con {peer['name']}: {trades_made}")
            return True
        return False

    def negotiate(self):
        """Negocia con todos los peers - optimizado para 5+ nodos"""
        Logger.info(f"🔄 {self.client_name} iniciando ronda de negociación...")

        if self.numbers.is_complete_set():
            Logger.info(f"{self.client_name} ya tiene colección completa")
            return True
        
        duplicates, missing = self.get_trade_opportunities()
        
        if not duplicates or not missing:
            Logger.info(f"{self.client_name} no puede negociar (sin duplicados o sin faltantes)")
            return False
        
        Logger.info(f"{self.client_name} necesita: {sorted(missing)}")
        Logger.debug(f"{self.client_name} puede ofrecer: {sorted(duplicates)}")
        
        successful_peers = 0
        peers_list = self.peers.get_all()
        
        # OPTIMIZACIÓN: Randomizar orden de peers para evitar patrones
        available_peers = [p for p in peers_list if p.get("name") != self.client_name]
        random.shuffle(available_peers)
        
        for peer in available_peers:
            Logger.info(f"{self.client_name} -> {peer['name']} (iniciando negociación)")
            
            success = self.negotiate_with_peer(peer)
            if success:
                successful_peers += 1
            
            if self.numbers.is_complete_set():
                Logger.info(f"{self.client_name} completó su colección después de negociar con {peer['name']}!")
                return True
            
            # Pausa entre peers más corta para 5+ nodos
            time.sleep(0.3 if self.total_peers >= 4 else 0.5)
        
        # Resumen final
        final_missing = [n for n in range(11) if self.numbers.numbers.count(n) == 0]
        
        if successful_peers > 0:
            Logger.info(f"{self.client_name} hizo trades exitosos con {successful_peers} peers")
            if final_missing:
                Logger.info(f"{self.client_name} aún necesita: {sorted(final_missing)}")
            return True
        else:
            Logger.info(f"{self.client_name} no pudo hacer trades en esta ronda")
            Logger.info(f"{self.client_name} aún necesita: {sorted(final_missing)}")
            return False