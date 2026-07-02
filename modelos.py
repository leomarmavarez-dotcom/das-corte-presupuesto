"""Modelos de datos compartidos entre catálogo, plantillas, motor de corte,
inventario y presupuesto.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PiezaAluminio:
    """Una necesidad de corte de aluminio: 'cantidad' piezas de 'longitud_mm'
    del perfil 'perfil_codigo', para el módulo 'modulo' de la ventana 'ventana_id'.
    """
    perfil_codigo: str
    descripcion: str
    longitud_mm: float
    cantidad: int
    ventana_id: str
    modulo: str

    def longitudes_individuales(self) -> list[float]:
        return [self.longitud_mm] * self.cantidad


@dataclass
class PiezaVidrio:
    tipo: str
    espesor_mm: float
    ancho_mm: float
    alto_mm: float
    cantidad: int
    ventana_id: str
    modulo: str
    descripcion: str = ""


@dataclass
class PiezaHerraje:
    codigo: str
    descripcion: str
    cantidad: int
    ventana_id: str
    modulo: str = ""


@dataclass
class DespieceVentana:
    """Resultado de aplicar una plantilla: todas las piezas necesarias para un trabajo."""
    ventana_id: str
    plantilla: str
    ancho_total_mm: float
    alto_total_mm: float
    piezas_aluminio: list[PiezaAluminio] = field(default_factory=list)
    piezas_vidrio: list[PiezaVidrio] = field(default_factory=list)
    piezas_herrajes: list[PiezaHerraje] = field(default_factory=list)
