import requests
import json
from jsonrpcserver import method, serve,Success

URL_INVENTARIO = "http://172.20.0.3:5001"

@method
def tienda_controller():
    cargar_productos()
    return Success()
    



@method
def cargar_productos():
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "Tienda"},
        "id": 1
    }

    print(f"TIENDA: Pidiendo productod de inventario {URL_INVENTARIO}...")
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        print("Respuesta de Inventario:")
        
        data = response.json()
        #print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        for producto in data["result"]:
            print(f"ID: {producto["id"]} - Nombre: {producto["nombre"]} - Categoría: {producto["categoria"]} - Precio: {producto["precio"]} - Stock {producto["stock"]}")
    except Exception as e:
        print(f"ERROR: {e}")
    cantidad_de_productos = int(input("¿Cuantos productos desea comprar?: "))

    i = 0
    carro_de_compras = []
    while i < cantidad_de_productos: 
        compra = int(input("¿Que desea comprar?(Ingrese id): "))
        for item in data["result"]:
            if item["id"] == compra:
                elementos = {}
                elementos["id"] = item["id"]
                elementos["nombre"] = item["nombre"]
                elementos["categoria"] = item["categoria"]
                elementos["precio"] = item["precio"]
                elementos["stock"] = item["stock"]
                carro_de_compras.append(elementos)
        i += 1
    
    payload_venta ={
        "jsonrpc": "2.0",
        "method": "registrar_venta",
        "params": {
                "carrito": carro_de_compras,
                "origen":"tienda"
            },
        "id": 1
    }
    URL_COMPRASVENTAS = "http://172.20.0.4:5003"
    response = requests.post(URL_COMPRASVENTAS, json=payload_venta, timeout=5)
    data = response.json()
    print("COMPRA REGISTRADA")

    try:
        responseFactura = requests.post(URL_COMPRASVENTAS,json=payload_venta, timeout=5)
        dataFactura = responseFactura.json()
        print(dataFactura)
    except Exception as e:
        print(f"Error: {e}")

    #print(data)



if __name__ == "__main__":
    serve("172.20.0.2",5002)
    

    

 
    

