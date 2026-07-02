from __future__ import annotations

from modelos import DespieceVentana, PiezaAluminio
from plantillas.base import PlantillaVentana
from plantillas.comun import ReglasFabricacion, marco_perimetral, panel_fijo, seccion_corrediza
from plantillas.registro import registrar_plantilla


@registrar_plantilla("corrediza_2h_fijo")
class VentanaCorrediza2HojasFijo(PlantillaVentana):
    """Ventana corrediza de 2 hojas + paño fijo lateral.

    ancho_total_mm / alto_total_mm son la medida del vano (marco a marco).
    ancho_fijo_mm es el ancho del módulo del paño fijo; el resto del ancho
    se reparte entre las 2 hojas corredizas (con traslape).
    """
    nombre = "corrediza_2h_fijo"
    descripcion = "Ventana corrediza de 2 hojas + paño fijo lateral"

    def calcular_piezas(self, ventana_id: str, ancho_total_mm: float, alto_total_mm: float, *,
                         ancho_fijo_mm: float | None = None,
                         reglas: ReglasFabricacion | None = None,
                         perfil_marco: str = "MC-01", perfil_hoja: str = "HJ-01",
                         perfil_junquillo: str = "JQ-01", tipo_vidrio: str = "Claro",
                         espesor_vidrio_mm: float = 4.0, **_) -> DespieceVentana:
        reglas = reglas or ReglasFabricacion()
        if ancho_fijo_mm is None:
            ancho_fijo_mm = round(ancho_total_mm / 3)
        if not (0 < ancho_fijo_mm < ancho_total_mm):
            raise ValueError("ancho_fijo_mm debe estar entre 0 y ancho_total_mm")

        despiece = DespieceVentana(ventana_id, self.nombre, ancho_total_mm, alto_total_mm)

        despiece.piezas_aluminio += marco_perimetral(
            ventana_id, "marco", ancho_total_mm, alto_total_mm, reglas, perfil_marco)

        alto_util = alto_total_mm - 2 * reglas.ancho_perfil_marco_mm
        despiece.piezas_aluminio.append(
            PiezaAluminio(perfil_marco, "Parante entre paño fijo y sección corrediza",
                          alto_util, 1, ventana_id, "marco")
        )

        # Ancho útil de cada módulo: se descuenta el marco lateral y medio parante central
        ancho_util_fijo = ancho_fijo_mm - reglas.ancho_perfil_marco_mm - reglas.ancho_perfil_marco_mm / 2
        ancho_util_corredizo = (
            (ancho_total_mm - ancho_fijo_mm) - reglas.ancho_perfil_marco_mm - reglas.ancho_perfil_marco_mm / 2
        )

        piezas_alu_fijo, piezas_vidrio_fijo = panel_fijo(
            ventana_id, "fijo", ancho_util_fijo, alto_util, reglas, perfil_junquillo,
            tipo_vidrio, espesor_vidrio_mm)
        despiece.piezas_aluminio += piezas_alu_fijo
        despiece.piezas_vidrio += piezas_vidrio_fijo

        piezas_alu_corr, piezas_vidrio_corr = seccion_corrediza(
            ventana_id, "corredizo", ancho_util_corredizo, alto_util, 2, reglas,
            perfil_hoja, perfil_junquillo, tipo_vidrio, espesor_vidrio_mm)
        despiece.piezas_aluminio += piezas_alu_corr
        despiece.piezas_vidrio += piezas_vidrio_corr

        return despiece
