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
            # Establecer timeout MUY corto para evitar bloqueos
            conn.settimeout(0.5)  # ⬅️ Cambiar de 2.0 a 0.5 segundos
            
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
                # ⬅️ Agregar shutdown explícito para cerrar la conexión más rápido
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
        """Procesa una solicitud de trade y retorna la respuesta"""
        offer = request.get("offer")
        want = request.get("want")
        from_peer = request.get("from")

        Logger.info(f"{self.name}: 💱 trade de {from_peer}, me ofrece {offer}, quiere {want}")

        # ✅ CORRECCIÓN: Verificar correctamente si puedo y debo hacer el trade
        current_numbers = self.numbers.numbers
        
        # Calcular cuántos tengo de cada número
        counts = {i: current_numbers.count(i) for i in range(11)}
        want_count = counts.get(want, 0)
        offer_count = counts.get(offer, 0)
        
        # Solo acepto si tengo MÁS DE 1 del que me piden Y necesito el que me ofrecen
        if want_count > 1 and offer_count == 0:
            # Aceptar el trade
            self.numbers.numbers.remove(want)
            self.numbers.numbers.append(offer)
            self.numbers.save()

            Logger.info(f"{self.name}: ✅ trade aceptado con {from_peer}, entregué {want}, recibí {offer}")
            Logger.info(f"{self.name}: 📋 nueva lista -> {sorted(self.numbers.numbers)}")
            
            return {"status": "accepted", "given": want}
        else:
            # ✅ CORRECCIÓN: Rechazar el trade con razones más precisas
            reason = ""
            if want_count <= 1:
                if want_count == 0:
                    reason = f"no tengo {want}"
                else:
                    reason = f"solo tengo 1 {want} (no puedo darlo)"
            elif offer_count > 0:
                reason = f"ya tengo {offer}"
            
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