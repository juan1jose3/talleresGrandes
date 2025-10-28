from jsonrpcserver import method, serve, Success
import requests
import json

ventas_registradas = []
compras_registradas = []
factura_actual = {}


URL_MIDDLEWARE = "http://192.168.1.10:5010"

@method
def registrar_venta(carrito, origen=None):
    ventas_registradas.append(carrito)
    print(f"Venta nueva desde: {origen}")
    print(ventas_registradas)

    return Success({"Message":"carrito recivido"})


@method
def registrar_compra(productos, origen=None):
    """
    Registra una compra a proveedores.
    """
    compra = {
        "productos": productos,
        "origen": origen,
        "timestamp": json.dumps({"fecha": "now"})  
    }
    
    compras_registradas.append(compra)
    
   
    print("COMPRA REGISTRADA")
    print(f"Origen: {origen}")
    print(f"Productos a comprar: {len(productos)}")
    print()
    
    total_unidades = 0
    for p in productos:
        cantidad = p.get('comprar', 0)
        total_unidades += cantidad
        print(f"  - {p['nombre']}: {cantidad} unidades (${p['precio']} c/u)")
    
    print(f"\nTotal unidades: {total_unidades}")
    print(f"Total de compras registradas: {len(compras_registradas)}")
    
    return Success({"mensaje": "Compra registrada exitosamente"})




if __name__ == "__main__":
    print("Compras ventas corriendo")
    serve("192.168.1.4", 5003)