"""
Microservicio Middleware - Sistema Distribuido de Gestión de Muebles
=====================================================================

Este microservicio actúa como orquestador central del sistema distribuido,
coordinando las operaciones entre todos los microservicios. Gestiona dos flujos
principales: ventas a clientes y compras a proveedores (reabastecimiento).

Configuración del Servicio
--------------------------
- **Host:** 192.168.1.10
- **Puerto:** 5010
- **Protocolo:** JSON-RPC 2.0
- **Versión:** 1.0.0
- **Rol:** Orquestador/Coordinador del sistema

Dependencias
------------
Este servicio se comunica con:
    - Inventario (192.168.1.2:5001): Gestión de productos y stock
    - Tienda (192.168.1.3:5002): Interfaz de cliente y órdenes
    - ComprasVentas (192.168.1.4:5003): Registro de transacciones
    - Contabilidad (192.168.1.5:5004): Generación de facturas
    - Proveedores (192.168.1.6:5005): Gestión de reabastecimiento
    - Transporte (192.168.1.7:5006): Logística de envíos

Variables Globales
-----------------
origen : str
    Identificador del servicio middleware para trazabilidad.
    Valor: "MiddleWare"

URL_INVENTARIO : str
    URL del servicio de inventario.
    Valor: "http://192.168.1.2:5001"

URL_TIENDA : str
    URL del servicio de tienda.
    Valor: "http://192.168.1.3:5002"

URL_COMPRASVENTAS : str
    URL del servicio de compras y ventas.
    Valor: "http://192.168.1.4:5003"

URL_CONTABILIDAD : str
    URL del servicio de contabilidad.
    Valor: "http://192.168.1.5:5004"

URL_PROVEEDORES : str
    URL del servicio de proveedores.
    Valor: "http://192.168.1.6:5005"

URL_TRANSPORTE : str
    URL del servicio de transporte.
    Valor: "http://192.168.1.7:5006"

carrito_compras : dict
    Almacena temporalmente el carrito de compras durante el flujo de venta.
    Estructura: {"productos": [...]}

Flujos de Operación
-------------------

**Flujo de Ventas (middleWareController):**
    1. Cargar productos desde inventario
    2. Enviar productos a tienda para selección del cliente
    3. Registrar venta en ComprasVentas
    4. Validar stock disponible
    5. Generar factura en Contabilidad
    6. Actualizar inventario (restar stock)
    7. Solicitar transporte
    8. Enviar factura a tienda

**Flujo de Compras/Reabastecimiento (middlewareControllerProveedores):**
    1. Consultar productos con bajo stock (≤5 unidades)
    2. Registrar compra en ComprasVentas
    3. Generar factura de compra en Contabilidad
    4. Actualizar inventario (sumar stock)
    5. Confirmar recepción a Proveedores

Ejemplo de Uso
--------------
Para iniciar el servicio::

    python middleware.py

El servicio quedará escuchando peticiones JSON-RPC en 192.168.1.10:5010

Ejemplo de flujo de venta completo::

    import requests
    
    # Iniciar flujo de venta
    payload = {
        "jsonrpc": "2.0",
        "method": "middleWareController",
        "params": {},
        "id": 1
    }
    
    response = requests.post("http://192.168.1.10:5010", json=payload)

Ejemplo de flujo de reabastecimiento::

    import requests
    
    # Iniciar flujo de compra a proveedores
    payload = {
        "jsonrpc": "2.0",
        "method": "middlewareControllerProveedores",
        "params": {"origen": "proveedores"},
        "id": 1
    }
    
    response = requests.post("http://192.168.1.10:5010", json=payload)

Notas
-----
- Este servicio NO tiene interfaz de usuario directa
- Actúa como coordinador entre todos los microservicios
- Maneja la lógica de negocio transaccional
- Valida stock antes de completar ventas
- Gestiona automáticamente el reabastecimiento

See Also
--------
tienda : Interfaz de cliente y órdenes
inventario : Gestión de productos
contabilidad : Generación de facturas
comprasventas : Registro de transacciones
"""

import requests
import json
from jsonrpcserver import method, serve, Success

# Configuración de origen y URLs de servicios
origen = "MiddleWare"
URL_INVENTARIO = "http://192.168.1.2:5001"
URL_TIENDA = "http://192.168.1.3:5002"
URL_COMPRASVENTAS = "http://192.168.1.4:5003"
URL_CONTABILIDAD = "http://192.168.1.5:5004"
URL_PROVEEDORES = "http://192.168.1.6:5005"
URL_TRANSPORTE = "http://192.168.1.7:5006"

# Almacenamiento temporal del carrito
carrito_compras = {}


@method
def middleWareController():
    """
    Controlador principal del flujo de ventas a clientes.
    
    Este método orquesta el proceso completo de venta: desde la carga de productos,
    selección por el cliente, validación de stock, generación de factura, hasta
    la coordinación del transporte. Es el punto de entrada para iniciar una
    transacción de venta en el sistema.
    
    El flujo completo incluye:
        1. Cargar catálogo de productos desde inventario
        2. Enviar productos a tienda para selección interactiva
        3. Registrar la venta en el servicio de ComprasVentas
        4. Validar disponibilidad de stock
        5. Si hay stock: generar factura y actualizar inventario
        6. Si no hay stock: cancelar operación
        7. Solicitar servicio de transporte
        8. Enviar factura final a tienda
    
    Parameters
    ----------
    None
    
    Returns
    -------
    Success
        Objeto Success vacío indicando que el flujo se ejecutó correctamente.
        
        Estructura::
        
            {}
    
    Raises
    ------
    requests.exceptions.RequestException
        Si hay errores de comunicación con algún microservicio.
    
    requests.exceptions.Timeout
        Si algún servicio no responde en el tiempo establecido.
    
    Examples
    --------
    Solicitud JSON-RPC básica::
    
        {
            "jsonrpc": "2.0",
            "method": "middleWareController",
            "params": {},
            "id": 1
        }
    
    Respuesta exitosa::
    
        {
            "jsonrpc": "2.0",
            "result": {},
            "id": 1
        }
    
    Flujo de ejecución con salida por consola::
    
        >>> # Cliente invoca middleWareController
        >>> # Salida en consola del middleware:
        Solicitando productos a inventario
        ============================================================
        Productos recibidos
        ID: 1 - Nombre: Sofá Seccional - Categoría: Sala - Precio: 1200.0 - Stock 10
        ID: 2 - Nombre: Mesa de Comedor - Categoría: Comedor - Precio: 800.0 - Stock 15
        ============================================================
        Enviando productos a tienda .....
        INFORMACIÓN CARRITO
        ============================================================
        Carrito guardado: 2 productos
        ID: 1 - Nombre: Sofá Seccional - Categoría: Sala - Precio: 1200.0 - Stock 10
        ID: 2 - Nombre: Mesa de Comedor - Categoría: Comedor - Precio: 800.0 - Stock 15
        ============================================================
        Enviando a comprasVentas
        Mensaje comprasVentas: Venta registrada exitosamente
        
        ==================================================
        Validando stock antes de facturar...
        ==================================================
        Stock disponible para todos los productos
        
        ==================================================
        Generando factura de venta...
        ==================================================
        Factura generada exitosamente
        
        Restando stock en inventario...
        Stock actualizado correctamente
        
        ==================================================
        Obteniendo factura generada...
        ==================================================
        2025-10-30 -- 2000.0 -- 380.0 -- 0 -- 2380.0
        Factura recibida:
        Fecha: 2025-10-30
        Total: $2380.00
        
        Respuesta de transporte: {...}
        Respuesta de tienda: {...}
    
    Flujo con stock insuficiente::
    
        >>> # Cuando no hay stock suficiente:
        ==================================================
        Validando stock antes de facturar...
        ==================================================
        Stock insuficiente para completar la venta
           - Sofá Seccional: disponible 2, solicitado 5
        Operación cancelada: Stock insuficiente
    
    Notes
    -----
    - Este método coordina múltiples servicios de forma secuencial
    - Si la validación de stock falla, se cancela toda la operación
    - El carrito se almacena en la variable global `carrito_compras`
    - Los timeouts varían según el servicio (5-15 segundos)
    - La actualización de inventario resta stock (operación de venta)
    
    Warnings
    --------
    - Requiere que todos los servicios dependientes estén activos
    - Si un servicio falla, puede dejar la transacción en estado inconsistente
    - No implementa mecanismos de rollback o compensación
    - La ejecución puede ser lenta por múltiples llamadas síncronas
    
    See Also
    --------
    cargar_productos : Obtiene el catálogo de inventario
    enviar_productos_tienda : Envía productos a tienda para selección
    validar_stock_disponible : Verifica disponibilidad antes de vender
    pedir_genrar_factura : Genera factura y actualiza inventario
    middlewareControllerProveedores : Flujo de compras/reabastecimiento
    """
    productos = cargar_productos()
    enviar_productos_tienda(productos)
    enviar_compras_ventas()
    
    if validar_stock_disponible():
        pedir_genrar_factura()
        factura = pedir_recibir_factura()
        enviar_factura_tienda(factura)
    else:
        print("Operación cancelada: Stock insuficiente")
    
    return Success()


