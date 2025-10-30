"""
Microservicio de Inventario - Sistema Distribuido de Gestión de Muebles
========================================================================

Este microservicio gestiona el inventario de productos utilizando JSON-RPC 2.0.
Proporciona funcionalidades para consultar productos, validar stock y actualizar
el inventario según las operaciones de venta o compra.

Configuración del Servicio
--------------------------
- **Host:** 192.168.1.2
- **Puerto:** 5001
- **Protocolo:** JSON-RPC 2.0
- **Versión:** 1.0.0

Datos Iniciales
--------------
El servicio mantiene un catálogo de 10 productos de muebles con las siguientes categorías:
- Sala
- Comedor
- Oficina
- Dormitorio
- Almacenamiento
- Bar

Estructura del Producto
-----------------------
Cada producto contiene:
    - id (int): Identificador único del producto
    - nombre (str): Nombre descriptivo del producto
    - categoria (str): Categoría a la que pertenece
    - precio (float): Precio unitario en la moneda del sistema
    - stock (int): Cantidad disponible en inventario

Ejemplo de Uso
--------------
Para iniciar el servicio::

    python inventario.py

El servicio quedará escuchando peticiones JSON-RPC en 192.168.1.2:5001

Ejemplo de llamada desde cliente JSON-RPC::

    import requests
    
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "servicio_ventas"},
        "id": 1
    }
    
    response = requests.post("http://192.168.1.2:5001", json=payload)
    productos = response.json()["result"]["productos"]

Notas
-----
- El inventario se mantiene en memoria durante la ejecución del servicio
- Los cambios en el inventario no persisten después de reiniciar el servicio
- Todas las operaciones son síncronas
"""

from jsonrpcserver import method, serve, Success
import json

# Catálogo de productos inicial
productos = [
    {"id": 1, "nombre": "Sofá Seccional", "categoria": "Sala", "precio": 1200.0, "stock": 5},
    {"id": 2, "nombre": "Mesa de Comedor", "categoria": "Comedor", "precio": 800.0, "stock": 10},
    {"id": 3, "nombre": "Silla de Oficina", "categoria": "Oficina", "precio": 150.0, "stock": 20},
    {"id": 4, "nombre": "Cama Queen", "categoria": "Dormitorio", "precio": 1000.0, "stock": 7},
    {"id": 5, "nombre": "Estantería", "categoria": "Almacenamiento", "precio": 200.0, "stock": 15},
    {"id": 6, "nombre": "Mesa de Centro", "categoria": "Sala", "precio": 250.0, "stock": 12},
    {"id": 7, "nombre": "Silla de Comedor", "categoria": "Comedor", "precio": 120.0, "stock": 30},
    {"id": 8, "nombre": "Escritorio", "categoria": "Oficina", "precio": 350.0, "stock": 8},
    {"id": 9, "nombre": "Armario", "categoria": "Dormitorio", "precio": 600.0, "stock": 4},
    {"id": 10, "nombre": "Taburete", "categoria": "Bar", "precio": 90.0, "stock": 25}
]


@method
def cargar_productos(origen=None):
    """
    Obtiene el catálogo completo de productos disponibles en el inventario.
    
    Este método retorna todos los productos con su información detallada incluyendo
    id, nombre, categoría, precio y stock actual. Es utilizado principalmente para
    sincronizar el catálogo entre diferentes microservicios del sistema.
    
    Parameters
    ----------
    origen : str, optional
        Identificador del servicio o cliente que realiza la solicitud.
        Se utiliza para propósitos de logging y trazabilidad.
        Default: None
    
    Returns
    -------
    Success
        Objeto Success de jsonrpcserver conteniendo:
        
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
    
    Examples
    --------
    Solicitud JSON-RPC::
    
        {
            "jsonrpc": "2.0",
            "method": "cargar_productos",
            "params": {
                "origen": "servicio_ventas"
            },
            "id": 1
        }
    
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
                        "stock": 5
                    },
                    ...
                ]
            },
            "id": 1
        }
    
    Notes
    -----
    - Si se proporciona el parámetro 'origen', se imprime en consola para tracking
    - Retorna la lista completa de productos sin filtros
    - No modifica el estado del inventario
    
    See Also
    --------
    validar_stock : Valida disponibilidad de productos para una venta
    actualizar_inventario : Actualiza las cantidades en stock
    """
    if origen:
        print(f"Solicitud recibida de {origen}")
    return Success({"productos": productos})


