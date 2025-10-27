"""
Servicio de Contabilidad - Sistema Distribuido
==============================================

Microservicio encargado de generar y gestionar facturas del sistema.
Utiliza arquitectura MVC (Modelo-Vista-Controlador) y JSON-RPC para comunicación.

Funcionalidades:
    - Generación de facturas con cálculo de impuestos (IVA 19%, Impuesto Extra 4%)
    - Almacenamiento de historial de facturas
    - Notificación a Inventario para actualización de stock
    - Diferenciación entre compras (suma stock) y ventas (resta stock)

Endpoints JSON-RPC:
    - generar_factura(carrito, origen): Genera una nueva factura
    - recibir_factura(origen): Devuelve la última factura generada

Puerto: 5004
Host: 172.20.0.5


Librerias a instalar:
    - jsonrpcserver -> pip install jsonrpcserver 
    - requests -> pip install requests
"""

from jsonrpcserver import method, serve
from controller.factura_controller import FacturaController


@method
def generar_factura(carrito, origen=None):
    """
    Endpoint JSON-RPC para generar facturas.
    
    Args:
        carrito (list): Lista de productos a facturar
        origen (str, optional): Origen de la transacción
    
    Returns:
        Success: Respuesta con factura generada
    
    Example Request:
        {
            "jsonrpc": "2.0",
            "method": "generar_factura",
            "params": {
                "carrito": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "precio": 1200.0,
                        "comprar": 1
                    }
                ],
                "origen": "tienda"
            },
            "id": 1
        }
    
    Example Response:
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Factura generada",
                "factura": {
                    "fecha": "2025-10-21 20:50:16",
                    "origen": "tienda",
                    "productos": [...],
                    "subtotal": 1200.0,
                    "iva": 228.0,
                    "impuesto_extra": 48.0,
                    "total": 1476.0
                }
            },
            "id": 1
        }
    """
    return FacturaController.generar_factura(carrito, origen)


@method
def recibir_factura(origen=None):
    """
    Endpoint JSON-RPC para obtener la última factura.
    
    Args:
        origen (str, optional): Servicio solicitante
    
    Returns:
        Success: Respuesta con última factura registrada
    
    Example Request:
        {
            "jsonrpc": "2.0",
            "method": "recibir_factura",
            "params": {
                "origen": "comprasVentas"
            },
            "id": 1
        }
    
    Example Response:
        {
            "jsonrpc": "2.0",
            "result": {
                "factura": {
                    "fecha": "2025-10-21 20:50:16",
                    "origen": "tienda",
                    "subtotal": 1200.0,
                    "iva": 228.0,
                    "impuesto_extra": 48.0,
                    "total": 1476.0
                }
            },
            "id": 1
        }
    """
    return FacturaController.recibir_factura(origen)


if __name__ == "__main__":
    print("="*60)
    print("Servicio de Contabilidad corriendo en 192.168.1.5:5004")
    print("="*60)
    print("\nEndpoints disponibles:")
    print("  - generar_factura(carrito, origen)")
    print("  - recibir_factura(origen)")
    print("\nArquitectura: MVC (Modelo-Vista-Controlador)")
    print("Protocolo: JSON-RPC 2.0")
    print("="*60 + "\n")
    
    serve("192.168.1.5", 5004)