def cargar_productos():
    """
    Solicita el catálogo completo de productos al servicio de inventario.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Realiza una petición al servicio de inventario para obtener todos los
    productos disponibles en el sistema.
    
    Parameters
    ----------
    None
        Utiliza la constante global URL_INVENTARIO para la comunicación.
    
    Returns
    -------
    dict
        Respuesta completa del servicio de inventario con la estructura:
        
        {
            "jsonrpc": "2.0",
            "result": {
                "productos": [
                    {
                        "id": int,
                        "nombre": str,
                        "categoria": str,
                        "precio": float,
                        "stock": int
                    },
                    ...
                ]
            },
            "id": 1
        }
    
    Raises
    ------
    requests.exceptions.ConnectionError
        Si no se puede conectar con el servicio de inventario.
    
    requests.exceptions.Timeout
        Si el servicio no responde (timeout=None, espera indefinida).
    
    json.JSONDecodeError
        Si la respuesta no es JSON válido.
    
    Examples
    --------
    Uso interno::
    
        >>> productos = cargar_productos()
        Solicitando productos a inventario
        ============================================================
        Productos recibidos
        ID: 1 - Nombre: Sofá Seccional - Categoría: Sala - Precio: 1200.0 - Stock 10
        ID: 2 - Nombre: Mesa de Comedor - Categoría: Comedor - Precio: 800.0 - Stock 15
        ============================================================
    
    Estructura de retorno::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 10
                    },
                    {
                        "id": 2,
                        "nombre": "Mesa de Comedor",
                        "categoria": "Comedor",
                        "precio": 800.0,
                        "stock": 15
                    }
                ]
            },
            "id": 1
        }
    
    Payload enviado a inventario::
    
        {
            "jsonrpc": "2.0",
            "method": "cargar_productos",
            "params": {"origen": "MiddleWare"},
            "id": 1
        }
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Imprime el catálogo formateado en consola para debugging
    - Utiliza timeout=None (espera indefinida) en la petición
    - El parámetro 'origen' se utiliza para trazabilidad en el inventario
    - La respuesta completa se retorna sin procesamiento adicional
    
    Warnings
    --------
    - Sin timeout definido, puede bloquear indefinidamente
    - No maneja excepciones, deben capturarse en el llamador
    - Imprime información sensible en consola (precios, stock)
    
    See Also
    --------
    enviar_productos_tienda : Utiliza los productos cargados
    consultar_productos_bajo_stock : Variante para reabastecimiento
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": origen},
        "id": 1
    }
    print("Solicitando productos a inventario")
    response = requests.post(URL_INVENTARIO, json=payload, timeout=None)
    productos = response.json()
    print("="*60)
    print("Productos recibidos")
    for producto in productos["result"]["productos"]:
        print(f"ID: {producto['id']} - Nombre: {producto['nombre']} - Categoría: {producto['categoria']} - Precio: {producto['precio']} - Stock {producto['stock']}")
    print("="*60)
    return productos


def enviar_productos_tienda(productos):
    """
    Envía el catálogo de productos a la tienda para selección del cliente.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Invoca el método 'ordenar' del servicio de tienda, el cual presenta los
    productos al usuario y captura su orden de compra. El resultado (carrito)
    se almacena en la variable global `carrito_compras`.
    
    Parameters
    ----------
    productos : dict
        Respuesta completa del servicio de inventario conteniendo:
        
        {
            "jsonrpc": "2.0",
            "result": {
                "productos": [
                    {
                        "id": int,
                        "nombre": str,
                        "categoria": str,
                        "precio": float,
                        "stock": int
                    },
                    ...
                ]
            },
            "id": int
        }
    
    Returns
    -------
    None
        No retorna valor. Actualiza la variable global `carrito_compras` con:
        
        {
            "productos": [
                {
                    "id": int,
                    "nombre": str,
                    "categoria": str,
                    "precio": float,
                    "stock": int,
                    "comprar": int
                },
                ...
            ]
        }
    
    Raises
    ------
    requests.exceptions.RequestException
        Si hay error de comunicación con el servicio de tienda.
    
    requests.exceptions.Timeout
        Si la tienda no responde (timeout=None, espera indefinida).
    
    KeyError
        Si la estructura de respuesta no contiene las claves esperadas.
    
    Examples
    --------
    Uso interno::
    
        >>> productos = cargar_productos()
        >>> enviar_productos_tienda(productos)
        Enviando productos a tienda .....
        INFORMACIÓN CARRITO
        ============================================================
        Carrito guardado: 2 productos
        ID: 1 - Nombre: Sofá Seccional - Categoría: Sala - Precio: 1200.0 - Stock 10
        ID: 2 - Nombre: Mesa de Comedor - Categoría: Comedor - Precio: 800.0 - Stock 15
        ============================================================
    
    Payload enviado a tienda::
    
        {
            "jsonrpc": "2.0",
            "method": "ordenar",
            "params": {
                "origen": "MiddleWare",
                "productos": {
                    "productos": [
                        {"id": 1, "nombre": "Sofá", "categoria": "Sala", 
                         "precio": 1200.0, "stock": 10},
                        {"id": 2, "nombre": "Mesa", "categoria": "Comedor",
                         "precio": 800.0, "stock": 15}
                    ]
                }
            },
            "id": 1
        }
    
    Respuesta esperada de tienda::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 10,
                        "comprar": 2
                    },
                    {
                        "id": 2,
                        "nombre": "Mesa de Comedor",
                        "categoria": "Comedor",
                        "precio": 800.0,
                        "stock": 15,
                        "comprar": 1
                    }
                ]
            },
            "id": 1
        }
    
    Estado de carrito_compras después::
    
        {
            "productos": [
                {"id": 1, "nombre": "Sofá Seccional", ..., "comprar": 2},
                {"id": 2, "nombre": "Mesa de Comedor", ..., "comprar": 1}
            ]
        }
    
    Manejo de errores::
    
        >>> # Si hay error en la comunicación:
        Enviando productos a tienda .....
        Error en tienda: Connection refused
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Modifica la variable global `carrito_compras`
    - El servicio de tienda requiere interacción por consola del usuario
    - La ejecución se bloquea hasta que el usuario complete su orden
    - Utiliza timeout=None (espera indefinida)
    - Captura excepciones y las imprime sin propagarlas
    - Imprime información detallada del carrito para debugging
    
    Warnings
    --------
    - Función bloqueante que espera interacción del usuario en tienda
    - Sin timeout, puede esperar indefinidamente
    - No valida la estructura de la respuesta antes de acceder a las claves
    - Si falla, el carrito_compras puede quedar en estado inconsistente
    - Las excepciones se capturan pero no se propagan
    
    See Also
    --------
    cargar_productos : Obtiene los productos que se envían
    enviar_compras_ventas : Usa el carrito almacenado
    validar_stock_disponible : Valida el carrito antes de facturar
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "ordenar",
        "params": {
            "origen": origen,
            "productos": productos["result"]
        },
        "id": 1
    }
    print("Enviando productos a tienda .....")
    try:
        response = requests.post(URL_TIENDA, json=payload, timeout=None)
        message = response.json()
        carrito_compras["productos"] = message["result"]["productos"]
        print("INFORMACIÓN CARRITO")
        print("="*60)
        print(f"Carrito guardado: {len(carrito_compras['productos'])} productos")
        for i in carrito_compras["productos"]:
            print(f"ID: {i['id']} - Nombre: {i['nombre']} - Categoría: {i['categoria']} - Precio: {i['precio']} - Stock {i['stock']}")
        print("="*60)
    except Exception as e:
        print(f"Error en tienda: {e}")


