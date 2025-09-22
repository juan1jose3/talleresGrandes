import socket
import json
from view.logger import Logger

class PeerServer:
    def __init__(self, name, peers, numbers):
        self.name = name
        self.peers = peers
        self.numbers = numbers
        self.sock = None

    def start(self, host, port):
        """Arranca el servidor en modo no bloqueante"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.sock.setblocking(False)  
        Logger.info(f"{self.name}: servidor escuchando en {host}:{port}")

    def process_once(self):
        """Atiende conexiones entrantes si las hay, no bloquea"""
        if not self.sock:
            return

        # Procesar múltiples conexiones en esta iteración
        connections_processed = 0
        max_connections_per_cycle = 5

        while connections_processed < max_connections_per_cycle:
            try:
                conn, addr = self.sock.accept()
                Logger.debug(f"{self.name}: conexión entrante de {addr}")
                
                # Procesar la conexión inmediatamente
                self._handle_connection_sync(conn, addr)
                connections_processed += 1
                
            except BlockingIOError:
                # No hay más conexiones disponibles
                break
            except Exception as e:
                Logger.error(f"{self.name}: error aceptando conexión: {e}")
                break

    def _handle_connection_sync(self, conn, addr):
        """Maneja una conexión de forma síncrona y rápida"""
        try:
            # Timeout más corto para ser más ágil
            conn.settimeout(0.3)
            
            data = conn.recv(4096)
            if not data:
                Logger.debug(f"{self.name}: conexión vacía de {addr}")
                return

            msg = data.decode("utf-8").strip()
            Logger.debug(f"{self.name}: recibido de {addr} -> {msg}")

            try:
                request = json.loads(msg)
            except json.JSONDecodeError as e:
                Logger.error(f"{self.name}: mensaje inválido de {addr}, no es JSON: {e}")
                conn.sendall(b'{"status":"error","reason":"invalid_json"}\n')
                return

            # Procesar solo trades
            if request.get("action") == "trade":
                response = self._process_trade(request, addr)
                conn.sendall((json.dumps(response) + "\n").encode())
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except:
                    pass
            else:
                Logger.debug(f"{self.name}: acción desconocida de {addr}: {request.get('action')}")
                conn.sendall(b'{"status":"error","reason":"unknown_action"}\n')

        except socket.timeout:
            Logger.debug(f"{self.name}: timeout leyendo de {addr}")
        except ConnectionResetError:
            Logger.debug(f"{self.name}: conexión resetada por {addr}")
        except Exception as e:
            Logger.error(f"{self.name}: error inesperado con {addr}: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def _process_trade(self, request, addr):
        """Procesa una solicitud de trade con lógica mejorada para evitar deadlocks"""
        offer = request.get("offer")
        want = request.get("want")
        from_peer = request.get("from")

        Logger.info(f"{self.name}: trade de {from_peer}, me ofrece {offer}, quiere {want}")

        # Verificar que ambos números son válidos
        if offer is None or want is None or not (0 <= offer <= 10) or not (0 <= want <= 10):
            return {"status": "rejected", "reason": "números inválidos"}

        current_numbers = self.numbers.numbers
        counts = {i: current_numbers.count(i) for i in range(11)}
        want_count = counts.get(want, 0)
        offer_count = counts.get(offer, 0)
        
        # LÓGICA MEJORADA: Más flexible para evitar deadlocks
        should_accept = False
        reason = ""
        
        # Si no tengo lo que me pide, rechazo inmediatamente
        if want_count == 0:
            reason = f"no tengo {want}"
            should_accept = False
        else:
            # Caso 1: No tengo el número que me ofrecen (lo necesito urgentemente)
            if offer_count == 0:
                # Siempre acepto si no tengo el número ofrecido, incluso si es mi último
                should_accept = True
                Logger.debug(f"{self.name}: acepto porque necesito urgentemente {offer}")
                
            # Caso 2: Ya tengo el número que me ofrecen
            elif offer_count > 0:
                # Solo acepto si tengo más de 1 del número que piden
                if want_count > 1:
                    should_accept = True
                    Logger.debug(f"{self.name}: acepto porque tengo {want_count} copias de {want}")
                else:
                    # CASO ESPECIAL: Si tengo solo 1, pero el trade me ayuda a reducir números faltantes
                    temp_counts = counts.copy()
                    temp_counts[want] -= 1
                    temp_counts[offer] += 1
                    
                    missing_before = sum(1 for i in range(11) if counts[i] == 0)
                    missing_after = sum(1 for i in range(11) if temp_counts[i] == 0)
                    
                    if missing_after < missing_before:
                        should_accept = True
                        Logger.debug(f"{self.name}: acepto trade beneficioso: faltantes {missing_before}→{missing_after}")
                    else:
                        reason = f"ya tengo {offer} y necesito mi único {want}"
        
        if should_accept and want_count > 0:
            # Realizar el trade
            self.numbers.numbers.remove(want)
            self.numbers.numbers.append(offer)
            self.numbers.save()

            Logger.info(f"{self.name}: ✅ TRADE ACEPTADO con {from_peer}, entregué {want}, recibí {offer}")
            Logger.info(f"{self.name}: nueva lista -> {sorted(self.numbers.numbers)}")
            
            # Verificar si completé mi colección
            new_counts = {i: self.numbers.numbers.count(i) for i in range(11)}
            missing_after_trade = [n for n in range(11) if new_counts[n] == 0]
            
            if not missing_after_trade:
                Logger.info(f"{self.name}: 🎉 ¡COLECCIÓN COMPLETA después del trade!")
            
            return {"status": "accepted", "given": want}
        else:
            # Rechazar el trade
            if not reason:
                if want_count == 0:
                    reason = f"no tengo {want}"
                else:
                    reason = f"trade no beneficioso"
            
            Logger.debug(f"{self.name}: ❌ trade rechazado con {from_peer} ({reason})")
            return {"status": "rejected", "reason": reason}

    def close(self):
        """Cierra el servidor"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        Logger.info(f"{self.name}: servidor cerrado")