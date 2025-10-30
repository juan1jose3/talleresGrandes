Module taller_tiendaMiddle.comprasVentas.comprasVentas
======================================================
Microservicio de Compras y Ventas - Sistema Distribuido de Gestión de Muebles
==============================================================================

Este microservicio gestiona el registro de ventas a clientes y compras a proveedores
utilizando JSON-RPC 2.0. Actúa como sistema de registro transaccional para mantener
el histórico de todas las operaciones comerciales del negocio.

Configuración del Servicio
--------------------------
- **Host:** 192.168.1.4
- **Puerto:** 5003
- **Protocolo:** JSON-RPC 2.0
- **Versión:** 1.0.0
- **Middleware:** http://192.168.1.10:5010

Responsabilidades
-----------------
Este servicio es responsable de:
    - Registrar todas las ventas realizadas a clientes
    - Registrar todas las compras realizadas a proveedores
    - Mantener histórico de transacciones en memoria
    - Generar estadísticas básicas de operaciones
    - Proveer información para auditoría y reportes

Dependencias
------------
Este servicio se comunica con:
    - Middleware (192.168.1.10:5010): Para orquestar operaciones del sistema
    - Servicio de Inventario (indirectamente): Para sincronizar stock
    - Servicio de Tienda (indirectamente): Para procesar órdenes de clientes

Variables Globales
-----------------
ventas_registradas : list
    Lista que almacena todas las ventas realizadas. Cada elemento es un carrito
    de compras con los productos vendidos.
    
compras_registradas : list
    Lista que almacena todas las compras a proveedores. Cada elemento contiene
    productos, origen y timestamp de la operación.
    
factura_actual : dict
    Diccionario que almacena la factura en proceso actual.
    (Actualmente no utilizado en las operaciones)
    
URL_MIDDLEWARE : str
    URL del servicio middleware para comunicación entre microservicios.
    Valor: "http://192.168.1.10:5010"

Modelo de Datos
---------------
**Estructura de Venta:**
    Lista de productos vendidos, cada uno con:
    - id (int): ID del producto
    - nombre (str): Nombre del producto
    - categoria (str): Categoría del producto
    - precio (float): Precio unitario
    - stock (int): Stock disponible al momento de la venta
    - comprar (int): Cantidad vendida

**Estructura de Compra:**
    {
        "productos": list,  # Lista de productos comprados
        "origen": str,      # Servicio o usuario que registró la compra
        "timestamp": str    # Timestamp de la operación en formato JSON
    }

Flujo de Operaciones
--------------------
**Flujo de Venta:**
    1. Cliente crea orden en Tienda
    2. Middleware valida stock en Inventario
    3. Se invoca 'registrar_venta' para guardar la transacción
    4. Inventario se actualiza restando stock
    5. Se genera factura al cliente

**Flujo de Compra a Proveedor:**
    1. Administrador crea orden de compra
    2. Se invoca 'registrar_compra' para guardar la transacción
    3. Inventario se actualiza sumando stock
    4. Se registra la operación para control

Ejemplo de Uso
--------------
Para iniciar el servicio::

    python comprasVentas.py

El servicio quedará escuchando peticiones JSON-RPC en 192.168.1.4:5003

Ejemplo de registro de venta desde cliente JSON-RPC::

    import requests
    
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_venta",
        "params": {
            "carrito": [
                {
                    "id": 1,
                    "nombre": "Sofá Seccional",
                    "precio": 1200.0,
                    "comprar": 2
                }
            ],
            "origen": "Tienda"
        },
        "id": 1
    }
    
    response = requests.post("http://192.168.1.4:5003", json=payload)
    print(response.json())

Notas
-----
- Los registros se mantienen en memoria durante la ejecución del servicio
- No hay persistencia en base de datos (se pierde al reiniciar)
- Ideal para sistemas de prueba o con persistencia externa
- Útil para auditoría y generación de reportes en tiempo real

Limitaciones
------------
- Sin persistencia permanente de transacciones
- Sin validación de duplicados
- Sin mecanismos de rollback
- Sin encriptación de datos sensibles

See Also
--------
inventario : Servicio de gestión de stock
tienda : Servicio de interfaz con clientes
middleware : Orquestador del sistema distribuido

Functions
---------