@method
def validar_stock(carrito):
    """
    Valida si hay suficiente stock disponible para procesar los productos solicitados.
    
    Este método verifica que cada producto en el carrito tenga stock suficiente
    para completar la operación. Es crucial llamar a este método antes de procesar
    una venta para evitar ventas de productos no disponibles.
    
    Parameters
    ----------
    carrito : list of dict
        Lista de productos a validar. Cada elemento debe contener:
        
        - id (int): ID del producto a validar
        - comprar (int): Cantidad solicitada del producto
        
        Estructura::
        
            [
                {"id": 1, "comprar": 2},
                {"id": 3, "comprar": 5},
                ...
            ]
    
    Returns
    -------
    Success
        Objeto Success con la siguiente estructura:
        
        **Si hay stock suficiente:**
        
        {
            "disponible": True,
            "mensaje": "Stock disponible para todos los productos"
        }
        
        **Si hay stock insuficiente:**
        
        {
            "disponible": False,
            "mensaje": "Stock insuficiente para algunos productos",
            "productos_sin_stock": [
                {
                    "nombre": str,
                    "stock_actual": int,
                    "cantidad_solicitada": int
                },
                ...
            ]
        }
    
    Examples
    --------
    Solicitud JSON-RPC con stock suficiente::
    
        {
            "jsonrpc": "2.0",
            "method": "validar_stock",
            "params": {
                "carrito": [
                    {"id": 1, "comprar": 2},
                    {"id": 3, "comprar": 5}
                ]
            },
            "id": 2
        }
    
    Respuesta exitosa::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "disponible": true,
                "mensaje": "Stock disponible para todos los productos"
            },
            "id": 2
        }
    
    Solicitud JSON-RPC con stock insuficiente::
    
        {
            "jsonrpc": "2.0",
            "method": "validar_stock",
            "params": {
                "carrito": [
                    {"id": 1, "comprar": 10}
                ]
            },
            "id": 3
        }
    
    Respuesta con productos sin stock::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "disponible": false,
                "mensaje": "Stock insuficiente para algunos productos",
                "productos_sin_stock": [
                    {
                        "nombre": "Sofá Seccional",
                        "stock_actual": 5,
                        "cantidad_solicitada": 10
                    }
                ]
            },
            "id": 3
        }
    
    Notes
    -----
    - Este método NO modifica el inventario, solo valida disponibilidad
    - Imprime información detallada en consola para cada producto validado
    - Si un producto no se encuentra en el inventario, se omite silenciosamente
    - Se debe llamar antes de 'actualizar_inventario' para garantizar consistencia
    
    Warnings
    --------
    Si el campo 'comprar' no está presente en algún item del carrito, se asume
    cantidad 0, lo cual siempre pasará la validación para ese producto.
    
    See Also
    --------
    actualizar_inventario : Aplica los cambios al inventario después de validar
    cargar_productos : Obtiene el catálogo completo de productos
    """
    print(f"\n{'='*50}")
    print("Validando disponibilidad de stock...")
    print(f"{'='*50}")
    
    productos_sin_stock = []
    
    for item in carrito:
        for p in productos:
            if p["id"] == item["id"]:
                cantidad_solicitada = item.get("comprar", 0)
                
                if p["stock"] < cantidad_solicitada:
                    productos_sin_stock.append({
                        "nombre": p["nombre"],
                        "stock_actual": p["stock"],
                        "cantidad_solicitada": cantidad_solicitada
                    })
                    print(f"{p['nombre']}: Stock insuficiente (disponible: {p['stock']}, solicitado: {cantidad_solicitada})")
                else:
                    print(f"{p['nombre']}: Stock suficiente ({p['stock']} >= {cantidad_solicitada})")
                break
    
    if productos_sin_stock:
        return Success({
            "disponible": False,
            "mensaje": "Stock insuficiente para algunos productos",
            "productos_sin_stock": productos_sin_stock
        })
    else:
        return Success({
            "disponible": True,
            "mensaje": "Stock disponible para todos los productos"
        })


