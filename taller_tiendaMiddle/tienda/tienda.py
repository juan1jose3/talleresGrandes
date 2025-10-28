import requests
import json
from jsonrpcserver import method, serve, Success

URL_MIDDLEWARE = "http://192.168.1.10:5010"
catalogo = []
@method
def tienda_controller():
    cargar_productos()
    return Success()

@method
def cargar_productos(productos,origen=None):
    global catalogo
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "Tienda"},
        "id": 1
    }

    if productos:
        catalogo = productos
     
        print(f"TIENDA: Obteniendo productos de inventario {origen}...")
        #print(json.dumps(productos,indent=4, ensure_ascii=False))
      
        for producto in productos["productos"]:
            print(f"ID: {producto['id']} - Nombre: {producto['nombre']} - Categoría: {producto['categoria']} - Precio: {producto['precio']} - Stock {producto['stock']}")
    else:
        catalogo.append("Vacío")

    print()
    carrito = crear_orden()

    return Success({"productos":carrito})


def crear_orden():    
   
    cantidad_de_productos = int(input("¿Cuantos productos desea comprar?: "))
    i = 0
    carro_de_compras = []
    while i < cantidad_de_productos:
        compra = int(input("¿Que desea comprar?(Ingrese id): "))
        
        for item in catalogo["productos"]:
            if item["id"] == compra:
                cantidad = int(input(f"¿Cuantas unidades de {item['nombre']}?: "))
                
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
    print(carro_de_compras)
    return carro_de_compras

@method
def leer_factura(factura,origen=None):
    print(factura)
    print(origen)

    return Success({"mensaje":"factura esta aqui"})


if __name__ == "__main__":
    serve("192.168.1.3", 5002)