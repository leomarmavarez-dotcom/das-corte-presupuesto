from __future__ import annotations

from abc import ABC, abstractmethod

from modelos import DespieceVentana


class PlantillaVentana(ABC):
    """Contrato que debe cumplir cualquier plantilla paramétrica de ventana/puerta.

    Para agregar un producto nuevo: crear una clase que herede de esta,
    implementar calcular_piezas() y decorarla con @registrar_plantilla("clave").
    """

    nombre: str = "base"
    descripcion: str = ""

    @abstractmethod
    def calcular_piezas(self, ventana_id: str, ancho_total_mm: float, alto_total_mm: float,
                         **kwargs) -> DespieceVentana:
        ...