@method
def actualizar_inventario(carrito, tipo_operacion="venta"):
    """
    Actualiza el stock de productos en el inventario según el tipo de operación.
    
    Este método modifica las cantidades en stock de los productos especificados.
    Soporta dos tipos de operaciones: ventas (resta stock) y compras a proveedores
    (suma stock). Es fundamental validar el stock antes de llamar a este método
    en operaciones de venta.
    
    Parameters
    ----------
    carrito : list of dict
        Lista de productos a actualizar. Cada elemento debe contener:
        
        - id (int): ID del producto a actualizar
        - comprar (int): Cantidad a sumar o restar del stock
        
        Estructura::
        
            [
                {"id": 1, "comprar": 2},
                {"id": 3, "comprar": 5},
                ...
            ]
    
    tipo_operacion : str, optional
        Tipo de operación a realizar. Opciones válidas:
        
        - "venta": Resta la cantidad del stock (compra del cliente)
        - "compra": Suma la cantidad al stock (compra a proveedores)
        
        Default: "venta"
    
    Returns
    -------
    Success
        Objeto Success conteniendo:
        
        {
            "mensaje": "Inventario actualizado",
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
        
        Retorna el inventario completo actualizado con los nuevos valores de stock.
    
    Examples
    --------
    Actualización por venta (resta stock)::
    
        {
            "jsonrpc": "2.0",
            "method": "actualizar_inventario",
            "params": {
                "carrito": [
                    {"id": 1, "comprar": 2},
                    {"id": 3, "comprar": 3}
                ],
                "tipo_operacion": "venta"
            },
            "id": 4
        }
    
    Respuesta::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Inventario actualizado",
                "productos": [
                    {
                        "id": 1,
                        "nombre": "Sofá Seccional",
                        "categoria": "Sala",
                        "precio": 1200.0,
                        "stock": 3
                    },
                    ...
                ]
            },
            "id": 4
        }
    
    Actualización por compra a proveedor (suma stock)::
    
        {
            "jsonrpc": "2.0",
            "method": "actualizar_inventario",
            "params": {
                "carrito": [
                    {"id": 1, "comprar": 10}
                ],
                "tipo_operacion": "compra"
            },
            "id": 5
        }
    
    Respuesta::
    
        {
            "jsonrpc": "2.0",
            "result": {
                "mensaje": "Inventario actualizado",
                "productos": [...]
            },
            "id": 5
        }
    
    Notes
    -----
    - Este método MODIFICA el estado global del inventario
    - Imprime en consola el detalle de cada actualización realizada
    - Imprime el inventario completo al finalizar en formato JSON
    - Si un producto no existe en el inventario, se omite silenciosamente
    - El campo 'comprar' con valor 0 no genera cambios en el stock
    
    Warnings
    --------
    - Para operaciones de "venta", asegúrese de llamar primero a 'validar_stock'
      para evitar stock negativo
    - No hay validación de stock negativo en este método
    - Los cambios son inmediatos y no hay rollback automático
    
    See Also
    --------
    validar_stock : Debe llamarse antes para operaciones de venta
    cargar_productos : Obtiene el estado actual del inventario
    
    Raises
    ------
    Este método no lanza excepciones explícitas, pero valores inválidos en
    'tipo_operacion' causarán que se ejecute el comportamiento por defecto (resta).
    """
    print(f"\n{'='*50}")
    print(f"Actualizando inventario ({tipo_operacion})...")
    print(f"{'='*50}")
    
    for item in carrito:
        for p in productos:
            if p["id"] == item["id"]:
                cantidad = item.get("comprar", 0)
                stock_anterior = p["stock"]
                
                if tipo_operacion == "compra":
                    p["stock"] += cantidad
                    operacion_simbolo = "+"
                else:
                    p["stock"] -= cantidad
                    operacion_simbolo = "-"
                
                print(f"  {operacion_simbolo} {p['nombre']}: {stock_anterior} {operacion_simbolo} {cantidad} = {p['stock']}")
                break
    
    print("\nInventario final actualizado:")
    print(json.dumps(productos, indent=4, ensure_ascii=False))
    
    return Success({"mensaje": "Inventario actualizado", "productos": productos})


if __name__ == "__main__":
    print("Servicio de Inventario corriendo en 192.168.1.2:5001")
    serve("192.168.1.2", 5001)