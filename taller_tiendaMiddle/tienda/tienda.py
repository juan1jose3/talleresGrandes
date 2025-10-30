"""
Microservicio de Tienda - Sistema Distribuido de Gestión de Muebles
====================================================================

Este microservicio gestiona la interfaz de tienda para clientes utilizando JSON-RPC 2.0.
Proporciona funcionalidades para visualizar el catálogo de productos, crear órdenes de
compra y recibir facturas del sistema de ventas.

Configuración del Servicio
--------------------------
- **Host:** 192.168.1.3
- **Puerto:** 5002
- **Protocolo:** JSON-RPC 2.0
- **Versión:** 1.0.0
- **Middleware:** http://192.168.1.10:5010

Dependencias
------------
Este servicio se comunica con:
    - Middleware (192.168.1.10:5010): Para orquestar las operaciones del sistema
    - Servicio de Inventario (indirectamente): A través del middleware para obtener productos

Variables Globales
-----------------
catalogo : list
    Almacena temporalmente el catálogo de productos recibido del inventario.
    Se actualiza cada vez que se invoca el método 'ordenar' con productos.

URL_MIDDLEWARE : str
    URL del servicio middleware para comunicación entre microservicios.
    Valor: "http://192.168.1.10:5010"

Flujo de Operación
------------------
1. El cliente invoca 'tienda_controller' para iniciar el proceso de compra
2. Se obtiene el catálogo de productos del inventario vía middleware
3. El usuario interactúa por consola para crear su orden de compra
4. La orden se envía al middleware para procesamiento
5. El servicio recibe la factura final mediante 'leer_factura'

Ejemplo de Uso
--------------
Para iniciar el servicio::

    python tienda.py

El servicio quedará escuchando peticiones JSON-RPC en 192.168.1.3:5002

Ejemplo de flujo completo desde cliente JSON-RPC::

    import requests
    
    # Iniciar proceso de compra
    payload = {
        "jsonrpc": "2.0",
        "method": "tienda_controller",
        "params": {},
        "id": 1
    }
    
    response = requests.post("http://192.168.1.3:5002", json=payload)

Notas
-----
- Este servicio requiere interacción por consola del usuario
- El catálogo se mantiene en memoria durante la sesión
- La comunicación con otros servicios es a través del middleware

See Also
--------
middleware : Orquestador del sistema distribuido
inventario : Servicio de gestión de productos
ventas : Servicio de procesamiento de transacciones
"""

import requests
import json
from jsonrpcserver import method, serve, Success

# URL del middleware para comunicación entre servicios
URL_MIDDLEWARE = "http://192.168.1.10:5010"

# Catálogo de productos en memoria
catalogo = []


@method
def tienda_controller():
    """
    Controlador principal que inicia el flujo de compra en la tienda.
    
    Este método orquesta el proceso completo de compra: obtiene el catálogo de
    productos y facilita la creación de una orden. Es el punto de entrada
    principal para que un cliente inicie una transacción de compra.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    Success
        Objeto Success vacío indicando que el controlador se ejecutó correctamente.
        
        Estructura::
        
            {}
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "tienda_controller",
            "params": {},
            "id": 1
        }
    
    Respuesta JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {},
            "id": 1
        }
    
    Notes
    -----
    - Este método invoca internamente a 'ordenar()' sin parámetros
    - El flujo continúa con interacción del usuario por consola
    - No retorna datos significativos ya que el proceso es interactivo
    
    See Also
    --------
    ordenar : Gestiona la visualización del catálogo y creación de orden
    crear_orden : Función auxiliar para capturar la orden del usuario
    """
    ordenar()
    return Success()


