import requests
import json
from jsonrpcserver import method, serve, Success

origen = "MiddleWare"

URL_INVENTARIO = "http://192.168.1.2:5001"
URL_TIENDA = "http://192.168.1.3:5002"
URL_COMPRASVENTAS = "http://192.168.1.4:5003"
URL_CONTABILIDAD = "http://192.168.1.5:5004"
URL_PROVEEDORES = "http://192.168.1.6:5005"

carrito_compras = {}

@method
def middleWareController():
    productos = cargar_productos()
    enviar_productos_tienda(productos)
    enviar_compras_ventas()
    return Success()



def cargar_productos():
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": origen},
        "id": 1
    }
   

    print("Solicitando productos a inventario")


    response = requests.post(URL_INVENTARIO, json=payload, timeout=None)
    productos = response.json()

    print("Productos recibidos")

    print(productos)
    return productos


def enviar_productos_tienda(productos):
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {
                    "origen": origen,
                    "productos":productos["result"]
                },
        "id": 1
    }

    print("Enviando productos a tienda .....")

    try:
        response = requests.post(URL_TIENDA, json=payload, timeout=5)
        message = response.json()
        print(f"Mensaje desde tienda:{message}")
        carrito_compras["carrito"] = message
        return Success(message)
    except Exception as e:
        return Success({"Error" : e})

    


def enviar_compras_ventas():
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_venta",
        "params": {
                    "origen": origen,
                    "carrito":carrito_compras
                },
        "id": 1
    }

    print("Enviando a comprasVentas")

    response = requests.post(URL_COMPRASVENTAS, json=payload, timeout=None)










if __name__ == "__main__":
    print("MiddleWare corriendo")
    serve("192.168.1.10",5010)