"""Helpers geométricos reutilizables por las plantillas de ventanas/puertas.

Las constantes de fabricación (anchos de perfil, holguras, traslapes) son
valores de referencia típicos de sistemas de aluminio comerciales, PLACEHOLDERS
DE EJEMPLO. AJÚSTALOS en ReglasFabricacion según las plantillas de corte reales
que usa DAS Aluminios y Vidrios antes de fabricar con estos números.

Convenciones de cálculo usadas aquí (documentadas para poder auditarlas):
- El marco perimetral se corta a la medida exacta del vano (ancho_total x
  alto_total): las piezas horizontales van de lado a lado y las verticales
  se ajustan entre ellas.
- Las hojas corredizas se traslapan entre sí ("traslape_hojas_mm") para
  cubrir el ancho útil disponible.
- El vidrio siempre lleva una holgura ("holgura_vidrio_mm") respecto al
  canal donde se aloja (marco, hoja o junquillo).
"""
from __future__ import annotations

from dataclasses import dataclass

from modelos import PiezaAluminio, PiezaHerraje, PiezaVidrio


@dataclass
class ReglasFabricacion:
    ancho_perfil_marco_mm: float = 40.0
    ancho_perfil_hoja_mm: float = 32.0
    ancho_perfil_junquillo_mm: float = 18.0
    ancho_perfil_travesano_mm: float = 40.0
    traslape_hojas_mm: float = 20.0
    holgura_vidrio_mm: float = 5.0


def marco_perimetral(ventana_id: str, modulo: str, ancho_total_mm: float, alto_total_mm: float,
                      reglas: ReglasFabricacion, perfil_codigo: str = "MC-01") -> list[PiezaAluminio]:
    """Marco perimetral: horizontales pasantes (superior/inferior) + verticales
    (laterales) ajustados entre ellas."""
    return [
        PiezaAluminio(perfil_codigo, "Marco horizontal (superior/inferior)",
                      ancho_total_mm, 2, ventana_id, modulo),
        PiezaAluminio(perfil_codigo, "Marco vertical (laterales)",
                      alto_total_mm - 2 * reglas.ancho_perfil_marco_mm, 2, ventana_id, modulo),
    ]


def panel_fijo(ventana_id: str, modulo: str, ancho_util_mm: float, alto_util_mm: float,
               reglas: ReglasFabricacion, perfil_junquillo: str = "JQ-01",
               tipo_vidrio: str = "Claro", espesor_vidrio_mm: float = 4.0
               ) -> tuple[list[PiezaAluminio], list[PiezaVidrio]]:
    """Paño fijo: vidrio sostenido directamente por junquillo dentro del marco."""
    ancho_vidrio = ancho_util_mm - 2 * reglas.holgura_vidrio_mm
    alto_vidrio = alto_util_mm - 2 * reglas.holgura_vidrio_mm

    piezas_alu = [
        PiezaAluminio(perfil_junquillo, "Junquillo paño fijo horizontal", ancho_vidrio, 2, ventana_id, modulo),
        PiezaAluminio(perfil_junquillo, "Junquillo paño fijo vertical", alto_vidrio, 2, ventana_id, modulo),
    ]
    piezas_vidrio = [
        PiezaVidrio(tipo_vidrio, espesor_vidrio_mm, ancho_vidrio, alto_vidrio, 1, ventana_id, modulo, "Vidrio paño fijo")
    ]
    return piezas_alu, piezas_vidrio


def seccion_corrediza(ventana_id: str, modulo: str, ancho_util_mm: float, alto_util_mm: float,
                       num_hojas: int, reglas: ReglasFabricacion, perfil_hoja: str = "HJ-01",
                       perfil_junquillo: str = "JQ-01", tipo_vidrio: str = "Claro",
                       espesor_vidrio_mm: float = 4.0) -> tuple[list[PiezaAluminio], list[PiezaVidrio]]:
    """Sección corrediza de num_hojas hojas que se traslapan para cubrir ancho_util_mm."""
    if num_hojas < 2:
        raise ValueError("Una sección corrediza necesita al menos 2 hojas")

    n_traslapes = num_hojas - 1
    ancho_hoja = (ancho_util_mm + n_traslapes * reglas.traslape_hojas_mm) / num_hojas
    alto_hoja = alto_util_mm

    piezas_alu = [
        PiezaAluminio(perfil_hoja, f"Hoja corrediza vertical ({num_hojas} hojas)",
                      alto_hoja, 2 * num_hojas, ventana_id, modulo),
        PiezaAluminio(perfil_hoja, f"Hoja corrediza horizontal ({num_hojas} hojas)",
                      ancho_hoja - 2 * reglas.ancho_perfil_hoja_mm, 2 * num_hojas, ventana_id, modulo),
    ]

    ancho_vidrio = ancho_hoja - 2 * reglas.ancho_perfil_hoja_mm - 2 * reglas.holgura_vidrio_mm
    alto_vidrio = alto_hoja - 2 * reglas.ancho_perfil_hoja_mm - 2 * reglas.holgura_vidrio_mm

    piezas_alu.append(
        PiezaAluminio(perfil_junquillo, f"Junquillo hoja corrediza vertical ({num_hojas} hojas)",
                      alto_vidrio, 2 * num_hojas, ventana_id, modulo)
    )
    piezas_alu.append(
        PiezaAluminio(perfil_junquillo, f"Junquillo hoja corrediza horizontal ({num_hojas} hojas)",
                      ancho_vidrio, 2 * num_hojas, ventana_id, modulo)
    )

    piezas_vidrio = [
        PiezaVidrio(tipo_vidrio, espesor_vidrio_mm, ancho_vidrio, alto_vidrio, num_hojas,
                    ventana_id, modulo, "Vidrio hoja corrediza")
    ]

    return piezas_alu, piezas_vidrio


