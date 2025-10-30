"""
Microservicio de Proveedores - Sistema Distribuido de Gestión de Inventario
============================================================================

Este microservicio gestiona el reabastecimiento de inventario en el sistema
distribuido utilizando JSON-RPC 2.0. Actúa como iniciador del proceso de
reabastecimiento, delegando toda la lógica de negocio al middleware orquestador.

Configuración del Servicio
--------------------------
- **Host:** 192.168.1.6
- **Puerto:** 5005
- **Protocolo:** JSON-RPC 2.0
- **Versión:** 1.0.0
- **Middleware:** http://192.168.1.10:5010

Dependencias
------------
Este servicio se comunica con:
    - Middleware (192.168.1.10:5010): Para orquestar el proceso de reabastecimiento
    - Servicio de Inventario (indirectamente): A través del middleware
    - Servicio de Compras (indirectamente): A través del middleware

Variables Globales
-----------------
URL_MIDDLEWARE : str
    URL del servicio middleware para comunicación entre microservicios.
    Valor: "http://192.168.1.10:5010"

Flujo de Operación
------------------
1. El servicio invoca 'proveedores' para iniciar el reabastecimiento
2. Se delega al middleware que coordina todo el proceso
3. El middleware consulta inventario para identificar productos con bajo stock
4. El middleware genera órdenes de compra en el servicio de compras
5. El middleware confirma el resultado mediante 'confirmar_recepcion_compra'

Ejemplo de Uso
--------------
Para iniciar el servicio::

    python proveedores.py

El servicio quedará escuchando peticiones JSON-RPC en 192.168.1.6:5005

Ejemplo de flujo completo desde cliente JSON-RPC::

    import requests
    
    # Iniciar proceso de reabastecimiento
    payload = {
        "jsonrpc": "2.0",
        "method": "proveedores",
        "params": {},
        "id": 1
    }
    
    response = requests.post("http://192.168.1.6:5005", json=payload)

Notas
-----
- Este servicio NO contiene lógica de negocio, solo orquestación
- Implementa el patrón de delegación al middleware
- Utiliza callbacks para recibir confirmación del proceso
- Timeout configurado a 30 segundos para operaciones largas

See Also
--------
middleware : Orquestador del sistema distribuido
inventario : Servicio de gestión de stock
compras : Servicio de procesamiento de órdenes de compra
"""

from jsonrpcserver import method, serve, Success
import requests
import json
import sys
from http.server import HTTPServer

# URL del middleware para comunicación entre servicios
URL_MIDDLEWARE = "http://192.168.1.10:5010"


