"""
Módulo de Controlador de Facturas
=================================

Este módulo actúa como intermediario entre el modelo y la vista,
manejando la lógica de aplicación y comunicación con otros servicios.

Fecha: 2025-10-21
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
    """
    
    URL_MIDDLEWARE = "http://192.168.1.10:5010"
    
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
        
        #Notificar al inventario
        #FacturaController.notificar_inventario(carrito, tipo_operacion)
        
        return Success({"mensaje": "Factura generada"})
    
    
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