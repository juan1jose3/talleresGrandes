import socket
import json
from view.logger import Logger

class TradeManager:
    def __init__(self, client_name, peers, numbers):
        self.client_name = client_name
        self.peers = peers
        self.numbers = numbers

    def attempt_trade(self, peer, offer, want):
        """Intenta un trade específico con un peer"""
        try:
            # ✅ CORRECCIÓN: Pausa más larga entre intentos
            import time
            time.sleep(0.5)  # 500ms de pausa entre intentos (antes 200ms)
            
            # ✅ CORRECCIÓN: Timeout más largo para conexiones
            with socket.create_connection((peer["ip"], peer["port"]), timeout=10) as s:  # antes timeout=1
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
                    Logger.info(f"✅ Trade exitoso con {peer['name']}: di {offer}, recibí {resp['given']}")
                    Logger.info(f"📋 Lista después del trade: {sorted(self.numbers.numbers)}")
                    return True
                else:
                    Logger.debug(f"❌ Trade rechazado por {peer['name']} (ofrecí {offer}, quería {want})")
                    return False
        except Exception as e:
            Logger.debug(f"🔌 No se pudo conectar con {peer.get('name', '??')}: {e}")
            return False
    
    def negotiate_with_peer(self, peer):
        """Intenta negociar con un peer específico hasta completarse o no poder más"""
        Logger.info(f"🤝 Negociando con {peer['name']} ({peer['ip']}:{peer['port']})")
        
        trades_made = 0
        max_attempts = 5  # Aumentamos intentos para más oportunidades
        
        for attempt in range(max_attempts):
            # Verificar si ya estoy completo
            if self.numbers.is_complete_set():
                Logger.info(f"🎉 ¡Colección completa! Deteniendo negociación con {peer['name']}")
                return True
            
            # ✅ CORRECCIÓN CLAVE: Calcular correctamente qué números necesito
            counts = {i: self.numbers.numbers.count(i) for i in range(11)}
            duplicates = [n for n in range(11) if counts[n] > 1]  # Tengo más de 1
            missing = [n for n in range(11) if counts[n] == 0]    # No tengo ninguno
            
            if not duplicates or not missing:
                Logger.debug(f"📝 No hay más trades posibles con {peer['name']}")
                break
            
            # Intentar trades de manera más inteligente
            trade_attempted = False
            
            # Priorizar intercambios más beneficiosos
            for offer in duplicates:
                for want in missing:
                    Logger.debug(f"💱 Intentando con {peer['name']}: ofrezco {offer}, quiero {want}")
                    
                    if self.attempt_trade(peer, offer, want):
                        trades_made += 1
                        trade_attempted = True
                        break  # Salir del loop interno
                if trade_attempted:
                    break  # Salir del loop externo
            
            # Si no se pudo hacer ningún trade, terminar con este peer
            if not trade_attempted:
                Logger.debug(f"🚫 No se pudo hacer más trades con {peer['name']}")
                break
        
        if trades_made > 0:
            Logger.info(f"📊 Trades realizados con {peer['name']}: {trades_made}")
        return trades_made > 0

    def negotiate(self):
        """Negocia secuencialmente con cada peer según el diagrama"""
        Logger.info(f"🔄 {self.client_name} iniciando ronda de negociación...")
        
        # Verificar si ya estoy completo antes de empezar
        if self.numbers.is_complete_set():
            Logger.info(f"✅ {self.client_name} ya tiene colección completa, no necesita negociar")
            return True
        
        # ✅ CORRECCIÓN: Calcular correctamente qué números necesito
        counts = {i: self.numbers.numbers.count(i) for i in range(11)}
        initial_missing = [n for n in range(11) if counts[n] == 0]
        initial_duplicates = [n for n in range(11) if counts[n] > 1]
        
        Logger.info(f"📋 {self.client_name} necesita: {sorted(initial_missing)}")
        Logger.debug(f"💰 {self.client_name} puede ofrecer: {sorted(initial_duplicates)}")
        
        total_successful_peers = 0
        peers_list = self.peers.get_all()
        
        # Negociar con cada peer en orden (excluyendo a mí mismo)
        for peer in peers_list:
            if peer.get("name") == self.client_name:
                continue
            
            Logger.info(f"👥 {self.client_name} -> {peer['name']} (iniciando negociación)")
            
            # Negociar con este peer
            success = self.negotiate_with_peer(peer)
            if success:
                total_successful_peers += 1
            
            # Si ya completé mi colección, terminar inmediatamente
            if self.numbers.is_complete_set():
                Logger.info(f"🎯 {self.client_name} completó su colección después de negociar con {peer['name']}!")
                return True
            
            # ✅ CORRECCIÓN: Pausa más larga entre peers
            import time
            time.sleep(0.5)  # 500ms entre peers (antes 300ms)
        
        # Resumen de la ronda
        counts = {i: self.numbers.numbers.count(i) for i in range(11)}
        final_missing = [n for n in range(11) if counts[n] == 0]
        
        if total_successful_peers > 0:
            Logger.info(f"📈 {self.client_name} hizo trades exitosos con {total_successful_peers} peers")
            if final_missing:
                Logger.info(f"📋 {self.client_name} aún necesita: {sorted(final_missing)}")
            return True
        else:
            Logger.info(f"📉 {self.client_name} no pudo hacer trades en esta ronda")
            Logger.info(f"📋 {self.client_name} aún necesita: {sorted(final_missing)}")
            return False