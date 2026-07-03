from __future__ import annotations

from modelos import DespieceVentana, PiezaAluminio
from plantillas.base import PlantillaVentana
from plantillas.comun import ReglasFabricacion, marco_perimetral, panel_proyectante, seccion_batientes
from plantillas.registro import registrar_plantilla


@registrar_plantilla("batiente_4h_1proyectante")
class Ventana4HojasProyectante(PlantillaVentana):
    """Ventana de 4 hojas batientes (fila inferior) + 1 módulo proyectante
    (fila superior, para ventilación), separadas por un travesaño horizontal.

    ancho_total_mm / alto_total_mm son la medida del vano. alto_proyectante_mm
    es la altura del módulo proyectante superior; el resto de la altura queda
    para la fila de 4 hojas batientes.
    """
    nombre = "batiente_4h_1proyectante"
    descripcion = "Ventana de 4 hojas + 1 proyectante"

    def calcular_piezas(self, ventana_id: str, ancho_total_mm: float, alto_total_mm: float, *,
                         alto_proyectante_mm: float | None = None,
                         reglas: ReglasFabricacion | None = None,
                         perfil_marco: str = "MC-01", perfil_hoja: str = "HJ-01",
                         perfil_junquillo: str = "JQ-01", perfil_travesano: str = "TR-01",
                         perfil_hoja_proyectante: str = "ALD-724", perfil_junquillo_proyectante: str = "ALD-722",
                         tipo_vidrio: str = "Claro", espesor_vidrio_mm: float = 4.0, **_) -> DespieceVentana:
        reglas = reglas or ReglasFabricacion()
        if alto_proyectante_mm is None:
            alto_proyectante_mm = round(alto_total_mm / 3)
        if not (0 < alto_proyectante_mm < alto_total_mm):
            raise ValueError("alto_proyectante_mm debe estar entre 0 y alto_total_mm")

        despiece = DespieceVentana(ventana_id, self.nombre, ancho_total_mm, alto_total_mm)

        despiece.piezas_aluminio += marco_perimetral(
            ventana_id, "marco", ancho_total_mm, alto_total_mm, reglas, perfil_marco)

        ancho_util = ancho_total_mm - 2 * reglas.ancho_perfil_marco_mm
        despiece.piezas_aluminio.append(
            PiezaAluminio(perfil_travesano, "Travesaño entre proyectante y hojas batientes",
                          ancho_util, 1, ventana_id, "marco")
        )

        alto_util_proyectante = (
            alto_proyectante_mm - reglas.ancho_perfil_marco_mm - reglas.ancho_perfil_travesano_mm / 2
        )
        alto_util_batientes = (
            (alto_total_mm - alto_proyectante_mm) - reglas.ancho_perfil_marco_mm - reglas.ancho_perfil_travesano_mm / 2
        )

        alu_p, vid_p, her_p = panel_proyectante(
            ventana_id, "proyectante", ancho_util, alto_util_proyectante, reglas,
            perfil_hoja_proyectante, perfil_junquillo_proyectante, tipo_vidrio, espesor_vidrio_mm)
        despiece.piezas_aluminio += alu_p
        despiece.piezas_vidrio += vid_p
        despiece.piezas_herrajes += her_p

        alu_b, vid_b, her_b = seccion_batientes(
            ventana_id, "batientes", ancho_util, alto_util_batientes, 4, reglas,
            perfil_hoja, perfil_junquillo, perfil_marco, tipo_vidrio, espesor_vidrio_mm)
        despiece.piezas_aluminio += alu_b
        despiece.piezas_vidrio += vid_b
        despiece.piezas_herrajes += her_b

        return despiece
