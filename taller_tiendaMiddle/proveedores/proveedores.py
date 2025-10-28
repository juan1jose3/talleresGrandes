from jsonrpcserver import method, serve, Success
import requests
import json
import sys
from http.server import HTTPServer

URL_MIDDLEWARE = "http://192.168.1.10:5010"

@method
def proveedores():
    """
    Inicia el proceso de reabastecimiento.
    Delega toda la lógica al Middleware.
    """
    print("\n" + "="*60)
    print("PROVEEDORES: Solicitando reabastecimiento al Middleware")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "method": "middlewareControllerProveedores",
        "params": {"origen": "proveedores"},
        "id": 1
    }
    
    try:
        # El Middleware maneja todo el proceso
        response = requests.post(URL_MIDDLEWARE, json=payload, timeout=30)
        resultado = response.json()
        
        mensaje = resultado.get('result', {}).get('mensaje', 'Proceso completado')
        productos_comprados = resultado.get('result', {}).get('productos_comprados', [])
        
        print(f"\n{mensaje}")
        if productos_comprados:
            print(f"{len(productos_comprados)} productos reabastecidos")
        
        return Success(resultado.get('result', {}))
        
    except requests.exceptions.Timeout:
        print("Timeout esperando respuesta del Middleware")
        return Success({"mensaje": "Timeout en proceso"})
    except Exception as e:
        print(f"Error: {e}")
        return Success({"mensaje": f"Error: {e}"})


@method
def confirmar_recepcion_compra(productos, origen=None):
    """
    Recibe confirmación de que la compra fue procesada.
    """
    print("\n" + "="*60)
    print("CONFIRMACIÓN DE COMPRA RECIBIDA")
    print("="*60)
    print(f"Productos recibidos: {len(productos)} items")
    
    total_unidades = 0
    for p in productos:
        cantidad = p.get('comprar', 0)
        total_unidades += cantidad
        print(f"{p['nombre']}: +{cantidad} unidades")
    
    print(f"\nTotal agregado: {total_unidades} unidades")
    print("="*60 + "\n")
    
    return Success({"mensaje": "Compra confirmada por Proveedores"})


class SilentHTTPServer(HTTPServer):
    """HTTPServer que maneja BrokenPipe errors silenciosamente"""
    def handle_error(self, request, client_address):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type == BrokenPipeError:
            print(f"Cliente {client_address[0]} cerró conexión")
        else:
            super().handle_error(request, client_address)


if __name__ == "__main__":
    from jsonrpcserver.server import RequestHandler
    print("="*60)
    print("Servicio de Proveedores corriendo en 192.168.1.6:5005")
    print("="*60)
    print("\nEndpoints:")
    print("  - proveedores() → Inicia reabastecimiento")
    print("  - confirmar_recepcion_compra(productos, origen)")
    print("="*60 + "\n")
    
    server = SilentHTTPServer(("192.168.1.6", 5005), RequestHandler)
    server.serve_forever()