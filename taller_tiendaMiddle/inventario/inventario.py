from jsonrpcserver import method, serve, Success
import json

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
    if origen:
        print(f"Solicitud recibida de {origen}")
    return Success(productos)

@method
def actualizar_inventario(carrito, tipo_operacion="venta"):
    """
    Actualiza el stock de los productos según la operación.
    - tipo_operacion="venta": Resta stock (compra del cliente)
    - tipo_operacion="compra": Suma stock (compra a proveedores)
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
    print("Servicio de Inventario corriendo en 172.20.0.3:5001")
    serve("172.20.0.3", 5001)
