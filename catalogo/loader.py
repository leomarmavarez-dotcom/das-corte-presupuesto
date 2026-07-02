"""Carga del catálogo (perfiles de aluminio, vidrio, herrajes y configuración
general) desde los archivos JSON editables de este directorio.

Los precios y medidas en los .json son PLACEHOLDERS DE EJEMPLO — reemplázalos
con los datos reales de tus perfiles, láminas y proveedores.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DIR_CATALOGO = Path(__file__).resolve().parent


@dataclass
class PerfilAluminio:
    codigo: str
    nombre: str
    categoria: str
    longitud_barra_mm: float
    costo_por_barra: float


@dataclass
class Vidrio:
    tipo: str
    espesor_mm: float
    ancho_lamina_mm: float
    alto_lamina_mm: float
    costo_m2: float


@dataclass
class Herraje:
    codigo: str
    nombre: str
    unidad: str
    costo_unitario: float


@dataclass
class ConfiguracionGeneral:
    moneda: str
    longitud_barra_default_mm: float
    kerf_aluminio_mm: float
    kerf_vidrio_mm: float
    pct_mano_obra_default: float
    pct_margen_default: float


class Catalogo:
    def __init__(self, perfiles: list[PerfilAluminio], vidrios: list[Vidrio],
                 herrajes: list[Herraje], config: ConfiguracionGeneral):
        self._perfiles = {p.codigo: p for p in perfiles}
        self._vidrios = {(v.tipo, v.espesor_mm): v for v in vidrios}
        self._herrajes = {h.codigo: h for h in herrajes}
        self.config = config

    def obtener_perfil(self, codigo: str) -> PerfilAluminio:
        try:
            return self._perfiles[codigo]
        except KeyError:
            raise KeyError(f"Perfil '{codigo}' no está en el catálogo (catalogo/perfiles.json)") from None

    def obtener_vidrio(self, tipo: str, espesor_mm: float) -> Vidrio:
        try:
            return self._vidrios[(tipo, espesor_mm)]
        except KeyError:
            raise KeyError(f"Vidrio '{tipo}' {espesor_mm}mm no está en el catálogo (catalogo/vidrio.json)") from None

    def obtener_herraje(self, codigo: str) -> Herraje:
        try:
            return self._herrajes[codigo]
        except KeyError:
            raise KeyError(f"Herraje '{codigo}' no está en el catálogo (catalogo/herrajes.json)") from None

    def perfiles(self) -> list[PerfilAluminio]:
        return list(self._perfiles.values())

    def vidrios(self) -> list[Vidrio]:
        return list(self._vidrios.values())

    def herrajes(self) -> list[Herraje]:
        return list(self._herrajes.values())


def cargar_catalogo(directorio: Path | None = None) -> Catalogo:
    base = directorio or DIR_CATALOGO

    def leer(nombre: str):
        with (base / nombre).open(encoding="utf-8") as f:
            return json.load(f)

    perfiles = [
        PerfilAluminio(p["codigo"], p["nombre"], p["categoria"], p["longitud_barra_mm"], p["costo_por_barra"])
        for p in leer("perfiles.json")
    ]
    vidrios = [
        Vidrio(v["tipo"], v["espesor_mm"], v["ancho_lamina_mm"], v["alto_lamina_mm"], v["costo_m2"])
        for v in leer("vidrio.json")
    ]
    herrajes = [
        Herraje(h["codigo"], h["nombre"], h["unidad"], h["costo_unitario"])
        for h in leer("herrajes.json")
    ]
    cfg = leer("config.json")
    config = ConfiguracionGeneral(
        moneda=cfg["moneda"],
        longitud_barra_default_mm=cfg["longitud_barra_default_mm"],
        kerf_aluminio_mm=cfg["kerf_aluminio_mm"],
        kerf_vidrio_mm=cfg["kerf_vidrio_mm"],
        pct_mano_obra_default=cfg["pct_mano_obra_default"],
        pct_margen_default=cfg["pct_margen_default"],
    )
    return Catalogo(perfiles, vidrios, herrajes, config)