def enviar_compras_ventas():
    """
    Registra la venta en el servicio de ComprasVentas.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Envía el carrito de compras al servicio de ComprasVentas para que se
    registre la transacción de venta en el sistema.
    
    Parameters
    ----------
    None
        Utiliza la variable global `carrito_compras` que contiene el carrito
        actualizado desde el servicio de tienda.
    
    Returns
    -------
    None
        No retorna valor. Imprime el mensaje de confirmación en consola.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si el servicio no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con ComprasVentas.
    
    KeyError
        Si la respuesta no contiene la estructura esperada.
    
    Examples
    --------
    Uso interno::
    
        >>> # Después de enviar_productos_tienda
        >>> enviar_compras_ventas()
        Enviando a comprasVentas
        Mensaje comprasVentas: Venta registrada exitosamente
    
    Payload enviado a ComprasVentas::
    
        {
            "jsonrpc": "2.0",
            "method": "registrar_venta",
            "params": {
                "origen": "MiddleWare",
                "carrito": {
                    "productos": [
                        {
                            "id": 1,
                            "nombre": "Sofá Seccional",
                            "categoria": "Sala",
                            "precio": 1200.0,
                            "stock": 10,
                            "comprar": 2
                        },
                        {
                            "id": 2,
                            "nombre": "Mesa de Comedor",
                            "categoria": "Comedor",
                            "precio": 800.0,
                            "stock": 15,
                            "comprar": 1
                        }
                    ]
                }
            },
            "id": 1
        }
    
    Respuesta esperada::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "Mensaje": "Venta registrada exitosamente",
                "id_venta": "VEN-20251030-001"
            },
            "id": 1
        }
    
    Ejemplo de error por timeout::
    
        >>> enviar_compras_ventas()
        Enviando a comprasVentas
        Traceback (most recent call last):
            ...
        requests.exceptions.Timeout: HTTPConnectionPool(host='192.168.1.4', port=5003): 
            Read timed out. (read timeout=5)
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - No maneja excepciones, deben capturarse en el llamador
    - Depende de que `carrito_compras` esté poblado previamente
    - Solo imprime el campo "Mensaje" de la respuesta
    - El registro en ComprasVentas es para auditoría y reportes
    
    Warnings
    --------
    - No valida que carrito_compras exista o tenga datos
    - Las excepciones se propagan sin manejo
    - Timeout corto (5s) puede causar fallos en redes lentas
    - No retorna el ID de venta generado
    
    See Also
    --------
    enviar_productos_tienda : Genera el carrito que se registra
    registrar_compra_comprasventas : Versión para compras a proveedores
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_venta",
        "params": {
            "origen": origen,
            "carrito": carrito_compras
        },
        "id": 1
    }
    print("Enviando a comprasVentas")
    response = requests.post(URL_COMPRASVENTAS, json=payload, timeout=5)
    respuestaComprasVentas = response.json()
    print(registrar_compra_comprasventas)
    #print(f"Mensaje comprasVentas: {respuestaComprasVentas['result']['Mensaje']}")


def validar_stock_disponible():
    """
    Valida que haya stock suficiente antes de procesar la venta.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Consulta al servicio de inventario para verificar que todos los productos
    en el carrito tengan stock disponible en las cantidades solicitadas.
    
    Parameters
    ----------
    None
        Utiliza la variable global `carrito_compras["productos"]` que contiene
        los productos con sus cantidades solicitadas.
    
    Returns
    -------
    bool
        True si hay stock suficiente para todos los productos.
        False si algún producto no tiene stock suficiente.
    
    Examples
    --------
    Caso exitoso (stock disponible)::
    
        >>> validar_stock_disponible()
        
        ==================================================
        Validando stock antes de facturar...
        ==================================================
        Stock disponible para todos los productos
        True
    
    Caso con stock insuficiente::
    
        >>> validar_stock_disponible()
        
        ==================================================
        Validando stock antes de facturar...
        ==================================================
        Stock insuficiente para completar la venta
           - Sofá Seccional: disponible 2, solicitado 5
           - Mesa de Comedor: disponible 1, solicitado 3
        False
    
    Payload enviado a inventario::
    
        {
            "jsonrpc": "2.0",
            "method": "validar_stock",
            "params": {
                "carrito": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 10,
                        "comprar": 2
                    },
                    {
                        "id": 2,
                        "nombre": "Mesa de Comedor",
                        "categoria": "Comedor",
                        "precio": 800.0,
                        "stock": 15,
                        "comprar": 1
                    }
                ]
            },
            "id": 1
        }
    
    Respuesta de inventario (stock disponible)::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "disponible": true,
                "mensaje": "Stock disponible para todos los productos"
            },
            "id": 1
        }
    
    Respuesta de inventario (stock insuficiente)::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "disponible": false,
                "mensaje": "Stock insuficiente para completar la venta",
                "productos_sin_stock": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "stock_actual": 2,
                        "cantidad_solicitada": 5
                    },
                    {
                        "id": 2,
                        "nombre": "Mesa de Comedor",
                        "stock_actual": 1,
                        "cantidad_solicitada": 3
                    }
                ]
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> # Si hay error de comunicación:
        ==================================================
        Validando stock antes de facturar...
        ==================================================
        Error validando stock: Connection refused
        False
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - Imprime separadores visuales y mensajes informativos en consola
    - Muestra detalles de productos sin stock cuando aplique
    - Captura excepciones y retorna False en caso de error
    - Si no se puede validar (error), asume que no hay stock disponible
    
    Warnings
    --------
    - En caso de error de comunicación, retorna False (seguro)
    - No distingue entre "sin stock" y "error de comunicación"
    - Timeout corto (5s) puede causar falsos negativos
    - Asume que la respuesta tiene la estructura esperada
    
    See Also
    --------
    pedir_genrar_factura : Solo se ejecuta si esta función retorna True
    notificar_inventario_modificacion : Actualiza el stock después de validar
    """
    carrito = carrito_compras["productos"]
    
    payload = {
        "jsonrpc": "2.0",
        "method": "validar_stock",
        "params": {"carrito": carrito},
        "id": 1
    }
    
    print(f"\n{'='*50}")
    print("Validando stock antes de facturar...")
    print(f"{'='*50}")
    
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        resultado = response.json()
        
        disponible = resultado.get('result', {}).get('disponible', False)
        mensaje = resultado.get('result', {}).get('mensaje', '')
        
        if disponible:
            print(f"{mensaje}")
            return True
        else:
            print(f"{mensaje}")
            productos_sin_stock = resultado.get('result', {}).get('productos_sin_stock', [])
            for p in productos_sin_stock:
                print(f"   - {p['nombre']}: disponible {p['stock_actual']}, solicitado {p['cantidad_solicitada']}")
            return False
            
    except Exception as e:
        print(f"Error validando stock: {e}")
        return False


def pedir_genrar_factura():
    """
    Genera la factura de venta y actualiza el inventario restando stock.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Coordina dos operaciones críticas: solicita al servicio de contabilidad que
    genere la factura de venta, y luego notifica al inventario para que reste
    el stock vendido.
    
    Parameters
    ----------
    None
        Utiliza la variable global `carrito_compras["productos"]` que contiene
        los productos vendidos con sus cantidades.
    
    Returns
    -------
    None
        No retorna valor. Imprime mensajes de estado en consola.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Contabilidad no responde en 15 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Contabilidad o Inventario.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> pedir_genrar_factura()
        
        ==================================================
        Generando factura de venta...
        ==================================================
        Factura generada exitosamente
        
        Restando stock en inventario...
        Stock actualizado correctamente
    
    Payload enviado a Contabilidad::
    
        {
            "jsonrpc": "2.0",
            "method": "generar_factura",
            "params": {
                "origen": "MiddleWare",
                "carrito": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 10,
                        "comprar": 2
                    },
                    {
                        "id": 2,
                        "nombre": "Mesa de Comedor",
                        "categoria": "Comedor",
                        "precio": 800.0,
                        "stock": 15,
                        "comprar": 1
                    }
                ]
            },
            "id": 1
        }
    
    Respuesta esperada de Contabilidad::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Factura generada exitosamente",
                "id_factura": "FAC-20251030-001",
                "total": 2380.0
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> pedir_genrar_factura()
        
        ==================================================
        Generando factura de venta...
        ==================================================
        Error generando factura: Connection timeout
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 15 segundos para Contabilidad
    - Invoca `notificar_inventario_modificacion` con tipo_operacion="venta"
    - La operación "venta" indica que se debe RESTAR stock
    - Imprime separadores y mensajes para seguimiento del flujo
    - Captura excepciones y las imprime sin propagarlas
    
    Warnings
    --------
    - No valida que el carrito tenga productos antes de facturar
    - Si falla la generación de factura, NO actualiza el inventario
    - Si falla la actualización de inventario después de facturar,
      puede quedar inconsistencia (factura sin descuento de stock)
    - Las excepciones se capturan pero no se propagan
    
    See Also
    --------
    validar_stock_disponible : Debe ejecutarse antes de esta función
    notificar_inventario_modificacion : Actualiza el stock en inventario
    pedir_recibir_factura : Obtiene la factura generada
    generar_factura_compra : Versión para compras a proveedores
    """
    carrito = carrito_compras["productos"]
    
    print(f"\n{'='*50}")
    print("Generando factura de venta...")
    print(f"{'='*50}")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
            "origen": origen,
            "carrito": carrito
        },
        "id": 1
    }
    
    try:
        response = requests.post(URL_CONTABILIDAD, json=payload, timeout=15)
        resultado = response.json()
        print(f"{resultado.get('result', {}).get('mensaje', 'Factura generada')}")
        
        # Actualizar inventario (RESTA stock porque es venta)
        notificar_inventario_modificacion(carrito, tipo_operacion="venta")
        
    except Exception as e:
        print(f"Error generando factura: {e}")


def notificar_inventario_modificacion(carrito, tipo_operacion="venta"):
    """
    Actualiza el stock en el servicio de inventario.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Notifica al inventario para que actualice el stock de los productos según
    el tipo de operación: resta stock en ventas o suma stock en compras.
    
    Parameters
    ----------
    carrito : list of dict
        Lista de productos con sus cantidades a actualizar:
        
        [
            {
                "id": int,
                "nombre": str,
                "categoria": str,
                "precio": float,
                "stock": int,
                "comprar": int
            },
            ...
        ]
    
    tipo_operacion : str, optional
        Tipo de operación a realizar en el inventario.
        
        - "venta": Resta el stock (campo 'comprar' se resta del stock actual)
        - "compra": Suma el stock (campo 'comprar' se suma al stock actual)
        
        Default: "venta"
    
    Returns
    -------
    dict or None
        Respuesta del servicio de inventario si la operación es exitosa:
        
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Stock actualizado correctamente",
                "productos_actualizados": int
            },
            "id": 1
        }
        
        None si hay error en la comunicación.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Inventario no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Inventario.
    
    Examples
    --------
    Actualización por venta (resta stock)::
    
        >>> carrito = [
        ...     {"id": 1, "nombre": "Sofá", "comprar": 2},
        ...     {"id": 2, "nombre": "Mesa", "comprar": 1}
        ... ]
        >>> resultado = notificar_inventario_modificacion(carrito, "venta")
        
        Restando stock en inventario...
        Stock actualizado correctamente
    
    Actualización por compra (suma stock)::
    
        >>> carrito = [
        ...     {"id": 1, "nombre": "Sofá", "comprar": 10},
        ...     {"id": 2, "nombre": "Mesa", "comprar": 15}
        ... ]
        >>> resultado = notificar_inventario_modificacion(carrito, "compra")
        
        Sumando stock en inventario...
        Stock actualizado correctamente
    
    Payload enviado a Inventario::
    
        {
            "jsonrpc": "2.0",
            "method": "actualizar_inventario",
            "params": {
                "carrito": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 10,
                        "comprar": 2
                    }
                ],
                "tipo_operacion": "venta"
            },
            "id": 1
        }
    
    Respuesta esperada de Inventario::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Stock actualizado correctamente",
                "productos_actualizados": 2
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> notificar_inventario_modificacion(carrito, "venta")
        
        Restando stock en inventario...
        Error actualizando inventario: Connection refused
        None
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - El mensaje en consola cambia según tipo_operacion:
      * "venta" → "Restando stock en inventario..."
      * "compra" → "Sumando stock en inventario..."
    - Captura excepciones y retorna None sin propagarlas
    - El inventario es responsable de validar y aplicar la operación
    
    Warnings
    --------
    - No valida la estructura del carrito antes de enviar
    - No verifica que tipo_operacion sea válido
    - Las excepciones se capturan sin propagarse
    - Si falla, el sistema puede quedar inconsistente
    
    See Also
    --------
    pedir_genrar_factura : Usa esta función con tipo_operacion="venta"
    generar_factura_compra : Usa esta función con tipo_operacion="compra"
    validar_stock_disponible : Valida antes de permitir la actualización
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "actualizar_inventario",
        "params": {
            "carrito": carrito,
            "tipo_operacion": tipo_operacion
        },
        "id": 1
    }
    
    accion = "Restando" if tipo_operacion == "venta" else "Sumando"
    print(f"\n{accion} stock en inventario...")
    
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        data = response.json()
        mensaje = data.get('result', {}).get('mensaje', 'OK')
        print(f"{mensaje}")
        return data
    except Exception as e:
        print(f"Error actualizando inventario: {e}")
        return None


