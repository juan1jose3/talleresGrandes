"""
Módulo de Controlador de Facturas
=================================

Este módulo actúa como intermediario entre el modelo y la vista,
manejando la lógica de aplicación y comunicación con otros servicios.



IMPORTANTE - Comunicación con Inventario
----------------------------------------
Este módulo está configurado para usar XML-RPC para comunicarse con el servicio
de Inventario.
"""
import xmlrpc.client
import requests
from typing import Dict, Optional
from jsonrpcserver import Success
import json
from model.factura_model import FacturaModel
from view.factura_view import FacturaView
import xml.etree.ElementTree as ET


class FacturaController:
    """
    Controlador para gestionar operaciones de facturas.
    
    Esta clase coordina las operaciones entre el modelo de facturas,
    la vista y los servicios externos (como Inventario).
    
    Attributes:
        URL_INVENTARIO (str): URL del servicio de inventario

    También es muy importante aclarar que hay que cambiar URL_INVENTARIO a la ip que vaya a usar dicho componente,
    La presente ip muestra un ejemplo con una red local docker.
    """
    
    URL_INVENTARIO = "http://10.8.4.196:5000"
    
    @staticmethod
    def generar_factura(carrito: list, origen: str = None) -> Success:
        """
        Genera una factura completa y notifica al inventario.
        
        Este método es el punto de entrada principal para generar facturas.
        Realiza los siguientes pasos:
        1. Crea la factura con cálculos de impuestos
        2. Muestra la factura en consola
        3. Determina si es compra o venta
        4. Notifica al inventario para actualizar stock
        
        Args:
            carrito (list): Lista de productos a facturar. Cada producto debe tener:
                - id (int): Identificador del producto
                - nombre (str): Nombre del producto
                - precio (float): Precio unitario
                - comprar (int): Cantidad a comprar
            origen (str, optional): Origen de la transacción
        
        Returns:
            Success: Respuesta JSON-RPC exitosa con estructura:
                {
                    "mensaje": "Factura generada",
                    "factura": {
                        "fecha": str,
                        "origen": str,
                        "productos": list,
                        "subtotal": float,
                        "iva": float,
                        "impuesto_extra": float,
                        "total": float
                    }
                }
        
        Raises:
            Exception: Si hay error al notificar al inventario
        
        Example:
            >>> carrito = [
            ...     {"id": 1, "nombre": "Sofá", "precio": 1200.0, "comprar": 1}
            ... ]
            >>> resultado = FacturaController.generar_factura(carrito, "tienda")
            >>> resultado.result["factura"]["total"]
            1476.0
        
        Note:
            - Si origen es "proveedores", el inventario SUMA stock (compra)
            - Para cualquier otro origen, el inventario RESTA stock (venta)
        """
        # Crear factura usando el modelo
        factura = FacturaModel.crear_factura(carrito, origen)
        
        # Mostrar factura en consola
        FacturaView.mostrar_factura_generada(factura, origen)
        
        # Determinar tipo de operación (compra/venta)
        tipo_operacion = FacturaModel.determinar_tipo_operacion(origen)
        
        # Notificar al inventario
        FacturaController.notificar_inventario(carrito, tipo_operacion)
        
        return Success({"mensaje": "Factura generada", "factura": factura})
    
    @staticmethod
    def notificar_inventario(carrito: list, tipo_operacion: str = "venta") -> None:
        """
        Notifica al servicio de Inventario vía XML-RPC para actualizar el stock.
        
        IMPORTANTE - Protocolo de Comunicación:
        ----------------------------------------
        Este método usa XML-RPC por defecto. Si el servicio de Inventario usa JSON-RPC,
        debe comentar la implementación XML-RPC y descomentar el código JSON-RPC al final.
        
        Descripción:
        -----------
        Conecta con el servicio de Inventario mediante XML-RPC y actualiza
        el stock de cada producto en el carrito. Ajusta las cantidades según el tipo
        de operación (suma para compras, resta para ventas).
        
        Args:
            carrito (list): Lista de productos con cantidades. Cada item debe contener:
                - id (int): Identificador del producto
                - comprar (int): Cantidad del producto
            tipo_operacion (str, optional): Tipo de operación:
                - "venta": Resta stock (venta a cliente)
                - "compra": Suma stock (compra a proveedor)
                Default: "venta"
        
        Returns:
            None
        
        Side Effects:
            - Crea conexión XML-RPC con URL_INVENTARIO
            - Llama al método remoto 'actualizar_inventario' por cada producto
            - Imprime resultado en consola para cada actualización
            - Muestra notificaciones vía FacturaView
        
        Raises:
            Exception: Si hay error de conexión o comunicación con el servicio
        
        Example - Uso con XML-RPC (implementación actual):
            >>> carrito = [
            ...     {"id": 1, "nombre": "Silla", "comprar": 2},
            ...     {"id": 5, "nombre": "Mesa", "comprar": 1}
            ... ]
            >>> FacturaController.notificar_inventario(carrito, "venta")
            [FacturaController] Actualizando stock ID 1 (venta)...
            Inventario actualizado para producto 1
            [FacturaController] Actualizando stock ID 5 (venta)...
            Inventario actualizado para producto 5
        
        Technical Details - XML-RPC:
            - Usa xmlrpc.client.ServerProxy para crear el cliente XML-RPC
            - Envía diccionario con estructura:
                {
                    "producto_id": int,
                    "cantidad_cambio": int (negativo para ventas, positivo para compras)
                }
            - Procesa productos secuencialmente (no en lote)
            - Timeout por defecto de xmlrpc.client (sin límite explícito)
        
        Technical Details - JSON-RPC (implementación alternativa comentada):
            - Envía payload JSON-RPC 2.0 con estructura:
                {
                    "jsonrpc": "2.0",
                    "method": "actualizar_inventario",
                    "params": {
                        "carrito": list,
                        "tipo_operacion": str
                    },
                    "id": 1
                }
            - Timeout de 5 segundos para la petición HTTP
            - Envía todos los productos en una sola petición (modo lote)
        
        Note:
            - Los errores se capturan y muestran pero no detienen la ejecución
            - Ver código comentado al final del método para implementación JSON-RPC
            - La elección entre XML-RPC y JSON-RPC debe coincidir con lo que este manejando el
            inventario. 
        """
        try:
            # Crear proxy XML-RPC
            inventario_proxy = xmlrpc.client.ServerProxy(FacturaController.URL_INVENTARIO)

            # Recorrer carrito y enviar cada producto al inventario
            for item in carrito:
                producto_id = item.get("id")
                cantidad = item.get("comprar", 0)

                # Ajustar cantidad según tipo de operación
                if tipo_operacion == "venta":
                    cantidad_cambio = -abs(cantidad)
                else:
                    cantidad_cambio = abs(cantidad)

                datos_actualizacion = {
                    "producto_id": producto_id,
                    "cantidad_cambio": cantidad_cambio
                }

                print(f"[FacturaController] Actualizando stock ID {producto_id} ({tipo_operacion})...")
                resp = inventario_proxy.actualizar_inventario(datos_actualizacion)

                # Mostrar respuesta en consola y en FacturaView
                print(json.dumps(resp, indent=2,ensure_ascii=False))
                FacturaView.mostrar_notificacion_inventario(
                    f"Inventario actualizado para producto {producto_id}"
                )

        except Exception as e:
            FacturaView.mostrar_error("Error notificando a Inventario", e)


        
        # CÓDIGO ALTERNATIVO PARA JSON-RPC
    
        # Si el servicio de Inventario está usando JSON-RPC en lugar de XML-RPC,
        # comente todo el código XML-RPC arriba y descomente el siguiente bloque:
    
        """
        Notifica al servicio de Inventario vía JSON-RPC para actualizar el stock.
        
        IMPORTANTE: Este código está comentado. Solo descomentar si el servicio de 
        Inventario usa JSON-RPC en lugar de XML-RPC.
        
        Este método envía una petición JSON-RPC al microservicio de Inventario
        para que actualice el stock de productos según el tipo de operación.
        
        Args:
            carrito (list): Lista de productos con cantidades
            tipo_operacion (str, optional): Tipo de operación:
                - "venta": Resta stock (venta a cliente)
                - "compra": Suma stock (compra a proveedor)
                Default: "venta"
        
        Returns:
            None
        
        Side Effects:
            - Envía petición HTTP POST a URL_INVENTARIO
            - Imprime resultado en consola vía FacturaView
        
        Example:
            >>> carrito = [{"id": 1, "nombre": "Silla", "comprar": 2}]
            >>> FacturaController.notificar_inventario(carrito, "venta")
            Inventario actualizado
        
        Technical Details:
            - Envía payload JSON-RPC 2.0 con estructura:
                {
                    "jsonrpc": "2.0",
                    "method": "actualizar_inventario",
                    "params": {
                        "carrito": list,
                        "tipo_operacion": str
                    },
                    "id": 1
                }
            - Timeout de 5 segundos para la petición HTTP
        
        Note:
            - Los errores se capturan y muestran pero no detienen la ejecución
            - Requiere que el endpoint acepte JSON-RPC 2.0
        """
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
        
        
        try:
            response = requests.post(
                FacturaController.URL_INVENTARIO,
                json=payload,
                timeout=5
            )
            data = response.json()
            FacturaView.mostrar_notificacion_inventario(data['result']['mensaje'])
        
        except Exception as e:
            FacturaView.mostrar_error("Error notificando a Inventario", e)
        """
    
    @staticmethod
    def recibir_factura(origen: str = None) -> Success:
        """
        Devuelve la factura más reciente y muestra el historial completo.
        
        Este método recupera la última factura generada y muestra
        en consola un historial de todas las facturas registradas.
        
        Args:
            origen (str, optional): Servicio que solicita la factura
        
        Returns:
            Success: Respuesta JSON-RPC exitosa con estructura:
                {
                    "factura": Dict | None  # Última factura o None si no hay
                }
        
        Example:
            >>> resultado = FacturaController.recibir_factura("comprasVentas")
            'comprasVentas' solicitó la factura actual
            ===== HISTORIAL DE FACTURAS RADICADAS =====
            1. Fecha: 2025-10-21 20:50:16 | Total: $1476.0 | Origen: tienda
            >>> resultado.result["factura"]["total"]
            1476.0
        
        Note:
            - Si no hay facturas registradas, retorna {"factura": None}
            - El historial completo se muestra en consola
        """
        FacturaView.mostrar_solicitud_factura(origen)
        
        # Obtener última factura
        factura_actual = FacturaModel.obtener_ultima_factura()
        
        if not factura_actual:
            print("No hay facturas registradas aún.")
            return Success({"factura": None})
        
        # Mostrar historial completo
        todas_facturas = FacturaModel.obtener_todas_facturas()
        FacturaView.mostrar_historial_facturas(todas_facturas)
        
        return Success({"factura": factura_actual})