from jsonrpcserver import method, serve, Success
import requests
import json

URL_INVENTARIO = "http://172.20.0.3:5001"
URL_COMPRASVENTAS = "http://172.20.0.4:5003"

@method
def proveedores():
    print("Mandando petición para saber el stock de productos ....")
    productos = cargar_requerimientos_productos()

    if productos:
        print("\n Enviando productos con bajo stock a ComprasVentas...")
        enviar_a_comprasventas(productos)
    else:
        print("No hay productos con bajo stock.")

    return Success({"productos_bajo_stock": productos})


def cargar_requerimientos_productos():
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "atencionProveedores"},
        "id": 1
    }

    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        print("Respuesta de Inventario:")
        data = response.json()

        print("Productos con poco stock")
        productos_lista = []

        for producto in data["result"]:
            if producto["stock"] <= 5:
                print(f"ID: {producto['id']} - Nombre: {producto['nombre']} - Categoría: {producto['categoria']} - Precio: {producto['precio']} - Stock {producto['stock']}")

                productos_lista.append({
                    "id": producto["id"],
                    "nombre": producto["nombre"],
                    "categoria": producto["categoria"],
                    "precio": producto["precio"],
                    "stock": producto["stock"]
                })

        return productos_lista

    except Exception as e:
        print(f"Error al cargar productos: {e}")
        return []


def enviar_a_comprasventas(productos):
    """
    Envía los productos con bajo stock al microservicio de ComprasVentas.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_compra",
        "params": {"productos": productos, "origen": "proveedores"},
        "id": 1
    }

    try:
        response = requests.post(URL_COMPRASVENTAS, json=payload, timeout=5)
        data = response.json()
        print(f"Respuesta de ComprasVentas: {data}")
    except Exception as e:
        print(f"Error al enviar productos a ComprasVentas: {e}")




if __name__ == "__main__":
    print("Servicio de Proveedores corriendo en 172.20.0.6:5005")
    serve("172.20.0.6", 5005)