def pedir_recibir_factura():
    """
    Obtiene la última factura generada desde el servicio de contabilidad.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Solicita al servicio de contabilidad que devuelva la factura más reciente
    generada en el sistema, típicamente después de completar una venta.
    
    Parameters
    ----------
    None
        Utiliza la constante global URL_CONTABILIDAD y 'origen' para la petición.
    
    Returns
    -------
    dict or None
        Respuesta completa del servicio de contabilidad si es exitosa:
        
        {
            "jsonrpc": "2.0",
            "result": {
                "factura": [
                    {
                        "id_factura": str,
                        "fecha": str,
                        "productos": list,
                        "subtotal": float,
                        "iva": float,
                        "impuesto_extra": float,
                        "total": float,
                        "cliente": dict
                    }
                ]
            },
            "id": 1
        }
        
        None si hay error en la comunicación o no hay factura.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Contabilidad no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Contabilidad.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> factura = pedir_recibir_factura()
        
        ==================================================
        Obteniendo factura generada...
        ==================================================
        2025-10-30 -- 2000.0 -- 380.0 -- 0 -- 2380.0
        Factura recibida:
        Fecha: 2025-10-30
        Total: $2380.00
    
    Payload enviado a Contabilidad::
    
        {
            "jsonrpc": "2.0",
            "method": "recibir_factura",
            "params": {"origen": "MiddleWare"},
            "id": 1
        }
    
    Respuesta esperada de Contabilidad::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "factura": [
                    {
                        "id_factura": "FAC-20251030-001",
                        "fecha": "2025-10-30",
                        "productos": [
                            {
                                "id": 1,
                                "nombre": "Sofá Seccional",
                                "cantidad": 2,
                                "precio_unitario": 1200.0,
                                "subtotal": 2400.0
                            }
                        ],
                        "subtotal": 2000.0,
                        "iva": 380.0,
                        "impuesto_extra": 0,
                        "total": 2380.0,
                        "cliente": {...}
                    }
                ]
            },
            "id": 1
        }
    
    Caso sin factura disponible::
    
        >>> factura = pedir_recibir_factura()
        
        ==================================================
        Obteniendo factura generada...
        ==================================================
        Factura recibida:
        Fecha: None
        Total: $0.00
        None
    
    Manejo de errores::
    
        >>> factura = pedir_recibir_factura()
        
        ==================================================
        Obteniendo factura generada...
        ==================================================
        Error obteniendo factura: Timeout exceeded
        None
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - Imprime separadores visuales para seguimiento
    - Si hay factura, imprime un resumen de cada item (fecha, valores)
    - Captura excepciones y retorna None sin propagarlas
    - Asume que la factura es una lista con al menos un elemento
    
    Warnings
    --------
    - No valida la estructura de la respuesta antes de acceder
    - Asume que 'factura' es una lista, no un objeto directo
    - Las excepciones se capturan sin propagarse
    - Puede retornar None por múltiples razones (error o sin factura)
    
    See Also
    --------
    pedir_genrar_factura : Genera la factura que luego se obtiene
    enviar_factura_tienda : Usa la factura obtenida para enviarla
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "recibir_factura",
        "params": {"origen": origen},
        "id": 1
    }
    
    print(f"\n{'='*50}")
    print("Obteniendo factura generada...")
    print(f"{'='*50}")
    
    try:
        response = requests.post(URL_CONTABILIDAD, json=payload, timeout=5)
        resultado = response.json()
        
        factura = resultado.get('result', {}).get('factura', None)
        
        if factura:
            print(factura)
            print(f"Fecha: {factura['fecha']}")
            print(f"Origen: {factura['origen']}")
            print(f"Subtotal: {factura['subtotal']}")
            print(f"IVA: {factura['iva']}")
            print(f"Impuesto Extra: {factura['impuesto_extra']}")
            print(f"Total: {factura['total']}")
                    
            print(f"Factura recibida:")
           
        
        return resultado
        
    except Exception as e:
        print(f"Error obteniendo factura: {e}")
        return None


def enviar_factura_tienda(factura):
    """
    Envía la factura final a la tienda junto con información de transporte.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Coordina el envío de la factura al cliente a través del servicio de tienda,
    incluyendo información sobre el servicio de transporte/logística.
    
    Parameters
    ----------
    factura : dict
        Respuesta completa de contabilidad conteniendo la factura:
        
        {
            "jsonrpc": "2.0",
            "result": {
                "factura": [
                    {
                        "id_factura": str,
                        "fecha": str,
                        "productos": list,
                        "subtotal": float,
                        "iva": float,
                        "impuesto_extra": float,
                        "total": float
                    }
                ]
            },
            "id": int
        }
    
    Returns
    -------
    None
        No retorna valor. Imprime la respuesta del servicio de tienda en consola.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Tienda no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Tienda o Transporte.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> factura_data = {
        ...     "jsonrpc": "2.0",
        ...     "result": {
        ...         "factura": [{
        ...             "id_factura": "FAC-001",
        ...             "fecha": "2025-10-30",
        ...             "total": 2380.0
        ...         }]
        ...     }
        ... }
        >>> enviar_factura_tienda(factura_data)
        Respuesta de transporte: {'result': {'mensaje': 'Transporte asignado'}}
        Respuesta de tienda: {'result': {'mensaje': 'factura esta aqui'}}
    
    Payload enviado a Tienda::
    
        {
            "jsonrpc": "2.0",
            "method": "leer_factura",
            "params": {
                "factura": {
                    "jsonrpc": "2.0",
                    "result": {
                        "factura": [...]
                    },
                    "id": 1
                },
                "origen": "MiddleWare",
                "transporte": {
                    "jsonrpc": "2.0",
                    "result": {
                        "servicio": "Envío Express",
                        "tiempo_estimado": "2 días hábiles"
                    },
                    "id": 1
                }
            },
            "id": 1
        }
    
    Respuesta esperada de Tienda::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "factura esta aqui"
            },
            "id": 1
        }
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - Invoca `pedir_transporte()` para obtener información de logística
    - Imprime la respuesta completa de tienda en consola
    - No maneja excepciones, deben capturarse en el llamador
    
    Warnings
    --------
    - Las excepciones se propagan sin manejo
    - No valida la estructura de la factura antes de enviar
    - Si falla pedir_transporte(), puede enviar transporte=None
    
    See Also
    --------
    pedir_recibir_factura : Obtiene la factura que se envía
    pedir_transporte : Obtiene información de transporte
    """
    transporte = pedir_transporte(factura)
    payload = {
        "jsonrpc": "2.0",
        "method": "leer_factura",
        "params": {
                    "factura": factura,
                    "origen": origen,
                    "transporte": transporte
                   },
        "id": 1
    }

    response = requests.post(URL_TIENDA, json=payload, timeout=5)
    print(f"Respuesta de tienda: {response.json()}")
    

def pedir_transporte(factura):
    """
    Solicita servicio de transporte/logística para la entrega.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Envía la factura al servicio de transporte para coordinar la logística
    de entrega de los productos vendidos.
    
    Parameters
    ----------
    factura : dict
        Respuesta completa de contabilidad conteniendo la factura con detalles
        de productos, dirección de entrega, etc.
    
    Returns
    -------
    dict
        Respuesta completa del servicio de transporte:
        
        {
            "jsonrpc": "2.0",
            "result": {
                "servicio": str,
                "tiempo_estimado": str,
                "costo": float,
                "tracking_id": str
            },
            "id": 1
        }
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Transporte no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Transporte.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> factura = {...}
        >>> transporte = pedir_transporte(factura)
        Respuesta de transporte: {
            'jsonrpc': '2.0',
            'result': {
                'servicio': 'Envío Express',
                'tiempo_estimado': '2 días hábiles',
                'costo': 50.0,
                'tracking_id': 'TRK-20251030-001'
            },
            'id': 1
        }
    
    Payload enviado a Transporte::
    
        {
            "jsonrpc": "2.0",
            "method": "ordenar_transporte",
            "params": {
                "factura": {
                    "jsonrpc": "2.0",
                    "result": {
                        "factura": [...]
                    },
                    "id": 1
                },
                "origen": "MiddleWare"
            },
            "id": 1
        }
    
    Respuesta esperada de Transporte::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "servicio": "Envío Express",
                "tiempo_estimado": "2 días hábiles",
                "costo": 50.0,
                "tracking_id": "TRK-20251030-001",
                "mensaje": "Transporte asignado exitosamente"
            },
            "id": 1
        }
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - Imprime la respuesta completa del transporte en consola
    - No maneja excepciones, deben capturarse en el llamador
    - La respuesta se incluye luego en el envío a tienda
    
    Warnings
    --------
    - Las excepciones se propagan sin manejo
    - No valida la estructura de la factura antes de enviar
    
    See Also
    --------
    enviar_factura_tienda : Usa el transporte obtenido
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "ordenar_transporte",
        "params": {
                    "factura": factura,
                    "origen": origen,
                   },
        "id": 1
    }
    response = requests.post(URL_TRANSPORTE, json=payload, timeout=5)
    print(f"Respuesta de transporte: {response.json()}")
    return response.json()


