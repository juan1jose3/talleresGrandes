"""
Módulo de Modelo de Facturas
============================

Este módulo contiene la lógica de negocio para la gestión de facturas,
incluyendo cálculos de impuestos y almacenamiento en memoria.

Constantes:
    IVA (float): Impuesto al Valor Agregado (19%)
    IMPUESTO_EXTRA (float): Impuesto adicional (4%)


Fecha: 2025-10-21
"""

from datetime import datetime
from typing import List, Dict, Optional

# Constantes de impuestos
IVA = 0.19
IMPUESTO_EXTRA = 0.04

# Almacenamiento en memoria de facturas
facturas_guardadas: List[Dict] = []


class FacturaModel:
    """
    Modelo de datos y lógica de negocio para facturas.
    
    Esta clase maneja la creación, cálculo y almacenamiento de facturas
    en el sistema de contabilidad.
    
    Attributes:
        facturas_guardadas (List[Dict]): Lista de todas las facturas registradas
    """
    
    @staticmethod
    def calcular_subtotal(carrito: List[Dict]) -> float:
        """
        Calcula el subtotal de un carrito de productos.
        
        Args:
            carrito (List[Dict]): Lista de productos con estructura:
                {
                    "id": int,
                    "nombre": str,
                    "precio": float,
                    "comprar": int
                }
        
        Returns:
            float: Subtotal calculado (precio * cantidad) de todos los productos
        
        Example:
            >>> carrito = [{"precio": 100.0, "comprar": 2}]
            >>> FacturaModel.calcular_subtotal(carrito)
            200.0
        """
        return sum(p.get("precio", 0) * p.get("comprar", 1) for p in carrito)
    
    @staticmethod
    def calcular_impuestos(subtotal: float) -> Dict[str, float]:
        """
        Calcula los impuestos aplicables sobre un subtotal.
        
        Args:
            subtotal (float): Monto base sobre el cual calcular impuestos
        
        Returns:
            Dict[str, float]: Diccionario con estructura:
                {
                    "iva": float,           # IVA calculado (19%)
                    "impuesto_extra": float, # Impuesto adicional (4%)
                    "total": float          # Suma de subtotal + impuestos
                }
        
        Example:
            >>> FacturaModel.calcular_impuestos(1000.0)
            {'iva': 190.0, 'impuesto_extra': 40.0, 'total': 1230.0}
        """
        iva_total = round(subtotal * IVA, 2)
        impuesto_extra = round(subtotal * IMPUESTO_EXTRA, 2)
        total = round(subtotal + iva_total + impuesto_extra, 2)
        
        return {
            "iva": iva_total,
            "impuesto_extra": impuesto_extra,
            "total": total
        }
    
    @staticmethod
    def crear_factura(carrito: List[Dict], origen: str) -> Dict:
        """
        Crea una factura completa con todos los cálculos necesarios.
        
        Args:
            carrito (List[Dict]): Lista de productos a facturar
            origen (str): Origen de la transacción ("tienda", "proveedores", etc.)
        
        Returns:
            Dict: Factura completa con estructura:
                {
                    "fecha": str,           # Formato: "YYYY-MM-DD HH:MM:SS"
                    "origen": str,          # Origen de la transacción
                    "productos": List[Dict], # Lista de productos
                    "subtotal": float,      # Subtotal sin impuestos
                    "iva": float,           # IVA (19%)
                    "impuesto_extra": float,# Impuesto adicional (4%)
                    "total": float          # Total a pagar
                }
        
        Example:
            >>> carrito = [{"id": 1, "nombre": "Silla", "precio": 150.0, "comprar": 2}]
            >>> factura = FacturaModel.crear_factura(carrito, "tienda")
            >>> factura["total"]
            369.0
        
        Note:
            La factura se almacena automáticamente en facturas_guardadas
        """
        subtotal = FacturaModel.calcular_subtotal(carrito)
        impuestos = FacturaModel.calcular_impuestos(subtotal)
        
        factura = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origen": origen,
            "productos": carrito,
            "subtotal": subtotal,
            "iva": impuestos["iva"],
            "impuesto_extra": impuestos["impuesto_extra"],
            "total": impuestos["total"]
        }
        
        facturas_guardadas.append(factura)
        return factura
    
    @staticmethod
    def obtener_todas_facturas() -> List[Dict]:
        """
        Obtiene todas las facturas registradas en el sistema.
        
        Returns:
            List[Dict]: Lista de todas las facturas almacenadas
        
        Example:
            >>> facturas = FacturaModel.obtener_todas_facturas()
            >>> len(facturas)
            5
        """
        return facturas_guardadas
    
    @staticmethod
    def obtener_ultima_factura() -> Optional[Dict]:
        """
        Obtiene la factura más reciente registrada.
        
        Returns:
            Optional[Dict]: La última factura registrada, o None si no hay facturas
        
        Example:
            >>> factura = FacturaModel.obtener_ultima_factura()
            >>> factura["origen"]
            'tienda'
        """
        return facturas_guardadas[-1] if facturas_guardadas else None
    
    @staticmethod
    def determinar_tipo_operacion(origen: str) -> str:
        """
        Determina el tipo de operación según el origen de la transacción.
        
        Args:
            origen (str): Origen de la transacción
        
        Returns:
            str: Tipo de operación ("compra" o "venta")
                - "compra": Cuando se compra a proveedores (suma stock)
                - "venta": Cuando se vende a clientes (resta stock)
        
        Example:
            >>> FacturaModel.determinar_tipo_operacion("proveedores")
            'compra'
            >>> FacturaModel.determinar_tipo_operacion("tienda")
            'venta'
        """
        return "compra" if origen == "proveedores" else "venta"