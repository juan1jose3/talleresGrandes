from jsonrpcserver import method, serve,Success
import requests
import json



ventas_registradas = []
factura_actual ={}
url_contabilidad = "http://172.20.0.5:5004"
origenPeticion ="comprasVentas"
url_tienda = "http://172.20.0.2:5002"

@method
def registrar_venta(carrito,origen=None):
    ventas_registradas.append(carrito)
    print(f"Venta nueva desde: {origen}")
    print(ventas_registradas)
    print("Enviando a contabilidad")

    try:
        pedir_generar_recibo(carrito,origen)
        pedir_recibo()
        #enviar_tienda()
        
    except Exception as e:
        print(f"Error{e}")
    
    mensaje = {
        "mensaje": factura_actual,
    }

    return Success(mensaje)


@method
def pedir_generar_recibo(carrito,origen):

    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
                    "carrito":carrito,
                    "origen":origen
                   },
        "id": 1
    }
    try:
        response = requests.post(url_contabilidad, json=payload, timeout=5)
        data = response.json()
        print(f"Respuesta de contabilidad: {data['result']['mensaje']}")
    except:
        print("Error")


@method
def pedir_recibo():
    payload = {
        "jsonrpc": "2.0",
        "method": "recibir_factura",
        "params": {"origen":origenPeticion},
        "id": 1
    }

    try:
        response = requests.post(url_contabilidad, json=payload, timeout=5)
        print("Recibiendo factura...")
        data = response.json()
        factura_actual["recibo"] = data
        print(f"Factura: -> {data}")

    except Exception as e:
        print("Error")
    

URL_PROVEEDORES = "http://172.20.0.6:5005"  # Endpoint de Proveedores

def notificar_proveedores(compras_realizadas, origen):
    """
    Envía la compra registrada a Proveedores para que ellos procesen el pedido.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_compra",
        "params": {
            "productos": compras_realizadas,
            "origen": origen
        },
        "id": 1
    }
    try:
        response = requests.post(URL_PROVEEDORES, json=payload, timeout=5)
        data = response.json()
        print(f"Proveedores notificados: {data['result']['mensaje']}")
    except Exception as e:
        print(f"Error notificando a Proveedores: {e}")


@method
def registrar_compra(productos, origen=None):
    print(f"\nNueva compra registrada desde {origen}")
    compras_realizadas = []

    for p in productos:
        cantidad_a_comprar = 5
        print(f"- {p['nombre']} (Stock actual: {p['stock']}) → Comprando {cantidad_a_comprar} unidades")
        compras_realizadas.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "categoria": p["categoria"],
            "precio": p["precio"],
            "stock_actual": p["stock"],
            "comprar": cantidad_a_comprar
        })

    print("\nResumen de la compra registrada:")
    for c in compras_realizadas:
        print(f"{c['nombre']}: comprando {c['comprar']} unidades (stock actual {c['stock_actual']})")

    # Enviar la compra a contabilidad
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
            "carrito": compras_realizadas,
            "origen": origen
        },
        "id": 1
    }

    try:
        response = requests.post(url_contabilidad, json=payload, timeout=5)
        data = response.json()
        print(f"Respuesta de Contabilidad: {data['result']['mensaje']}")
        pedir_recibo()
        notificar_proveedores(compras_realizadas, origen)

    except Exception as e:
        print(f"Error enviando factura a Contabilidad: {e}")

    mensaje = {
        "mensaje": "Compra registrada y enviada a contabilidad",
        "productos": compras_realizadas
    }

    return Success(mensaje)





if __name__ == "__main__":
    print("Compras ventas corriendo")
    serve("172.20.0.4",5003)