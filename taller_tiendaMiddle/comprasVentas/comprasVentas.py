from jsonrpcserver import method, serve, Success
import requests
import json

ventas_registradas = []
factura_actual = {}
url_contabilidad = "http://192.168.1.5:5004"
origenPeticion = "comprasVentas"
url_tienda = "http://192.168.1.3:5002"
URL_PROVEEDORES = "http://192.168.1.6:5005"

@method
def registrar_venta(carrito, origen=None):
    ventas_registradas.append(carrito)
    print(f"Venta nueva desde: {origen}")
    print(ventas_registradas)
    print("Enviando a contabilidad")
    
    try:
        pedir_generar_recibo(carrito, origen)
        pedir_recibo()
        #enviar_tienda()
        
    except Exception as e:
        print(f"Error{e}")
    
    mensaje = {
        "mensaje": factura_actual,
    }
    
    return Success(mensaje)


@method
def pedir_generar_recibo(carrito, origen):
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
            "carrito": carrito,
            "origen": origen
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
        "params": {"origen": origenPeticion},
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


def notificar_proveedores(compras_realizadas, origen):
    """
    Envía la compra registrada a Proveedores de forma asíncrona (fire-and-forget).
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
        # CLAVE: timeout bajo y no procesar respuesta detalladamente
        requests.post(URL_PROVEEDORES, json=payload, timeout=1)
        print("Notificación enviada a Proveedores (sin esperar respuesta)")
    except requests.exceptions.Timeout:
        print("Timeout notificando a Proveedores (normal, ya procesaron)")
    except Exception as e:
        print(f"Error notificando a Proveedores: {e}")


@method
def registrar_compra(productos, origen=None):
    """
    Procesa compras de productos con bajo stock.
    Recibe productos desde Proveedores, crea órdenes de compra y genera facturas.
    """
    print(f"\nNueva compra registrada desde {origen}")
    compras_realizadas = []

    # Crear órdenes de compra con cantidad fija de 5 unidades
    for p in productos:
        cantidad_a_comprar = 5
        print(f"  - {p['nombre']} (Stock actual: {p['stock']}) → Comprando {cantidad_a_comprar} unidades")
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
        print(f"   {c['nombre']}: comprando {c['comprar']} unidades (stock actual {c['stock_actual']})")

    # Enviar la compra a contabilidad para generar factura
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
        
        # Obtener la factura generada
        pedir_recibo()
        
        # Notificar a proveedores (fire-and-forget) para que registren la compra
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
    serve("192.168.1.4", 5003)