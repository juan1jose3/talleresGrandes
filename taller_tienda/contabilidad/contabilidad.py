from jsonrpcserver import method, serve, Success
import requests
import json
from datetime import datetime

facturas_guardadas = []
URL_INVENTARIO = "http://172.20.0.3:5001"
IVA = 0.19
IMPUESTO_EXTRA = 0.04

@method
def generar_factura(carrito, origen=None):
    print(f"Factura generada desde {origen}: {carrito}")

    subtotal = sum(p.get("precio", 0) * p.get("comprar", 1) for p in carrito)

    iva_total = round(subtotal * IVA, 2)
    impuesto_extra = round(subtotal * IMPUESTO_EXTRA, 2)
    total = round(subtotal + iva_total + impuesto_extra, 2)

    factura = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "origen": origen,
        "productos": carrito,
        "subtotal": subtotal,
        "iva": iva_total,
        "impuesto_extra": impuesto_extra,
        "total": total
    }

    facturas_guardadas.append(factura)
    print(f"Factura registrada correctamente. Total: {total}")

    
    notificar_inventario(carrito)

    return Success({"mensaje": "Factura generada", "factura": factura})




def notificar_inventario(carrito):
    """
    Hace la petición a Inventario para que actualice el stock.
    Contabilidad solo notifica, no actualiza directamente.
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "actualizar_inventario",
            "params": {"carrito": carrito},
            "id": 1
        }
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        data = response.json()
        print(f"Inventario actualizado: {data['result']['mensaje']}")
    except Exception as e:
        print(f"Error notificando a Inventario: {e}")

@method
def recibir_factura(origen=None):
    """
    Devuelve la factura más reciente, pero imprime todas las registradas
    """
    print(f"\n{origen} solicitó la factura actual")
    if not facturas_guardadas:
        print("No hay facturas registradas aún.")
        return Success({"factura": None})


    factura_actual = facturas_guardadas[-1]

    
    print("\n===== HISTORIAL DE FACTURAS RADICADAS =====")
    for i, f in enumerate(facturas_guardadas, start=1):
        print(f"{i}. Fecha: {f['fecha']} | Total: {f['total']} | Origen: {f['origen']}")
    print("============================================\n")

    return Success({"factura": factura_actual})


if __name__ == "__main__":
    print("Servicio de Contabilidad corriendo en 172.20.0.5:5004")
    serve("172.20.0.5", 5004)
