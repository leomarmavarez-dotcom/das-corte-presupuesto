from __future__ import annotations

from typing import Callable, Type

from plantillas.base import PlantillaVentana

_REGISTRO: dict[str, Type[PlantillaVentana]] = {}


def registrar_plantilla(clave: str) -> Callable[[Type[PlantillaVentana]], Type[PlantillaVentana]]:
    def decorador(cls: Type[PlantillaVentana]) -> Type[PlantillaVentana]:
        if clave in _REGISTRO:
            raise ValueError(f"La plantilla '{clave}' ya está registrada")
        _REGISTRO[clave] = cls
        return cls
    return decorador


def obtener_plantilla(clave: str) -> PlantillaVentana:
    if clave not in _REGISTRO:
        disponibles = ", ".join(sorted(_REGISTRO)) or "(ninguna)"
        raise KeyError(f"Plantilla '{clave}' no encontrada. Disponibles: {disponibles}")
    return _REGISTRO[clave]()


def listar_plantillas() -> list[str]:
    return sorted(_REGISTRO)