def panel_con_hoja(ventana_id: str, modulo: str, ancho_util_mm: float, alto_util_mm: float,
                    reglas: ReglasFabricacion, perfil_hoja: str, perfil_junquillo: str,
                    tipo_vidrio: str, espesor_vidrio_mm: float, descripcion_modulo: str
                    ) -> tuple[list[PiezaAluminio], list[PiezaVidrio]]:
    """Un panel de una sola hoja perimetral (batiente o proyectante): la hoja
    tiene su propio marco (2 verticales pasantes + 2 horizontales entre ellas)
    con vidrio sostenido por junquillo adentro."""
    piezas_alu = [
        PiezaAluminio(perfil_hoja, f"Hoja {descripcion_modulo} vertical", alto_util_mm, 2, ventana_id, modulo),
        PiezaAluminio(perfil_hoja, f"Hoja {descripcion_modulo} horizontal",
                      ancho_util_mm - 2 * reglas.ancho_perfil_hoja_mm, 2, ventana_id, modulo),
    ]
    ancho_vidrio = ancho_util_mm - 2 * reglas.ancho_perfil_hoja_mm - 2 * reglas.holgura_vidrio_mm
    alto_vidrio = alto_util_mm - 2 * reglas.ancho_perfil_hoja_mm - 2 * reglas.holgura_vidrio_mm
    piezas_alu.append(
        PiezaAluminio(perfil_junquillo, f"Junquillo {descripcion_modulo} horizontal", ancho_vidrio, 2, ventana_id, modulo)
    )
    piezas_alu.append(
        PiezaAluminio(perfil_junquillo, f"Junquillo {descripcion_modulo} vertical", alto_vidrio, 2, ventana_id, modulo)
    )
    piezas_vidrio = [
        PiezaVidrio(tipo_vidrio, espesor_vidrio_mm, ancho_vidrio, alto_vidrio, 1, ventana_id, modulo,
                    f"Vidrio {descripcion_modulo}")
    ]
    return piezas_alu, piezas_vidrio


def panel_proyectante(ventana_id: str, modulo: str, ancho_util_mm: float, alto_util_mm: float,
                       reglas: ReglasFabricacion, perfil_hoja: str = "HJ-01", perfil_junquillo: str = "JQ-01",
                       tipo_vidrio: str = "Claro", espesor_vidrio_mm: float = 4.0
                       ) -> tuple[list[PiezaAluminio], list[PiezaVidrio], list[PiezaHerraje]]:
    piezas_alu, piezas_vidrio = panel_con_hoja(
        ventana_id, modulo, ancho_util_mm, alto_util_mm, reglas, perfil_hoja, perfil_junquillo,
        tipo_vidrio, espesor_vidrio_mm, "proyectante")
    piezas_herrajes = [
        PiezaHerraje("COMPAS-PROY", "Compás de proyectante", 2, ventana_id, modulo),
        PiezaHerraje("MANIJA-PROY", "Manija de proyectante", 1, ventana_id, modulo),
    ]
    return piezas_alu, piezas_vidrio, piezas_herrajes


def seccion_batientes(ventana_id: str, modulo: str, ancho_util_mm: float, alto_util_mm: float,
                       num_hojas: int, reglas: ReglasFabricacion, perfil_hoja: str = "HJ-01",
                       perfil_junquillo: str = "JQ-01", perfil_marco: str = "MC-01",
                       tipo_vidrio: str = "Claro", espesor_vidrio_mm: float = 4.0
                       ) -> tuple[list[PiezaAluminio], list[PiezaVidrio], list[PiezaHerraje]]:
    """num_hojas hojas batientes (con bisagra) en una fila, separadas por
    parantes verticales del ancho del marco."""
    if num_hojas < 1:
        raise ValueError("num_hojas debe ser >= 1")

    n_parantes = num_hojas - 1
    ancho_modulo = (ancho_util_mm - n_parantes * reglas.ancho_perfil_marco_mm) / num_hojas

    piezas_alu: list[PiezaAluminio] = []
    piezas_vidrio: list[PiezaVidrio] = []
    piezas_herrajes: list[PiezaHerraje] = []

    if n_parantes > 0:
        piezas_alu.append(
            PiezaAluminio(perfil_marco, "Parante entre hojas batientes", alto_util_mm, n_parantes, ventana_id, modulo)
        )

    for i in range(1, num_hojas + 1):
        modulo_hoja = f"{modulo}-{i}"
        alu, vid = panel_con_hoja(
            ventana_id, modulo_hoja, ancho_modulo, alto_util_mm, reglas, perfil_hoja, perfil_junquillo,
            tipo_vidrio, espesor_vidrio_mm, f"batiente {i}")
        piezas_alu += alu
        piezas_vidrio += vid
        piezas_herrajes += [
            PiezaHerraje("BISAGRA-BAT", "Bisagra hoja batiente", 2, ventana_id, modulo_hoja),
            PiezaHerraje("CERRADURA-BAT", "Cerradura/pasador hoja batiente", 1, ventana_id, modulo_hoja),
        ]

    return piezas_alu, piezas_vidrio, piezas_herrajes
