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
    """Flujo de ventas desde la tienda"""
    productos = cargar_productos()
    enviar_productos_tienda(productos)
    enviar_compras_ventas()
    
    if validar_stock_disponible():
        pedir_genrar_factura()
        factura = pedir_recibir_factura()
        enviar_factura_tienda(factura)
    else:
        print("Operación cancelada: Stock insuficiente")
    
    return Success()



def cargar_productos():
    """Carga productos desde inventario (para ventas)"""
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
    return productos


def enviar_productos_tienda(productos):
    """Envía productos a la tienda para que el usuario seleccione"""
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {
            "origen": origen,
            "productos": productos["result"]
        },
        "id": 1
    }
    print("Enviando productos a tienda .....")
    try:
        response = requests.post(URL_TIENDA, json=payload, timeout=None)
        message = response.json()
        carrito_compras["productos"] = message["result"]["productos"]
        print(f"Carrito guardado: {len(carrito_compras['productos'])} productos")
    except Exception as e:
        print(f"Error en tienda: {e}")


def enviar_compras_ventas():
    """Registra venta en ComprasVentas"""
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_venta",
        "params": {
            "origen": origen,
            "carrito": carrito_compras
        },
        "id": 1
    }
    print("Enviando a comprasVentas")
    response = requests.post(URL_COMPRASVENTAS, json=payload, timeout=5)
    print(f"Mensaje comprasVentas: {response.json()}")


def validar_stock_disponible():
    """Valida si hay stock suficiente antes de vender"""
    carrito = carrito_compras["productos"]
    
    payload = {
        "jsonrpc": "2.0",
        "method": "validar_stock",
        "params": {"carrito": carrito},
        "id": 1
    }
    
    print(f"\n{'='*50}")
    print("Validando stock antes de facturar...")
    print(f"{'='*50}")
    
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        resultado = response.json()
        
        disponible = resultado.get('result', {}).get('disponible', False)
        mensaje = resultado.get('result', {}).get('mensaje', '')
        
        if disponible:
            print(f"{mensaje}")
            return True
        else:
            print(f"{mensaje}")
            productos_sin_stock = resultado.get('result', {}).get('productos_sin_stock', [])
            for p in productos_sin_stock:
                print(f"   - {p['nombre']}: disponible {p['stock_actual']}, solicitado {p['cantidad_solicitada']}")
            return False
            
    except Exception as e:
        print(f"Error validando stock: {e}")
        return False


def pedir_genrar_factura():
    """Genera factura de venta y actualiza inventario"""
    carrito = carrito_compras["productos"]
    
    print(f"\n{'='*50}")
    print("Generando factura de venta...")
    print(f"{'='*50}")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
            "origen": origen,
            "carrito": carrito
        },
        "id": 1
    }
    
    try:
        response = requests.post(URL_CONTABILIDAD, json=payload, timeout=15)
        resultado = response.json()
        print(f"{resultado.get('result', {}).get('mensaje', 'Factura generada')}")
        
        # Actualizar inventario (RESTA stock porque es venta)
        notificar_inventario_modificacion(carrito, tipo_operacion="venta")
        
    except Exception as e:
        print(f"Error generando factura: {e}")