@method
def ordenar(productos, origen=None):
    """
    Gestiona la visualización del catálogo y la creación de órdenes de compra.
    
    Este método recibe el catálogo de productos (generalmente del servicio de
    inventario), lo muestra al usuario por consola y facilita la creación de
    una orden de compra mediante interacción del usuario.
    
    Parameters
    ----------
    productos : dict or None
        Diccionario conteniendo el catálogo de productos con la estructura:
        
        {
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
        }
        
        Si es None, se marca el catálogo como vacío.
    
    origen : str, optional
        Identificador del servicio que envía los productos.
        Se utiliza para logging y trazabilidad.
        Default: None
    
    Returns
    -------
    Success
        Objeto Success conteniendo el carrito de compras creado:
        
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
    
    Examples
    --------
    Solicitud JSON-RPC con productos::
    
        {
            "jsonrpc": "2.0",
            "method": "ordenar",
            "params": {
                "productos": {
                    "productos": [
                        {
                            "id": 1,
                            "nombre": "Sofá Seccional",
                            "categoria": "Sala",
                            "precio": 1200.0,
                            "stock": 5
                        },
                        {
                            "id": 2,
                            "nombre": "Mesa de Comedor",
                            "categoria": "Comedor",
                            "precio": 800.0,
                            "stock": 10
                        }
                    ]
                },
                "origen": "Inventario"
            },
            "id": 2
        }
    
    Salida por consola::
    
        TIENDA: Obteniendo productos de inventario Inventario...
        ID: 1 - Nombre: Sofá Seccional - Categoría: Sala - Precio: 1200.0 - Stock 5
        ID: 2 - Nombre: Mesa de Comedor - Categoría: Comedor - Precio: 800.0 - Stock 10
        
        ¿Cuantos productos desea comprar?: 2
        ¿Que desea comprar?(Ingrese id): 1
        ¿Cuantas unidades de Sofá Seccional?: 2
        ¿Que desea comprar?(Ingrese id): 2
        ¿Cuantas unidades de Mesa de Comedor?: 1
    
    Respuesta JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 5,
                        "comprar": 2
                    },
                    {
                        "id": 2,
                        "nombre": "Mesa de Comedor",
                        "categoria": "Comedor",
                        "precio": 800.0,
                        "stock": 10,
                        "comprar": 1
                    }
                ]
            },
            "id": 2
        }
    
    Solicitud con catálogo vacío::
    
        {
            "jsonrpc": "2.0",
            "method": "ordenar",
            "params": {
                "productos": null,
                "origen": "Sistema"
            },
            "id": 3
        }
    
    Notes
    -----
    - Modifica la variable global 'catalogo' con los productos recibidos
    - Si productos es None o False, agrega "Vacío" al catálogo
    - Muestra cada producto con formato legible en consola
    - Invoca 'crear_orden()' para capturar la interacción del usuario
    - El payload interno muestra intención de comunicación con middleware
      (aunque no se usa activamente en el código actual)
    
    Warnings
    --------
    - Este método requiere interacción por consola (stdin)
    - Puede bloquear la ejecución esperando entrada del usuario
    - Si se llama desde un entorno sin terminal, la entrada fallará
    
    See Also
    --------
    crear_orden : Función que captura la orden interactivamente
    tienda_controller : Invoca este método para iniciar el flujo
    leer_factura : Recibe la factura después del procesamiento
    """
    global catalogo
    
    # Preparación de payload para comunicación con middleware (no utilizado activamente)
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "Tienda"},
        "id": 1
    }
    
    if productos:
        catalogo = productos
        print(f"TIENDA: Obteniendo productos de inventario {origen}...")
        
        # Mostrar catálogo formateado en consola
        for producto in productos["productos"]:
            print(f"ID: {producto['id']} - Nombre: {producto['nombre']} - "
                  f"Categoría: {producto['categoria']} - Precio: {producto['precio']} - "
                  f"Stock {producto['stock']}")
    else:
        catalogo.append("Vacío")
    
    print()
    
    # Crear orden de compra mediante interacción con el usuario
    carrito = crear_orden()
    
    return Success({"productos": carrito})