# ============================================================================
# SECCIÓN: GESTIÓN DE COMPRAS A PROVEEDORES (REABASTECIMIENTO)
# ============================================================================


@method
def middlewareControllerProveedores(origen="proveedores"):
    """
    Controlador principal del flujo de compras a proveedores (reabastecimiento).
    
    Este método orquesta el proceso completo de reabastecimiento automático:
    identifica productos con bajo stock, registra la compra, genera factura,
    actualiza el inventario sumando stock y confirma a proveedores.
    
    El flujo completo incluye:
        1. Consultar productos con stock ≤ 5 unidades
        2. Si no hay productos: terminar sin acciones
        3. Si hay productos: registrar compra en ComprasVentas
        4. Generar factura de compra en Contabilidad
        5. Actualizar inventario sumando stock (llevar a 20 unidades)
        6. Confirmar recepción a Proveedores
    
    Parameters
    ----------
    origen : str, optional
        Identificador del servicio que inicia el proceso.
        Default: "proveedores"
    
    Returns
    -------
    Success
        Objeto Success con el resultado del proceso:
        
        Si no hay productos con bajo stock::
        
            {
                "mensaje": "No se requiere reabastecimiento",
                "productos_comprados": []
            }
        
        Si se completó el reabastecimiento::
        
            {
                "mensaje": "Reabastecimiento completado exitosamente",
                "productos_comprados": [
                    {
                        "id": int,
                        "nombre": str,
                        "categoria": str,
                        "precio": float,
                        "stock": int,
                        "comprar": int
                    },
                    ...
                ]
            }
    
    Examples
    --------
    Solicitud JSON-RPC básica::
    
        {
            "jsonrpc": "2.0",
            "method": "middlewareControllerProveedores",
            "params": {},
            "id": 1
        }
    
    Solicitud con origen personalizado::
    
        {
            "jsonrpc": "2.0",
            "method": "middlewareControllerProveedores",
            "params": {"origen": "sistema_automatico"},
            "id": 1
        }
    
    Respuesta sin productos para reabastecer::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "No se requiere reabastecimiento",
                "productos_comprados": []
            },
            "id": 1
        }
    
    Respuesta con reabastecimiento exitoso::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Reabastecimiento completado exitosamente",
                "productos_comprados": [
                    {
                        "id": 3,
                        "nombre": "Silla Ergonómica",
                        "categoria": "Oficina",
                        "precio": 150.0,
                        "stock": 3,
                        "comprar": 17
                    },
                    {
                        "id": 7,
                        "nombre": "Lámpara de Escritorio",
                        "categoria": "Iluminación",
                        "precio": 45.0,
                        "stock": 5,
                        "comprar": 15
                    }
                ]
            },
            "id": 1
        }
    
    Salida por consola (caso exitoso)::
    
        ============================================================
        MIDDLEWARE: Iniciando proceso de reabastecimiento
        ============================================================
        
        Consultando productos con bajo stock...
        
        Productos con stock ≤ 5:
        ------------------------------------------------------------
        Silla Ergonómica
        Stock actual: 3 → Comprar: 17
        Lámpara de Escritorio
        Stock actual: 5 → Comprar: 15
        
        2 productos necesitan reabastecimiento
        
        Registrando compra en ComprasVentas...
        Compra registrada exitosamente
        
        Generando factura de compra...
        Factura de compra generada
        
        Sumando stock en inventario...
        Stock actualizado: +32 unidades en 2 productos
        
        Confirmando recepción a Proveedores...
        Proveedores confirmado
    
    Salida por consola (sin reabastecimiento)::
    
        ============================================================
        MIDDLEWARE: Iniciando proceso de reabastecimiento
        ============================================================
        
        Consultando productos con bajo stock...
        
        Productos con stock ≤ 5:
        ------------------------------------------------------------
        
        0 productos necesitan reabastecimiento
        No hay productos con bajo stock
    
    Notes
    -----
    - Este es un método JSON-RPC expuesto públicamente
    - El umbral de bajo stock es ≤ 5 unidades
    - Los productos se reabastecen hasta 20 unidades
    - Cantidad a comprar = 20 - stock_actual
    - La operación es transaccional (todo o nada conceptualmente)
    - Imprime separadores visuales para seguimiento del flujo
    - Si no hay productos, retorna exitosamente sin acciones
    
    Warnings
    --------
    - No implementa rollback si algún paso falla
    - Los errores en servicios individuales se manejan localmente
    - Puede dejar el sistema inconsistente si falla parcialmente
    - No valida que los servicios dependientes estén disponibles
    
    See Also
    --------
    consultar_productos_bajo_stock : Identifica productos a reabastecer
    registrar_compra_comprasventas : Registra la transacción de compra
    generar_factura_compra : Genera factura de compra a proveedor
    notificar_inventario_modificacion : Suma stock al inventario
    confirmar_a_proveedores : Notifica a proveedores
    middleWareController : Flujo de ventas a clientes
    """
    print("\n" + "="*60)
    print("MIDDLEWARE: Iniciando proceso de reabastecimiento")
    print("="*60)
    
    # 1. Consultar productos con bajo stock
    productos_bajo_stock = consultar_productos_bajo_stock()
    
    if not productos_bajo_stock:
        print("No hay productos con bajo stock")
        return Success({
            "mensaje": "No se requiere reabastecimiento",
            "productos_comprados": []
        })
    
    # 2. Registrar compra en ComprasVentas
    registrar_compra_comprasventas(productos_bajo_stock)
    
    # 3. Generar factura (origen="proveedores" para que sea compra)
    generar_factura_compra(productos_bajo_stock)
    
    # 4. Actualizar inventario (SUMA stock)
    notificar_inventario_modificacion(productos_bajo_stock, tipo_operacion="compra")
    
    # 5. Confirmar a Proveedores
    confirmar_a_proveedores(productos_bajo_stock)
    
    return Success({
        "mensaje": "Reabastecimiento completado exitosamente",
        "productos_comprados": productos_bajo_stock
    })


