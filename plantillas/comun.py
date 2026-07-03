"""Helpers geométricos reutilizables por las plantillas de ventanas/puertas.

Dos familias de constantes en ReglasFabricacion:

- Los campos `ancho_cabezal_mm` / `ancho_sillar_mm` / `ancho_jamba_mm` /
  `ancho_vertical_liso_mm` / `ancho_vertical_gancho_mm` / `alto_horizontal_hoja_mm`
  corresponden a la "Serie Normal" de corredizas de DAS (perfiles ALD-701 a
  ALD-709), tomados del manual técnico Aldoca que dio Leo (2026-07-03).
  VALIDADO: dimensiones y pesos de la tabla de texto del manual. SIN VALIDAR
  contra los diagramas del catálogo (PDF "aldoca-libro perfiles.pdf") — ese
  archivo no llegó adjunto a la sesión, así que la asignación de cuál cota de
  cada perfil "come" hacia el vano (vs. cuál es la profundidad del sistema)
  es una interpretación a partir de la tabla, no una lectura del plano. Antes
  de fabricar con estos números, confirmar visualmente contra el catálogo.
- `traslape_hojas_mm` y `holgura_vidrio_mm` siguen siendo PLACEHOLDERS DE
  EJEMPLO — el manual no da el valor numérico del enganche mecánico del
  ALD-701 ni la holgura de vidrio en junquillo.
- `ancho_perfil_marco_mm` / `ancho_perfil_hoja_mm` / `ancho_perfil_travesano_mm`
  siguen siendo PLACEHOLDERS DE EJEMPLO genéricos, usados solo por las
  plantillas batientes/proyectante (`seccion_batientes`, `panel_con_hoja`)
  para las que todavía no hay perfil real de DAS.

Convenciones de cálculo usadas aquí (documentadas para poder auditarlas):
- El marco perimetral corredizo tiene 3 perfiles distintos: cabezal (arriba),
  sillar (abajo, con desagüe) y jamba (laterales, igual a ambos lados) — no
  son la misma extrusión, así que el vano interior se descuenta de forma
  asimétrica en altura (cabezal + sillar) y simétrica en ancho (2x jamba).
- Cada hoja corrediza tiene un lado "liso" (contra la jamba) y un lado
  "gancho" (traslape mecánico con la hoja vecina) — son perfiles distintos.
  Las hojas de los extremos llevan 1 liso + 1 gancho; las hojas intermedias
  (en sistemas de 3+ hojas) llevan gancho a ambos lados. Esta generalización
  a N hojas es una extrapolación mía de la fórmula del manual (que solo cubre
  2 hojas explícitamente) — pendiente de confirmar con Leo para 3+ hojas.
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
    # Genéricos, PLACEHOLDER DE EJEMPLO: usados solo por plantillas batientes/
    # proyectante para las que no hay perfil real de DAS todavía.
    ancho_perfil_marco_mm: float = 40.0
    ancho_perfil_hoja_mm: float = 32.0
    ancho_perfil_junquillo_mm: float = 18.0
    ancho_perfil_travesano_mm: float = 40.0

    # Serie Normal corrediza (ALD-701..709) — dimensiones/pesos de la tabla
    # de texto del manual Aldoca, sin verificar contra los diagramas del PDF.
    ancho_cabezal_mm: float = 30.0        # ALD-702, cota "visible" 72.0x30.0
    ancho_sillar_mm: float = 41.0         # ALD-706, cota "visible" 72.0x41.0
    ancho_jamba_mm: float = 30.0          # ALD-709, cota "visible" 72.0x30.0
    ancho_vertical_liso_mm: float = 25.0  # ALD-703, cota "visible" 40.0x25.0
    ancho_vertical_gancho_mm: float = 38.0  # ALD-701, cota "visible" 40.0x38.0
    alto_horizontal_hoja_mm: float = 43.0   # ALD-704, cota "visible" 22.0x43.0

    # Sin validar: no vienen en la tabla de texto del manual (haría falta el
    # diagrama de corte / despiece para leerlos con precisión).
    traslape_hojas_mm: float = 20.0
    holgura_vidrio_mm: float = 5.0


def marco_perimetral(ventana_id: str, modulo: str, ancho_total_mm: float, alto_total_mm: float,
                      reglas: ReglasFabricacion, perfil_cabezal: str = "MC-01",
                      perfil_sillar: str | None = None, perfil_jamba: str | None = None,
                      ancho_cabezal_mm: float | None = None, ancho_sillar_mm: float | None = None
                      ) -> list[PiezaAluminio]:
    """Marco perimetral: cabezal (arriba) + sillar (abajo) + jambas (laterales).
    Si no se pasan perfil_sillar/perfil_jamba, se usa perfil_cabezal para los
    tres (caso de plantillas sin perfiles reales diferenciados todavía). Igual
    con ancho_cabezal_mm/ancho_sillar_mm: si no se pasan, se usa el genérico
    reglas.ancho_perfil_marco_mm simétrico (comportamiento previo, sin cambios,
    para las plantillas batientes/proyectante que no tienen datos reales)."""
    perfil_sillar = perfil_sillar or perfil_cabezal
    perfil_jamba = perfil_jamba or perfil_cabezal
    ancho_cabezal_mm = reglas.ancho_perfil_marco_mm if ancho_cabezal_mm is None else ancho_cabezal_mm
    ancho_sillar_mm = reglas.ancho_perfil_marco_mm if ancho_sillar_mm is None else ancho_sillar_mm
    return [
        PiezaAluminio(perfil_cabezal, "Cabezal (marco superior)", ancho_total_mm, 1, ventana_id, modulo),
        PiezaAluminio(perfil_sillar, "Sillar (marco inferior)", ancho_total_mm, 1, ventana_id, modulo),
        PiezaAluminio(perfil_jamba, "Jamba (marco lateral)",
                      alto_total_mm - ancho_cabezal_mm - ancho_sillar_mm, 2, ventana_id, modulo),
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
                       num_hojas: int, reglas: ReglasFabricacion,
                       perfil_vertical_liso: str = "HJ-01", perfil_vertical_gancho: str = "HJ-01",
                       perfil_horizontal_hoja: str = "HJ-01", perfil_junquillo: str = "JQ-01",
                       tipo_vidrio: str = "Claro", espesor_vidrio_mm: float = 4.0
                       ) -> tuple[list[PiezaAluminio], list[PiezaVidrio], list[PiezaHerraje]]:
    """Sección corrediza de num_hojas hojas que se traslapan para cubrir ancho_util_mm.

    Cada hoja tiene 2 verticales: el lado que da contra la jamba usa
    perfil_vertical_liso, el lado que traslapa con la hoja vecina usa
    perfil_vertical_gancho. Las hojas de los extremos llevan 1 liso + 1
    gancho; las intermedias (3+ hojas) llevan gancho a ambos lados — ver
    nota de generalización a N hojas en el docstring del módulo.

    Cuenta accesorios (RUEDA-CORREDIZA, CERRADURA-CORREDIZA) con cantidades
    supuestas (2 ruedas por hoja, 1 cerradura por sección) — no confirmadas
    por Leo todavía, ver CLAUDE.md."""
    if num_hojas < 2:
        raise ValueError("Una sección corrediza necesita al menos 2 hojas")

    n_traslapes = num_hojas - 1
    ancho_hoja = (ancho_util_mm + n_traslapes * reglas.traslape_hojas_mm) / num_hojas
    alto_hoja = alto_util_mm

    piezas_alu: list[PiezaAluminio] = []
    piezas_vidrio: list[PiezaVidrio] = []
    piezas_herrajes: list[PiezaHerraje] = []

    for i in range(1, num_hojas + 1):
        lado_izq_es_gancho = i > 1
        lado_der_es_gancho = i < num_hojas
        ancho_izq = reglas.ancho_vertical_gancho_mm if lado_izq_es_gancho else reglas.ancho_vertical_liso_mm
        ancho_der = reglas.ancho_vertical_gancho_mm if lado_der_es_gancho else reglas.ancho_vertical_liso_mm

        piezas_alu.append(PiezaAluminio(
            perfil_vertical_gancho if lado_izq_es_gancho else perfil_vertical_liso,
            f"Vertical {'gancho' if lado_izq_es_gancho else 'liso'} hoja {i} de {num_hojas} (lado izq.)",
            alto_hoja, 1, ventana_id, modulo))
        piezas_alu.append(PiezaAluminio(
            perfil_vertical_gancho if lado_der_es_gancho else perfil_vertical_liso,
            f"Vertical {'gancho' if lado_der_es_gancho else 'liso'} hoja {i} de {num_hojas} (lado der.)",
            alto_hoja, 1, ventana_id, modulo))

        ancho_vidrio = ancho_hoja - ancho_izq - ancho_der - 2 * reglas.holgura_vidrio_mm
        alto_vidrio = alto_hoja - 2 * reglas.alto_horizontal_hoja_mm - 2 * reglas.holgura_vidrio_mm

        piezas_alu.append(PiezaAluminio(
            perfil_horizontal_hoja, f"Horizontal hoja {i} de {num_hojas} (sup./inf.)",
            ancho_hoja - ancho_izq - ancho_der, 2, ventana_id, modulo))
        piezas_alu.append(PiezaAluminio(
            perfil_junquillo, f"Junquillo hoja {i} de {num_hojas} vertical", alto_vidrio, 2, ventana_id, modulo))
        piezas_alu.append(PiezaAluminio(
            perfil_junquillo, f"Junquillo hoja {i} de {num_hojas} horizontal", ancho_vidrio, 2, ventana_id, modulo))

        piezas_vidrio.append(PiezaVidrio(
            tipo_vidrio, espesor_vidrio_mm, ancho_vidrio, alto_vidrio, 1,
            ventana_id, modulo, f"Vidrio hoja corrediza {i} de {num_hojas}"))

        piezas_herrajes.append(PiezaHerraje("RUEDA-CORREDIZA", f"Rueda hoja {i} de {num_hojas}", 2,
                                             ventana_id, modulo))

    piezas_herrajes.append(PiezaHerraje("CERRADURA-CORREDIZA", "Cerradura corrediza", 1, ventana_id, modulo))

    return piezas_alu, piezas_vidrio, piezas_herrajes


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