def crear_orden():
    """
    Captura interactivamente la orden de compra del usuario por consola.
    
    Esta función NO es un método JSON-RPC, sino una función auxiliar interna.
    Solicita al usuario que seleccione productos del catálogo y especifique
    cantidades, construyendo un carrito de compras.
    
    Parameters
    ----------
    None
        Utiliza la variable global 'catalogo' para acceder a los productos disponibles.
    
    Returns
    -------
    list of dict
        Lista de productos seleccionados para compra con la estructura:
        
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
        
        Cada elemento incluye toda la información del producto más el campo
        'comprar' que indica la cantidad solicitada.
    
    Raises
    ------
    ValueError
        Si el usuario ingresa valores no numéricos cuando se esperan enteros.
    
    KeyError
        Si la estructura del catálogo no contiene la clave "productos".
    
    Examples
    --------
    Interacción por consola (entrada del usuario precedida por >)::
    
        ¿Cuantos productos desea comprar?: > 2
        ¿Que desea comprar?(Ingrese id): > 1
        ¿Cuantas unidades de Sofá Seccional?: > 3
        ¿Que desea comprar?(Ingrese id): > 5
        ¿Cuantas unidades de Estantería?: > 2
        [
            {
                'id': 1,
                'nombre': 'Sofá Seccional',
                'categoria': 'Sala',
                'precio': 1200.0,
                'stock': 5,
                'comprar': 3
            },
            {
                'id': 5,
                'nombre': 'Estantería',
                'categoria': 'Almacenamiento',
                'precio': 200.0,
                'stock': 15,
                'comprar': 2
            }
        ]
    
    Valor de retorno::
    
        [
            {"id": 1, "nombre": "Sofá Seccional", "categoria": "Sala", 
             "precio": 1200.0, "stock": 5, "comprar": 3},
            {"id": 5, "nombre": "Estantería", "categoria": "Almacenamiento",
             "precio": 200.0, "stock": 15, "comprar": 2}
        ]
    
    Notes
    -----
    - Esta es una función auxiliar, NO un método JSON-RPC
    - Requiere que 'catalogo' global esté poblado con productos
    - Utiliza input() bloqueante para capturar datos del usuario
    - Si el ID no existe en el catálogo, ignora la entrada y no incrementa el contador
    - Imprime el carrito completo antes de retornarlo
    - No valida stock disponible (esa validación ocurre en el servicio de inventario)
    
    Warnings
    --------
    - Función bloqueante que requiere stdin interactivo
    - No maneja excepciones de ValueError por entradas inválidas
    - Si el catálogo está vacío o mal formado, puede generar errores
    - No hay validación de cantidades negativas o cero
    
    See Also
    --------
    ordenar : Método que invoca esta función
    validar_stock : Método del servicio de inventario que valida disponibilidad
    """
    cantidad_de_productos = int(input("¿Cuantos productos desea comprar?: "))
    i = 0
    carro_de_compras = []
    
    while i < cantidad_de_productos:
        compra = int(input("¿Que desea comprar?(Ingrese id): "))
        
        # Buscar el producto en el catálogo
        for item in catalogo["productos"]:
            if item["id"] == compra:
                cantidad = int(input(f"¿Cuantas unidades de {item['nombre']}?: "))
                
                # Crear elemento del carrito con toda la información del producto
                elementos = {}
                elementos["id"] = item["id"]
                elementos["nombre"] = item["nombre"]
                elementos["categoria"] = item["categoria"]
                elementos["precio"] = item["precio"]
                elementos["stock"] = item["stock"]
                elementos["comprar"] = cantidad
                
                carro_de_compras.append(elementos)
                i += 1
                break
    
    # Mostrar carrito en consola
    print(carro_de_compras)
    
    return carro_de_compras


@method
def leer_factura(factura, origen=None, transporte=None):
    """
    Recibe y procesa la factura generada después de completar una venta.
    
    Este método actúa como endpoint para que el middleware o servicio de ventas
    envíe la factura final al cliente/tienda después de procesar una transacción.
    Muestra la información de la factura por consola.
    
    Parameters
    ----------
    factura : dict
        Diccionario conteniendo los detalles de la factura. La estructura exacta
        depende del servicio de ventas, pero típicamente incluye:
        
        {
            "id_factura": str,
            "fecha": str,
            "productos": list,
            "subtotal": float,
            "iva": float,
            "total": float,
            "cliente": dict,
            ...
        }
    
    origen : str, optional
        Identificador del servicio que envía la factura (ej: "Ventas", "Middleware").
        Se utiliza para logging y trazabilidad.
        Default: None
    
    transporte : str, optional
        Información sobre el método de transporte o envío asociado a la venta.
        Puede contener detalles del servicio de logística.
        Default: None
    
    Returns
    -------
    Success
        Objeto Success con confirmación de recepción:
        
        {
            "mensaje": "factura esta aqui"
        }
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "leer_factura",
            "params": {
                "factura": {
                    "id_factura": "FAC-001",
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
                    "subtotal": 2400.0,
                    "iva": 456.0,
                    "total": 2856.0
                },
                "origen": "Ventas",
                "transporte": "Envío Express - 2 días hábiles"
            },
            "id": 10
        }
    
    Salida por consola::
    
        {'id_factura': 'FAC-001', 'fecha': '2025-10-30', 'productos': [...], 
         'subtotal': 2400.0, 'iva': 456.0, 'total': 2856.0}
        Ventas
        Envío Express - 2 días hábiles
    
    Respuesta JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "factura esta aqui"
            },
            "id": 10
        }
    
    Notes
    -----
    - Imprime los tres parámetros recibidos por consola para debugging
    - No realiza procesamiento ni validación de la factura
    - El mensaje de retorno es estático y siempre el mismo
    - Este método actúa como callback/endpoint de notificación
    
    Warnings
    --------
    - No valida la estructura de la factura recibida
    - No persiste la factura en ningún almacenamiento
    - Los parámetros pueden ser None sin causar errores
    
    See Also
    --------
    ordenar : Inicia el proceso que eventualmente genera la factura
    crear_orden : Crea la orden que se procesa en venta
    """
    print(factura)
    print(origen)
    print(transporte)
    
    return Success({"mensaje": "factura esta aqui"})


if __name__ == "__main__":
    print("Tienda corriendo")
    serve("192.168.1.3", 5002)