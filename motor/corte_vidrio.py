"""Optimización de corte 2D (nesting) de láminas de vidrio usando rectpack.

Por cada combinación (tipo, espesor) se empaquetan los rectángulos pedidos
en "bins": primero los retazos en almacén (se agregan primero, por lo que
rectpack los llena antes de abrir una lámina nueva) y luego láminas nuevas
estándar. El kerf se modela infando cada pieza kerf_mm en ancho y alto antes
de empacar (deja espacio para el corte de la sierra/cortadora alrededor de
cada pieza) y se descuenta al reportar la medida real de corte.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from rectpack import newPacker

from modelos import PiezaVidrio


@dataclass
class RetazoVidrio:
    id: str
    tipo: str
    espesor_mm: float
    ancho_mm: float
    alto_mm: float


@dataclass
class PiezaColocada:
    ancho_mm: float
    alto_mm: float
    x_mm: float
    y_mm: float
    rotado: bool
    ventana_id: str
    modulo: str
    descripcion: str


@dataclass
class LaminaCortada:
    origen: str  # "nueva" o "retazo:<id>"
    ancho_lamina_mm: float
    alto_lamina_mm: float
    piezas: list[PiezaColocada] = field(default_factory=list)
    area_utilizada_m2: float = 0.0
    area_desperdicio_m2: float = 0.0


@dataclass
class ResultadoCorteVidrio:
    tipo: str
    espesor_mm: float
    laminas: list[LaminaCortada] = field(default_factory=list)
    laminas_nuevas_usadas: int = 0
    retazos_usados: list[str] = field(default_factory=list)
    piezas_sin_ubicar: list[tuple[float, float]] = field(default_factory=list)


def optimizar_corte_vidrio(piezas: list[PiezaVidrio], ancho_lamina_mm: float, alto_lamina_mm: float,
                            kerf_mm: float = 4.0, retazos: list[RetazoVidrio] | None = None,
                            max_laminas_nuevas: int = 20) -> dict[tuple[str, float], ResultadoCorteVidrio]:
    """Agrupa las piezas por (tipo, espesor) y resuelve el nesting de cada
    grupo por separado (no se mezclan tipos/espesores de vidrio en una lámina)."""
    retazos = retazos or []
    por_tipo: dict[tuple[str, float], list[PiezaVidrio]] = {}
    for p in piezas:
        por_tipo.setdefault((p.tipo, p.espesor_mm), []).append(p)

    resultados: dict[tuple[str, float], ResultadoCorteVidrio] = {}
    for (tipo, espesor), lista in por_tipo.items():
        retazos_tipo = [r for r in retazos if r.tipo == tipo and r.espesor_mm == espesor]
        resultados[(tipo, espesor)] = _optimizar_grupo(
            tipo, espesor, lista, ancho_lamina_mm, alto_lamina_mm, kerf_mm, retazos_tipo, max_laminas_nuevas)
    return resultados


def _optimizar_grupo(tipo: str, espesor: float, piezas: list[PiezaVidrio], ancho_lamina_mm: float,
                      alto_lamina_mm: float, kerf_mm: float, retazos: list[RetazoVidrio],
                      max_laminas_nuevas: int) -> ResultadoCorteVidrio:
    packer = newPacker(rotation=True)

    rid_info: dict[int, tuple[float, float, float, float, str, str, str]] = {}
    rid = 0
    for p in piezas:
        if p.ancho_mm > max(ancho_lamina_mm, alto_lamina_mm) or p.alto_mm > max(ancho_lamina_mm, alto_lamina_mm):
            raise ValueError(
                f"La pieza de vidrio {p.ancho_mm}x{p.alto_mm}mm ({tipo} {espesor}mm) no cabe en "
                f"ninguna orientación dentro de la lámina estándar {ancho_lamina_mm}x{alto_lamina_mm}mm"
            )
        w = p.ancho_mm + kerf_mm
        h = p.alto_mm + kerf_mm
        for _ in range(p.cantidad):
            packer.add_rect(w, h, rid)
            rid_info[rid] = (w, h, p.ancho_mm, p.alto_mm, p.ventana_id, p.modulo, p.descripcion)
            rid += 1

    bin_origen: dict[int, tuple[str, float, float]] = {}
    bin_id = 0
    for r in retazos:
        packer.add_bin(r.ancho_mm, r.alto_mm, bid=bin_id)
        bin_origen[bin_id] = (f"retazo:{r.id}", r.ancho_mm, r.alto_mm)
        bin_id += 1
    for _ in range(max_laminas_nuevas):
        packer.add_bin(ancho_lamina_mm, alto_lamina_mm, bid=bin_id)
        bin_origen[bin_id] = ("nueva", ancho_lamina_mm, alto_lamina_mm)
        bin_id += 1

    packer.pack()

    laminas: list[LaminaCortada] = []
    retazos_usados: list[str] = []
    laminas_nuevas_usadas = 0
    ids_colocados: set[int] = set()

    for abin in packer:
        origen, ancho_b, alto_b = bin_origen[abin.bid]
        piezas_colocadas: list[PiezaColocada] = []
        for rect in abin:
            w_kerf, h_kerf, ancho_real, alto_real, ventana_id, modulo, descripcion = rid_info[rect.rid]
            rotado = not math.isclose(rect.width, w_kerf, abs_tol=0.5)
            piezas_colocadas.append(
                PiezaColocada(ancho_real, alto_real, rect.x, rect.y, rotado, ventana_id, modulo, descripcion)
            )
            ids_colocados.add(rect.rid)
        if not piezas_colocadas:
            continue
        area_pzs_m2 = sum(c.ancho_mm * c.alto_mm for c in piezas_colocadas) / 1_000_000
        area_lamina_m2 = (ancho_b * alto_b) / 1_000_000
        laminas.append(LaminaCortada(origen, ancho_b, alto_b, piezas_colocadas, area_pzs_m2, area_lamina_m2 - area_pzs_m2))
        if origen.startswith("retazo:"):
            retazos_usados.append(origen.split(":", 1)[1])
        else:
            laminas_nuevas_usadas += 1

    piezas_sin_ubicar = [
        (rid_info[r][2], rid_info[r][3]) for r in rid_info if r not in ids_colocados
    ]
    if piezas_sin_ubicar:
        raise RuntimeError(
            f"No se pudieron ubicar {len(piezas_sin_ubicar)} pieza(s) de vidrio {tipo} {espesor}mm "
            f"con {max_laminas_nuevas} láminas nuevas disponibles; aumenta max_laminas_nuevas"
        )

    return ResultadoCorteVidrio(tipo, espesor, laminas, laminas_nuevas_usadas, retazos_usados, piezas_sin_ubicar)
