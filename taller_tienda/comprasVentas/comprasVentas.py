from jsonrpcserver import method, serve,Success

import json



ventas_registradas = []
@method
def registrar_venta(carrito,origen=None):
    ventas_registradas.append(carrito)
    print(f"Venta nueva desde: {origen}")
    print(ventas_registradas)

    """"
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {"origen": "ComprasVentas"},
        "id": 1
    }
    try:
        url_contabilidad = "http://172.20.0.5:5003"
        response = requests.post(url_contabilidad, json=payload, timeout=5)
        print("Enviando a contabilidad")


    except Exception as e:
        print(f"Error{e}")
    """
    mensaje = {
        "mensaje": "Venta registrada exitosamente",
        "productos": carrito
    }

    return Success(mensaje)



if __name__ == "__main__":
    print("Compras ventas corriendo")
    serve("172.20.0.4",5002)