def consultar_productos_bajo_stock():
    """
    Consulta el inventario y filtra productos con stock bajo (≤ 5 unidades).
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Obtiene todos los productos del inventario, identifica cuáles tienen stock
    igual o menor a 5 unidades, y calcula la cantidad necesaria para llevarlos
    a 20 unidades.
    
    Parameters
    ----------
    None
        Utiliza la constante global URL_INVENTARIO para la comunicación.
    
    Returns
    -------
    list of dict
        Lista de productos que necesitan reabastecimiento:
        
        [
            {
                "id": int,
                "nombre": str,
                "categoria": str,
                "precio": float,
                "stock": int,              # Stock actual (≤ 5)
                "comprar": int             # Cantidad a comprar (20 - stock)
            },
            ...
        ]
        
        Lista vacía [] si no hay productos con bajo stock.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Inventario no responde en 10 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Inventario.
    
    Examples
    --------
    Caso con productos de bajo stock::
    
        >>> productos = consultar_productos_bajo_stock()
        
        Consultando productos con bajo stock...
        
        Productos con stock ≤ 5:
        ------------------------------------------------------------
        Silla Ergonómica
        Stock actual: 3 → Comprar: 17
        Lámpara de Escritorio
        Stock actual: 5 → Comprar: 15
        Mesa Auxiliar
        Stock actual: 2 → Comprar: 18
        
        3 productos necesitan reabastecimiento
        
        >>> print(productos)
        [
            {
                'id': 3,
                'nombre': 'Silla Ergonómica',
                'categoria': 'Oficina',
                'precio': 150.0,
                'stock': 3,
                'comprar': 17
            },
            {
                'id': 7,
                'nombre': 'Lámpara de Escritorio',
                'categoria': 'Iluminación',
                'precio': 45.0,
                'stock': 5,
                'comprar': 15
            },
            {
                'id': 12,
                'nombre': 'Mesa Auxiliar',
                'categoria': 'Sala',
                'precio': 200.0,
                'stock': 2,
                'comprar': 18
            }
        ]
    
    Caso sin productos de bajo stock::
    
        >>> productos = consultar_productos_bajo_stock()
        
        Consultando productos con bajo stock...
        
        Productos con stock ≤ 5:
        ------------------------------------------------------------
        
        0 productos necesitan reabastecimiento
        
        >>> print(productos)
        []
    
    Payload enviado a Inventario::
    
        {
            "jsonrpc": "2.0",
            "method": "cargar_productos",
            "params": {"origen": "proveedores"},
            "id": 1
        }
    
    Respuesta esperada de Inventario::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 10
                    },
                    {
                        "id": 3,
                        "nombre": "Silla Ergonómica",
                        "categoria": "Oficina",
                        "precio": 150.0,
                        "stock": 3
                    },
                    ...
                ]
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> productos = consultar_productos_bajo_stock()
        
        Consultando productos con bajo stock...
        Error consultando inventario: Connection timeout
        
        >>> print(productos)
        []
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 10 segundos
    - Umbral de bajo stock: stock ≤ 5 unidades
    - Objetivo de reabastecimiento: 20 unidades
    - Fórmula: comprar = 20 - stock_actual
    - Imprime información detallada para cada producto encontrado
    - Captura excepciones y retorna lista vacía en caso de error
    
    Warnings
    --------
    - En caso de error, retorna [] sin distinguir del caso sin productos
    - No valida que la respuesta tenga la estructura esperada
    - Asume que todos los productos tienen campo 'stock' numérico
    
    See Also
    --------
    middlewareControllerProveedores : Usa esta función para iniciar el flujo
    cargar_productos : Función similar para el flujo de ventas
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "proveedores"},
        "id": 1
    }
    
    print("\nConsultando productos con bajo stock...")
    
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=10)
        data = response.json()
        
        productos_bajo_stock = []
        
        print("\nProductos con stock ≤ 5:")
        print("-"*60)
        
        for producto in data["result"]["productos"]:
            if producto["stock"] <= 5:
                # Calcular cantidad a comprar (llevar a 20 unidades)
                cantidad_a_comprar = 20 - producto['stock']
                
                print(f"{producto['nombre']}")
                print(f"Stock actual: {producto['stock']} → Comprar: {cantidad_a_comprar}")
                
                productos_bajo_stock.append({
                    "id": producto["id"],
                    "nombre": producto["nombre"],
                    "categoria": producto["categoria"],
                    "precio": producto["precio"],
                    "stock": producto["stock"],
                    "comprar": cantidad_a_comprar
                })
        
        print(f"\n{len(productos_bajo_stock)} productos necesitan reabastecimiento")
        return productos_bajo_stock
        
    except Exception as e:
        print(f"Error consultando inventario: {e}")
        return []


def registrar_compra_comprasventas(productos):
    """
    Registra la compra a proveedores en el servicio de ComprasVentas.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Envía los productos que se están comprando al servicio de ComprasVentas
    para que quede registrada la transacción en el historial del sistema.
    
    Parameters
    ----------
    productos : list of dict
        Lista de productos a comprar con la estructura:
        
        [
            {
                "id": int,
                "nombre": str,
                "categoria": str,
                "precio": float,
                "stock": int,
                "comprar": int
            },
            ...
        ]
    
    Returns
    -------
    None
        No retorna valor. Imprime el mensaje de confirmación en consola.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si ComprasVentas no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con ComprasVentas.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> productos = [
        ...     {"id": 3, "nombre": "Silla", "comprar": 17},
        ...     {"id": 7, "nombre": "Lámpara", "comprar": 15}
        ... ]
        >>> registrar_compra_comprasventas(productos)
        
        Registrando compra en ComprasVentas...
        Compra a proveedores registrada exitosamente
    
    Payload enviado a ComprasVentas::
    
        {
            "jsonrpc": "2.0",
            "method": "registrar_compra",
            "params": {
                "productos": [
                    {
                        "id": 3,
                        "nombre": "Silla Ergonómica",
                        "categoria": "Oficina",
                        "precio": 150.0,
                        "stock": 3,
                        "comprar": 17
                    }
                ],
                "origen": "proveedores"
            },
            "id": 1
        }
    
    Respuesta esperada de ComprasVentas::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Compra a proveedores registrada exitosamente",
                "id_compra": "COM-20251030-001",
                "total": 2550.0
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> registrar_compra_comprasventas(productos)
        
        Registrando compra en ComprasVentas...
        Error registrando en ComprasVentas: Connection refused
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - El origen se establece como "proveedores" para distinguir de ventas
    - Captura excepciones y las imprime sin propagarlas
    - Solo imprime el campo "mensaje" de la respuesta
    
    Warnings
    --------
    - No valida la estructura de productos antes de enviar
    - Las excepciones se capturan sin propagarse
    - No retorna indicación de éxito/fallo al llamador
    
    See Also
    --------
    enviar_compras_ventas : Versión para registro de ventas
    middlewareControllerProveedores : Usa esta función en el flujo
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_compra",
        "params": {
            "productos": productos,
            "origen": "proveedores"
        },
        "id": 1
    }
    
    print("\nRegistrando compra en ComprasVentas...")
    
    try:
        response = requests.post(URL_COMPRASVENTAS, json=payload, timeout=5)
        data = response.json()
        print(f"{data.get('result', {}).get('mensaje', 'Compra registrada')}")
    except Exception as e:
        print(f"Error registrando en ComprasVentas: {e}")