def notificar_inventario_modificacion(carrito, tipo_operacion="venta"):
    """
    Actualiza el stock en inventario.
    tipo_operacion: "venta" (resta) o "compra" (suma)
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "actualizar_inventario",
        "params": {
            "carrito": carrito,
            "tipo_operacion": tipo_operacion
        },
        "id": 1
    }
    
    accion = "Restando" if tipo_operacion == "venta" else "Sumando"
    print(f"\n{accion} stock en inventario...")
    
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=5)
        data = response.json()
        mensaje = data.get('result', {}).get('mensaje', 'OK')
        print(f"{mensaje}")
        return data
    except Exception as e:
        print(f"Error actualizando inventario: {e}")
        return None


def pedir_recibir_factura():
    """Obtiene la última factura generada"""
    payload = {
        "jsonrpc": "2.0",
        "method": "recibir_factura",
        "params": {"origen": origen},
        "id": 1
    }
    
    print(f"\n{'='*50}")
    print("Obteniendo factura generada...")
    print(f"{'='*50}")
    
    try:
        response = requests.post(URL_CONTABILIDAD, json=payload, timeout=5)
        resultado = response.json()
        
        factura = resultado.get('result', {}).get('factura', None)
        
        if factura:
            print(f"Factura recibida:")
            print(f"Fecha: {factura.get('fecha')}")
            print(f"Total: ${factura.get('total', 0):.2f}")
        
        return resultado
        
    except Exception as e:
        print(f"Error obteniendo factura: {e}")
        return None


def enviar_factura_tienda(factura):
    payload = {
        "jsonrpc": "2.0",
        "method": "leer_factura",
        "params": {
                    "factura":factura,
                    "origen": origen,
                   },
        "id": 1
    }

    response = requests.post(URL_TIENDA,json=payload,timeout=5)
    print(f"Respuesta de tienda: {response.json()}")


     





# proveedores

@method
def middlewareControllerProveedores(origen="proveedores"):
    """
    Flujo de compras a proveedores (reabastecimiento).
    
    1. Consulta productos con bajo stock
    2. Registra compra en ComprasVentas
    3. Genera factura en Contabilidad
    4. Actualiza inventario (SUMA stock)
    5. Confirma a Proveedores
    """
    print("\n" + "="*60)
    print("MIDDLEWARE: Iniciando proceso de reabastecimiento")
    print("="*60)
    
    # 1. Consultar productos con bajo stock
    productos_bajo_stock = consultar_productos_bajo_stock()
    
    if not productos_bajo_stock:
        print("No hay productos con bajo stock")
        return Success({
            "mensaje": "No se requiere reabastecimiento",
            "productos_comprados": []
        })
    
    # 2. Registrar compra en ComprasVentas
    registrar_compra_comprasventas(productos_bajo_stock)
    
    # 3. Generar factura (origen="proveedores" para que sea compra)
    generar_factura_compra(productos_bajo_stock)
    
    # 4. Actualizar inventario (SUMA stock)
    notificar_inventario_modificacion(productos_bajo_stock, tipo_operacion="compra")
    
    # 5. Confirmar a Proveedores
    confirmar_a_proveedores(productos_bajo_stock)
    
    return Success({
        "mensaje": "Reabastecimiento completado exitosamente",
        "productos_comprados": productos_bajo_stock
    })


def consultar_productos_bajo_stock():
    """
    Consulta inventario y filtra productos con stock <= 5.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "cargar_productos",
        "params": {"origen": "proveedores"},
        "id": 1
    }
    
    print("\nConsultando productos con bajo stock...")
    
    try:
        response = requests.post(URL_INVENTARIO, json=payload, timeout=10)
        data = response.json()
        
        productos_bajo_stock = []
        
        print("\nProductos con stock ≤ 5:")
        print("-"*60)
        
        for producto in data["result"]["productos"]:
            if producto["stock"] <= 5:
                # Calcular cantidad a comprar (llevar a 20 unidades)
                cantidad_a_comprar = 20 - producto['stock']
                
                print(f"{producto['nombre']}")
                print(f"Stock actual: {producto['stock']} → Comprar: {cantidad_a_comprar}")
                
                productos_bajo_stock.append({
                    "id": producto["id"],
                    "nombre": producto["nombre"],
                    "categoria": producto["categoria"],
                    "precio": producto["precio"],
                    "stock": producto["stock"],
                    "comprar": cantidad_a_comprar
                })
        
        print(f"\n{len(productos_bajo_stock)} productos necesitan reabastecimiento")
        return productos_bajo_stock
        
    except Exception as e:
        print(f"Error consultando inventario: {e}")
        return []


def registrar_compra_comprasventas(productos):
    """
    Registra la compra en el servicio de ComprasVentas.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "registrar_compra",
        "params": {
            "productos": productos,
            "origen": "proveedores"
        },
        "id": 1
    }
    
    print("\nRegistrando compra en ComprasVentas...")
    
    try:
        response = requests.post(URL_COMPRASVENTAS, json=payload, timeout=5)
        data = response.json()
        print(f"{data.get('result', {}).get('mensaje', 'Compra registrada')}")
    except Exception as e:
        print(f"Error registrando en ComprasVentas: {e}")


def generar_factura_compra(productos):
    """
    Genera factura de compra en Contabilidad.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "generar_factura",
        "params": {
            "carrito": productos,
            "origen": "proveedores"  
        },
        "id": 1
    }
    
    print("\nGenerando factura de compra...")
    
    try:
        response = requests.post(URL_CONTABILIDAD, json=payload, timeout=15)
        resultado = response.json()
        print(f"{resultado.get('result', {}).get('mensaje', 'Factura generada')}")
    except Exception as e:
        print(f"Error generando factura: {e}")


def confirmar_a_proveedores(productos):
    """
    Confirma al servicio de Proveedores que la compra fue procesada.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "confirmar_recepcion_compra",
        "params": {
            "productos": productos,
            "origen": "middleware"
        },
        "id": 1
    }
    
    print("\nConfirmando recepción a Proveedores...")
    
    try:
        response = requests.post(URL_PROVEEDORES, json=payload, timeout=5)
        print("Proveedores confirmado")
    except Exception as e:
        print(f"No se pudo confirmar a Proveedores: {e}")





if __name__ == "__main__":
    print("="*60)
    print("MiddleWare corriendo en 192.168.1.10:5010")
    print("="*60)
    print("\nEndpoints:")
    print("  - middleWareController() → Flujo de ventas")
    print("  - middlewareControllerProveedores() → Flujo de compras")
    print("="*60 + "\n")
    serve("192.168.1.10", 5010)