`registrar_compra(productos, origen=None)`
:   Registra una compra realizada a proveedores para reabastecer inventario.
    
    Este método almacena las compras a proveedores en el sistema, incluyendo
    los productos adquiridos, el origen de la solicitud y un timestamp. Proporciona
    estadísticas detalladas de la compra por consola.
    
    Parameters
    ----------
    productos : list of dict
        Lista de productos comprados al proveedor. Cada producto debe contener:
        
        {
            "id": int,              # ID del producto
            "nombre": str,          # Nombre del producto
            "categoria": str,       # Categoría del producto
            "precio": float,        # Precio de compra unitario
            "stock": int,           # Stock actual (informativo)
            "comprar": int          # Cantidad a comprar
        }
        
        Ejemplo::
        
            [
                {
                    "id": 1,
                    "nombre": "Sofá Seccional",
                    "categoria": "Sala",
                    "precio": 1200.0,
                    "stock": 5,
                    "comprar": 10
                },
                {
                    "id": 4,
                    "nombre": "Cama Queen",
                    "categoria": "Dormitorio",
                    "precio": 1000.0,
                    "stock": 7,
                    "comprar": 5
                }
            ]
    
    origen : str, optional
        Identificador del servicio, usuario o sistema que solicita la compra.
        Ejemplos: "Administrador", "Sistema Automatico", "Gerente"
        Se utiliza para trazabilidad y auditoría.
        Default: None
    
    Returns
    -------
    Success
        Objeto Success con confirmación de registro:
        
        {
            "mensaje": "Compra registrada exitosamente"
        }
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "registrar_compra",
            "params": {
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 5,
                        "comprar": 10
                    },
                    {
                        "id": 9,
                        "nombre": "Armario",
                        "categoria": "Dormitorio",
                        "precio": 600.0,
                        "stock": 4,
                        "comprar": 8
                    }
                ],
                "origen": "Administrador"
            },
            "id": 5
        }
    
    Salida por consola::
    
        COMPRA REGISTRADA
        Origen: Administrador
        Productos a comprar: 2
        
          - Sofá Seccional: 10 unidades ($1200.0 c/u)
          - Armario: 8 unidades ($600.0 c/u)
        
        Total unidades: 18
        Total de compras registradas: 1
    
    Respuesta JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Compra registrada exitosamente"
            },
            "id": 5
        }
    
    Estructura interna de registro::
    
        {
            "productos": [
                {
                    "id": 1,
                    "nombre": "Sofá Seccional",
                    "categoria": "Sala",
                    "precio": 1200.0,
                    "stock": 5,
                    "comprar": 10
                },
                ...
            ],
            "origen": "Administrador",
            "timestamp": '{"fecha": "now"}'
        }
    
    Notes
    -----
    - Crea un objeto de compra con productos, origen y timestamp
    - El timestamp actualmente es estático con valor '{"fecha": "now"}'
    - Agrega la compra a la lista global 'compras_registradas'
    - Imprime estadísticas detalladas en consola:
        - Origen de la compra
        - Número de productos diferentes
        - Detalle de cada producto con cantidad y precio
        - Total de unidades compradas
        - Total acumulado de compras registradas
    - No valida disponibilidad del proveedor
    - No calcula el costo total de la compra
    
    Warnings
    --------
    - El timestamp es estático y no refleja la fecha/hora real
    - Los datos no persisten después de reiniciar el servicio
    - No hay validación de duplicados
    - No hay límite de memoria para compras_registradas
    - Si 'comprar' no está en el producto, se asume 0 unidades
    - No se valida que los precios sean positivos
    
    See Also
    --------
    registrar_venta : Registra ventas a clientes
    compras_registradas : Variable global que almacena todas las compras
    actualizar_inventario : Método en servicio de inventario que suma stock

`registrar_venta(carrito, origen=None)`
:   Registra una venta realizada a un cliente en el sistema.
    
    Este método almacena el carrito de compras en el registro de ventas para
    mantener el histórico de transacciones. Se invoca típicamente después de
    validar el stock y antes de actualizar el inventario.
    
    Parameters
    ----------
    carrito : list of dict
        Lista de productos vendidos. Cada producto debe contener:
        
        {
            "id": int,              # ID del producto
            "nombre": str,          # Nombre del producto
            "categoria": str,       # Categoría del producto
            "precio": float,        # Precio unitario
            "stock": int,           # Stock disponible (informativo)
            "comprar": int          # Cantidad vendida
        }
        
        Ejemplo::
        
            [
                {
                    "id": 1,
                    "nombre": "Sofá Seccional",
                    "categoria": "Sala",
                    "precio": 1200.0,
                    "stock": 5,
                    "comprar": 2
                },
                {
                    "id": 3,
                    "nombre": "Silla de Oficina",
                    "categoria": "Oficina",
                    "precio": 150.0,
                    "stock": 20,
                    "comprar": 5
                }
            ]
    
    origen : str, optional
        Identificador del servicio o usuario que origina la venta.
        Ejemplos: "Tienda", "Sistema Web", "App Móvil", "Usuario123"
        Se utiliza para trazabilidad y auditoría.
        Default: None
    
    Returns
    -------
    Success
        Objeto Success con confirmación de registro:
        
        {
            "Message": "carrito recivido"
        }
        
        Nota: El mensaje contiene un error tipográfico intencional ("recivido")
        que se mantiene para compatibilidad con el sistema existente.
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "registrar_venta",
            "params": {
                "carrito": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 5,
                        "comprar": 2
                    },
                    {
                        "id": 6,
                        "nombre": "Mesa de Centro",
                        "categoria": "Sala",
                        "precio": 250.0,
                        "stock": 12,
                        "comprar": 1
                    }
                ],
                "origen": "Tienda"
            },
            "id": 1
        }
    
    Salida por consola::
    
        Venta nueva desde: Tienda
        [
            [
                {
                    'id': 1,
                    'nombre': 'Sofá Seccional',
                    'categoria': 'Sala',
                    'precio': 1200.0,
                    'stock': 5,
                    'comprar': 2
                },
                {
                    'id': 6,
                    'nombre': 'Mesa de Centro',
                    'categoria': 'Sala',
                    'precio': 250.0,
                    'stock': 12,
                    'comprar': 1
                }
            ]
        ]
    
    Respuesta JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "Message": "carrito recivido"
            },
            "id": 1
        }
    
    Notes
    -----
    - Agrega el carrito completo a la lista global 'ventas_registradas'
    - Imprime información de la venta en consola para logging
    - No valida la estructura del carrito recibido
    - No calcula totales ni genera factura (eso se hace en otros servicios)
    - El registro es inmediato y no reversible
    - Mantiene todas las ventas en memoria sin límite de tamaño
    
    Warnings
    --------
    - Los datos no persisten después de reiniciar el servicio
    - No hay validación de duplicados (la misma venta puede registrarse múltiples veces)
    - No hay límite de memoria para ventas_registradas
    - Si el origen es None, se imprime "None" en consola
    
    See Also
    --------
    registrar_compra : Registra compras a proveedores
    ventas_registradas : Variable global que almacena todas las ventas