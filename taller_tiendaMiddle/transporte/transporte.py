import requests
import json
from jsonrpcserver import method, serve, Success

# odio este componente :(

@method
def ordenar_transporte(factura,origen):
    print(factura)
    print(origen)

    return Success({"mensaje":"Transporte ordenado, tu pedido llegará en 3 días hábiles"})


if __name__ == "__main__":
    print("Transporte a la espera")
    serve("192.168.1.7",5006)