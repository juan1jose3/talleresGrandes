"""
Módulo de Vista de Facturas
===========================

Este módulo maneja la presentación y formato de la información de facturas
en la consola y logs del sistema.

Fecha: 2025-10-21
"""

from typing import List, Dict, Optional
import json


class FacturaView:
    """
    Vista para presentar información de facturas en consola.
    
    Esta clase es responsable de formatear y mostrar información
    de facturas de manera legible para logs y debugging.
    """
    
    @staticmethod
    def mostrar_factura_generada(factura: Dict, origen: str) -> None:
        """
        Muestra en consola la información de una factura recién generada.
        
        Args:
            factura (Dict): Factura a mostrar
            origen (str): Origen de la transacción
        
        Returns:
            None
        
        Example:
            >>> factura = {"total": 1476.0, "fecha": "2025-10-21 20:50:16"}
            >>> FacturaView.mostrar_factura_generada(factura, "tienda")
            Factura generada desde 'tienda'
            Total: $1476.0
        """
        print(f"\n{'='*60}")
        print(f"Factura generada desde '{origen}'")
        print(f"{'='*60}")
        print(f"Fecha: {factura['fecha']}")
        print(f"Subtotal: ${factura['subtotal']:.2f}")
        print(f"IVA (19%): ${factura['iva']:.2f}")
        print(f"Impuesto Extra (4%): ${factura['impuesto_extra']:.2f}")
        print(f"TOTAL: ${factura['total']:.2f}")
        print(f"{'='*60}\n")
    
    @staticmethod
    def mostrar_historial_facturas(facturas: List[Dict]) -> None:
        """
        Muestra el historial completo de facturas registradas.
        
        Args:
            facturas (List[Dict]): Lista de facturas a mostrar
        
        Returns:
            None
        
        Example:
            >>> facturas = [
            ...     {"fecha": "2025-10-21 10:00:00", "total": 100.0, "origen": "tienda"},
            ...     {"fecha": "2025-10-21 11:00:00", "total": 200.0, "origen": "proveedores"}
            ... ]
            >>> FacturaView.mostrar_historial_facturas(facturas)
            ===== HISTORIAL DE FACTURAS RADICADAS =====
            1. Fecha: 2025-10-21 10:00:00 | Total: $100.0 | Origen: tienda
            2. Fecha: 2025-10-21 11:00:00 | Total: $200.0 | Origen: proveedores
        """
        print("\n" + "="*60)
        print("HISTORIAL DE FACTURAS RADICADAS")
        print("="*60)
        
        if not facturas:
            print("No hay facturas registradas.")
        else:
            for i, f in enumerate(facturas, start=1):
                print(f"{i}. Fecha: {f['fecha']} | Total: ${f['total']:.2f} | Origen: {f['origen']}")
        
        print("="*60 + "\n")
    
    @staticmethod
    def mostrar_solicitud_factura(origen: str) -> None:
        """
        Muestra en consola que un servicio solicitó una factura.
        
        Args:
            origen (str): Servicio que solicitó la factura
        
        Returns:
            None
        
        Example:
            >>> FacturaView.mostrar_solicitud_factura("comprasVentas")
            'comprasVentas' solicitó la factura actual
        """
        print(f"\n'{origen}' solicitó la factura actual")
    
    @staticmethod
    def mostrar_error(mensaje: str, detalle: Exception = None) -> None:
        """
        Muestra un mensaje de error en consola.
        
        Args:
            mensaje (str): Mensaje de error principal
            detalle (Exception, optional): Excepción que causó el error
        
        Returns:
            None
        
        Example:
            >>> FacturaView.mostrar_error("Error al conectar", TimeoutError("Timeout"))
            Error al conectar
            Detalle: Timeout
        """
        print(f"\n{mensaje}")
        if detalle:
            print(f"Detalle: {detalle}")
    
    @staticmethod
    def mostrar_notificacion_inventario(mensaje: str) -> None:
        """
        Muestra resultado de notificación a inventario.
        
        Args:
            mensaje (str): Mensaje de respuesta del servicio de inventario
        
        Returns:
            None
        
        Example:
            >>> FacturaView.mostrar_notificacion_inventario("Inventario actualizado")
            Inventario actualizado
        """
        print(f"✓ {mensaje}")