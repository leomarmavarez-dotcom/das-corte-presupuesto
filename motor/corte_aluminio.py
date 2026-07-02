"""Optimización de corte 1D de perfiles de aluminio (cutting stock problem)
usando Google OR-Tools CP-SAT.

Por cada perfil se resuelve un bin-packing: las piezas pedidas son los ítems,
y las "barras" disponibles son los retazos en almacén (capacidad = su
longitud, costo = 0, se usan primero) más barras nuevas de longitud estándar
(costo > 0). El solver minimiza primero la cantidad de barras nuevas
compradas y, como criterio secundario, el desperdicio total.

Modelo de kerf: se descuenta kerf_mm por cada pieza cortada de una barra
(incluida la última). Es un modelo conservador y simple -- puede sobrestimar
el desperdicio en un par de milímetros por barra, pero nunca hace que una
barra se quede corta.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from modelos import PiezaAluminio


@dataclass
class RetazoAluminio:
    id: str
    perfil_codigo: str
    longitud_mm: float


@dataclass
class BarraCortada:
    origen: str  # "nueva:<n>" o "retazo:<id>"
    longitud_barra_mm: float
    piezas_mm: list[float]
    desperdicio_mm: float


@dataclass
class ResultadoCorteAluminio:
    perfil_codigo: str
    barras: list[BarraCortada] = field(default_factory=list)
    barras_nuevas_usadas: int = 0
    retazos_usados: list[str] = field(default_factory=list)
    longitud_total_utilizada_mm: float = 0.0
    desperdicio_total_mm: float = 0.0


def _ffd_num_bins(piezas_desc: list[float], capacidad_mm: float, kerf_mm: float) -> int:
    """First-Fit-Decreasing: solo se usa para acotar cuántas barras NUEVAS
    puede llegar a necesitar el modelo (cota superior, no el resultado final)."""
    bins: list[float] = []
    for pieza in piezas_desc:
        necesita = pieza + kerf_mm
        for i, restante in enumerate(bins):
            if necesita <= restante:
                bins[i] -= necesita
                break
        else:
            bins.append(capacidad_mm - necesita)
    return len(bins)


def optimizar_corte_perfil(perfil_codigo: str, longitudes_mm: list[float], longitud_barra_nueva_mm: float,
                            kerf_mm: float = 3.0, retazos: list[RetazoAluminio] | None = None,
                            tiempo_limite_seg: float = 15.0) -> ResultadoCorteAluminio:
    retazos = retazos or []
    piezas = sorted(longitudes_mm, reverse=True)
    if not piezas:
        return ResultadoCorteAluminio(perfil_codigo)

    if any(p > longitud_barra_nueva_mm for p in piezas):
        raise ValueError(
            f"Hay una pieza de perfil {perfil_codigo} más larga que la barra estándar "
            f"({longitud_barra_nueva_mm} mm)"
        )

    n = len(piezas)
    max_barras_nuevas = _ffd_num_bins(piezas, longitud_barra_nueva_mm, kerf_mm) + 1

    # bins_info: (origen, capacidad_mm, costo)
    bins_info: list[tuple[str, float, int]] = []
    for r in retazos:
        bins_info.append((f"retazo:{r.id}", r.longitud_mm, 0))
    for i in range(max_barras_nuevas):
        bins_info.append((f"nueva:{i + 1}", longitud_barra_nueva_mm, 1_000_000))

    num_bins = len(bins_info)

    model = cp_model.CpModel()
    x = {(i, j): model.NewBoolVar(f"x_{i}_{j}") for i in range(n) for j in range(num_bins)}
    y = [model.NewBoolVar(f"y_{j}") for j in range(num_bins)]

    for i in range(n):
        model.Add(sum(x[i, j] for j in range(num_bins)) == 1)

    piezas_kerf = [int(round(p + kerf_mm)) for p in piezas]
    for j in range(num_bins):
        _, capacidad, _ = bins_info[j]
        model.Add(sum(piezas_kerf[i] * x[i, j] for i in range(n)) <= int(round(capacidad)) * y[j])
        for i in range(n):
            model.Add(x[i, j] <= y[j])

    # Simetría: entre barras nuevas (todas con la misma capacidad), solo abrir
    # la barra nueva k si la k-1 ya está en uso.
    primer_indice_nueva = len(retazos)
    for j in range(primer_indice_nueva + 1, num_bins):
        model.Add(y[j] <= y[j - 1])

    costo_total = sum(bins_info[j][2] * y[j] for j in range(num_bins))
    desperdicio_aprox = sum(
        int(round(bins_info[j][1])) * y[j] - sum(piezas_kerf[i] * x[i, j] for i in range(n))
        for j in range(num_bins)
    )
    model.Minimize(costo_total * 10_000 + desperdicio_aprox)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tiempo_limite_seg
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"No se encontró una solución de corte para el perfil {perfil_codigo}")

    barras: list[BarraCortada] = []
    retazos_usados: list[str] = []
    barras_nuevas_usadas = 0
    for j in range(num_bins):
        if not solver.BooleanValue(y[j]):
            continue
        origen, capacidad, _ = bins_info[j]
        asignadas = [piezas[i] for i in range(n) if solver.BooleanValue(x[i, j])]
        if not asignadas:
            continue
        usado = sum(asignadas) + kerf_mm * len(asignadas)
        barras.append(BarraCortada(origen, capacidad, asignadas, capacidad - usado))
        if origen.startswith("retazo:"):
            retazos_usados.append(origen.split(":", 1)[1])
        else:
            barras_nuevas_usadas += 1

    return ResultadoCorteAluminio(
        perfil_codigo=perfil_codigo,
        barras=barras,
        barras_nuevas_usadas=barras_nuevas_usadas,
        retazos_usados=retazos_usados,
        longitud_total_utilizada_mm=sum(b.longitud_barra_mm for b in barras),
        desperdicio_total_mm=sum(b.desperdicio_mm for b in barras),
    )


def optimizar_corte_aluminio(piezas: list[PiezaAluminio], longitud_barra_mm: float = 6100.0,
                              kerf_mm: float = 3.0,
                              retazos_por_perfil: dict[str, list[RetazoAluminio]] | None = None,
                              tiempo_limite_seg: float = 15.0) -> dict[str, ResultadoCorteAluminio]:
    """Agrupa las piezas por perfil y resuelve el corte de cada uno por separado
    (barras de perfiles distintos no se pueden combinar)."""
    retazos_por_perfil = retazos_por_perfil or {}
    por_perfil: dict[str, list[PiezaAluminio]] = {}
    for p in piezas:
        por_perfil.setdefault(p.perfil_codigo, []).append(p)

    resultados: dict[str, ResultadoCorteAluminio] = {}
    for perfil_codigo, lista in por_perfil.items():
        longitudes: list[float] = []
        for p in lista:
            longitudes.extend(p.longitudes_individuales())
        resultados[perfil_codigo] = optimizar_corte_perfil(
            perfil_codigo, longitudes, longitud_barra_mm, kerf_mm,
            retazos_por_perfil.get(perfil_codigo, []), tiempo_limite_seg)
    return resultados