@method
def proveedores():
    """
    Solicita el reabastecimiento de inventario al middleware.
    
    Este método inicia el proceso de reabastecimiento delegando toda la lógica
    al middleware orquestador. El middleware se encarga de:
    1. Consultar el inventario actual
    2. Identificar productos con bajo stock
    3. Generar órdenes de compra
    4. Procesar las compras con el servicio de compras
    5. Confirmar el resultado a través de 'confirmar_recepcion_compra'
    
    El servicio actúa únicamente como iniciador del proceso, siguiendo el
    patrón de orquestación donde el middleware contiene toda la lógica de negocio.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    Success
        Objeto Success con el resultado del proceso de reabastecimiento:
        
        {
            "mensaje": str,
            "productos_comprados": list of dict
        }
        
        Donde cada producto en 'productos_comprados' tiene la estructura:
        
        {
            "id": int,
            "nombre": str,
            "categoria": str,
            "comprar": int,
            "precio_unitario": float,
            "subtotal": float
        }
    
    Raises
    ------
    requests.exceptions.Timeout
        Si el middleware no responde en 30 segundos. Retorna Success con
        mensaje de timeout en lugar de propagar la excepción.
    
    requests.exceptions.RequestException
        Si hay errores de conexión con el middleware. Retorna Success con
        mensaje de error en lugar de propagar la excepción.
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "proveedores",
            "params": {},
            "id": 1
        }
    
    Respuesta exitosa JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Reabastecimiento completado exitosamente",
                "productos_comprados": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "comprar": 10,
                        "precio_unitario": 1200.0,
                        "subtotal": 12000.0
                    },
                    {
                        "id": 3,
                        "nombre": "Mesa de Centro",
                        "categoria": "Sala",
                        "comprar": 15,
                        "precio_unitario": 350.0,
                        "subtotal": 5250.0
                    }
                ]
            },
            "id": 1
        }
    
    Salida por consola (proceso exitoso)::
    
        ============================================================
        PROVEEDORES: Solicitando reabastecimiento al Middleware
        ============================================================
        
        Reabastecimiento completado exitosamente
        2 productos reabastecidos
    
    Respuesta con timeout JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Timeout en proceso"
            },
            "id": 1
        }
    
    Salida por consola (timeout)::
    
        ============================================================
        PROVEEDORES: Solicitando reabastecimiento al Middleware
        ============================================================
        Timeout esperando respuesta del Middleware
    
    Respuesta con error JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Error: Connection refused"
            },
            "id": 1
        }
    
    Salida por consola (error)::
    
        ============================================================
        PROVEEDORES: Solicitando reabastecimiento al Middleware
        ============================================================
        Error: Connection refused
    
    Notes
    -----
    - El timeout está configurado a 30 segundos para permitir procesos largos
    - Imprime información diagnóstica en consola para debugging y auditoría
    - Los errores se capturan y retornan como Success para mantener el protocolo JSON-RPC
    - El middleware invocado es 'middlewareControllerProveedores'
    - Este método NO contiene lógica de negocio, solo inicia el proceso
    
    Warnings
    --------
    - Requiere que el middleware esté corriendo en 192.168.1.10:5010
    - Si el middleware no está disponible, retorna error pero no falla
    - Los mensajes de error se imprimen en stdout, no stderr
    
    See Also
    --------
    confirmar_recepcion_compra : Recibe la confirmación del middleware
    middlewareControllerProveedores : Método del middleware que procesa la solicitud
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
    Recibe y confirma la recepción de productos comprados.
    
    Este método actúa como callback para que el middleware notifique al servicio
    de proveedores que el proceso de compra se completó exitosamente. Registra
    en consola los detalles de los productos reabastecidos para auditoría.
    
    Parameters
    ----------
    productos : list of dict
        Lista de productos que fueron comprados. Cada producto debe tener:
        
        {
            "id": int,
            "nombre": str,
            "categoria": str,
            "comprar": int,
            "precio_unitario": float,
            "subtotal": float
        }
    
    origen : str, optional
        Identificador del servicio que envía la confirmación (típicamente "middleware").
        Se utiliza para logging y trazabilidad.
        Default: None
    
    Returns
    -------
    Success
        Objeto Success con confirmación de recepción:
        
        {
            "mensaje": "Compra confirmada por Proveedores"
        }
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "confirmar_recepcion_compra",
            "params": {
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "comprar": 10,
                        "precio_unitario": 1200.0,
                        "subtotal": 12000.0
                    },
                    {
                        "id": 3,
                        "nombre": "Mesa de Centro",
                        "categoria": "Sala",
                        "comprar": 15,
                        "precio_unitario": 350.0,
                        "subtotal": 5250.0
                    }
                ],
                "origen": "middleware"
            },
            "id": 2
        }
    
    
    
    Respuesta JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Compra confirmada por Proveedores"
            },
            "id": 2
        }
    
    Con lista vacía de productos::
    
        {
            "jsonrpc": "2.0",
            "method": "confirmar_recepcion_compra",
            "params": {
                "productos": [],
                "origen": "middleware"
            },
            "id": 3
        }
    
   
    
    Notes
    -----
    - Imprime un resumen detallado en consola para auditoría y debugging
    - Calcula automáticamente el total de unidades recibidas
    - El parámetro 'origen' es opcional y se usa para trazabilidad
    - No persiste la información, solo la registra en consola
    - Utiliza el campo 'comprar' de cada producto para determinar cantidad
    
    Warnings
    --------
    - No valida la estructura de los productos recibidos
    - Si 'comprar' no existe en un producto, se asume 0
    - No verifica que los productos existan en el sistema
    
    See Also
    --------
    proveedores : Método que inicia el proceso de reabastecimiento
    middlewareControllerProveedores : Método del middleware que orquesta el proceso
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


if __name__ == "__main__":
    """
    Punto de entrada principal del servicio.
    
    Inicia el servidor JSON-RPC en la dirección y puerto configurados.
    El servidor queda escuchando peticiones HTTP POST con payloads JSON-RPC 2.0.
    
    Configuración del Servidor
    --------------------------
    - IP: 192.168.1.6
    - Puerto: 5005
    - Protocolo: HTTP
    - Formato: JSON-RPC 2.0
    
    Endpoints Disponibles
    --------------------
    - proveedores() : Inicia el proceso de reabastecimiento
    - confirmar_recepcion_compra(productos, origen) : Recibe confirmación de compra
    
    Ejemplo de Uso
    --------------
    Para iniciar el servicio::
    
        python proveedores.py
    
    Para probar con curl::
    
        curl -X POST http://192.168.1.6:5005 \\
          -H "Content-Type: application/json" \\
          -d '{
            "jsonrpc": "2.0",
            "method": "proveedores",
            "params": {},
            "id": 1
          }'
    
    Para probar con Python requests::
    
        import requests
        
        payload = {
            "jsonrpc": "2.0",
            "method": "proveedores",
            "params": {},
            "id": 1
        }
        
        response = requests.post(
            "http://192.168.1.6:5005",
            json=payload
        )
        
        print(response.json())
    
    Notas
    -----
    - El servicio debe iniciarse antes que otros servicios intenten comunicarse
    - Asegúrate de que el middleware esté corriendo en 192.168.1.10:5010
    - Para detener el servicio usa Ctrl+C
    - Los mensajes de log se imprimen en stdout
    
    Warnings
    --------
    - Requiere que el puerto 5005 esté disponible
    - Debe tener conectividad de red con el middleware
    """
    from jsonrpcserver.server import RequestHandler
    
    print("="*60)
    print("Servicio de Proveedores corriendo en 192.168.1.6:5005")
    print("="*60)
    print("\nEndpoints:")
    print("  - proveedores() → Inicia reabastecimiento")
    print("  - confirmar_recepcion_compra(productos, origen)")
    print("="*60 + "\n")
    serve("192.168.1.6", 5005)