def generar_factura_compra(productos):
    """
    Genera la factura de compra a proveedores en el servicio de Contabilidad.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Solicita al servicio de contabilidad que genere una factura de compra
    (distinta a factura de venta) para documentar la adquisición de productos
    a proveedores.
    
    Parameters
    ----------
    productos : list of dict
        Lista de productos comprados con la estructura:
        
        [
            {
                "id": int,
                "nombre": str,
                "categoria": str,
                "precio": float,
                "stock": int,
                "comprar": int
            },
            ...
        ]
    
    Returns
    -------
    None
        No retorna valor. Imprime el mensaje de confirmación en consola.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Contabilidad no responde en 15 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Contabilidad.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> productos = [
        ...     {"id": 3, "nombre": "Silla", "precio": 150.0, "comprar": 17},
        ...     {"id": 7, "nombre": "Lámpara", "precio": 45.0, "comprar": 15}
        ... ]
        >>> generar_factura_compra(productos)
        
        Generando factura de compra...
        Factura de compra generada exitosamente
    
    Payload enviado a Contabilidad::
    
        {
            "jsonrpc": "2.0",
            "method": "generar_factura",
            "params": {
                "carrito": [
                    {
                        "id": 3,
                        "nombre": "Silla Ergonómica",
                        "categoria": "Oficina",
                        "precio": 150.0,
                        "stock": 3,
                        "comprar": 17
                    },
                    {
                        "id": 7,
                        "nombre": "Lámpara de Escritorio",
                        "categoria": "Iluminación",
                        "precio": 45.0,
                        "stock": 5,
                        "comprar": 15
                    }
                ],
                "origen": "proveedores"
            },
            "id": 1
        }
    
    Respuesta esperada de Contabilidad::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Factura de compra generada exitosamente",
                "id_factura": "FACC-20251030-001",
                "subtotal": 3225.0,
                "iva": 612.75,
                "total": 3837.75
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> generar_factura_compra(productos)
        
        Generando factura de compra...
        Error generando factura: Timeout exceeded
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 15 segundos (procesamiento puede ser lento)
    - El origen "proveedores" indica al servicio que es factura de COMPRA
    - El servicio de Contabilidad diferencia facturas según el origen
    - Captura excepciones y las imprime sin propagarlas
    
    Warnings
    --------
    - No valida la estructura de productos antes de enviar
    - Las excepciones se capturan sin propagarse
    - No retorna la factura generada (solo imprime confirmación)
    
    See Also
    --------
    pedir_genrar_factura : Versión para facturas de venta
    middlewareControllerProveedores : Usa esta función en el flujo
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
            "carrito": productos,
            "origen": "proveedores"  
        },
        "id": 1
    }
    
    print("\nGenerando factura de compra...")
    
    try:
        response = requests.post(URL_CONTABILIDAD, json=payload, timeout=15)
        resultado = response.json()
        print(f"{resultado.get('result', {}).get('mensaje', 'Factura generada')}")
    except Exception as e:
        print(f"Error generando factura: {e}")


def confirmar_a_proveedores(productos):
    """
    Confirma al servicio de Proveedores que la compra fue procesada exitosamente.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Notifica al servicio de proveedores que los productos fueron recibidos,
    facturados y agregados al inventario, cerrando el ciclo de reabastecimiento.
    
    Parameters
    ----------
    productos : list of dict
        Lista de productos comprados con la estructura:
        
        [
            {
                "id": int,
                "nombre": str,
                "categoria": str,
                "precio": float,
                "stock": int,
                "comprar": int
            },
            ...
        ]
    
    Returns
    -------
    None
        No retorna valor. Imprime mensaje de confirmación en consola.
    
    Raises
    ------
    requests.exceptions.Timeout
        Si Proveedores no responde en 5 segundos.
    
    requests.exceptions.RequestException
        Si hay error de comunicación con Proveedores.
    
    Examples
    --------
    Ejecución exitosa::
    
        >>> productos = [
        ...     {"id": 3, "nombre": "Silla", "comprar": 17},
        ...     {"id": 7, "nombre": "Lámpara", "comprar": 15}
        ... ]
        >>> confirmar_a_proveedores(productos)
        
        Confirmando recepción a Proveedores...
        Proveedores confirmado
    
    Payload enviado a Proveedores::
    
        {
            "jsonrpc": "2.0",
            "method": "confirmar_recepcion_compra",
            "params": {
                "productos": [
                    {
                        "id": 3,
                        "nombre": "Silla Ergonómica",
                        "categoria": "Oficina",
                        "precio": 150.0,
                        "stock": 3,
                        "comprar": 17
                    }
                ],
                "origen": "middleware"
            },
            "id": 1
        }
    
    Respuesta esperada de Proveedores::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Recepción confirmada",
                "orden_proveedor": "OC-20251030-001"
            },
            "id": 1
        }
    
    Manejo de errores::
    
        >>> confirmar_a_proveedores(productos)
        
        Confirmando recepción a Proveedores...
        No se pudo confirmar a Proveedores: Connection refused
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC expuesto
    - Utiliza timeout de 5 segundos
    - El origen se establece como "middleware" para identificación
    - Captura excepciones y las imprime sin propagarlas
    - Esta confirmación cierra el ciclo de reabastecimiento
    
    Warnings
    --------
    - No valida la estructura de productos antes de enviar
    - Las excepciones se capturan sin propagarse
    - Si falla, no afecta el inventario ya actualizado
    - No retorna indicación de éxito/fallo
    
    See Also
    --------
    middlewareControllerProveedores : Usa esta función como paso final
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "confirmar_recepcion_compra",
        "params": {
            "productos": productos,
            "origen": "middleware"
        },
        "id": 1
    }
    
    print("\nConfirmando recepción a Proveedores...")
    
    try:
        response = requests.post(URL_PROVEEDORES, json=payload, timeout=5)
        print("Proveedores confirmado")
    except Exception as e:
        print(f"No se pudo confirmar a Proveedores: {e}")


if __name__ == "__main__":
    print("="*60)
    print("MiddleWare corriendo en 192.168.1.10:5010")
    print("="*60)
    print("\nEndpoints:")
    print("  - middleWareController() → Flujo de ventas")
    print("  - middlewareControllerProveedores() → Flujo de compras")
    print("="*60 + "\n")
    serve("192.168.1.10", 5010)