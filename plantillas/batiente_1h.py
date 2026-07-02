from __future__ import annotations

from modelos import DespieceVentana
from plantillas.base import PlantillaVentana
from plantillas.comun import ReglasFabricacion, marco_perimetral, seccion_batientes
from plantillas.registro import registrar_plantilla


@registrar_plantilla("batiente_1h")
class PuertaBatiente1Hoja(PlantillaVentana):
    """Puerta o ventana batiente de una sola hoja (con bisagra). El vidrio
    ocupa todo el paño de la hoja, sostenido por junquillo — no modela un
    panel ciego inferior tipo puerta de entrada tradicional.

    ancho_total_mm / alto_total_mm son la medida del vano (marco a marco).
    """
    nombre = "batiente_1h"
    descripcion = "Puerta/ventana batiente de 1 hoja"

    def calcular_piezas(self, ventana_id: str, ancho_total_mm: float, alto_total_mm: float, *,
                         reglas: ReglasFabricacion | None = None,
                         perfil_marco: str = "MC-01", perfil_hoja: str = "HJ-01",
                         perfil_junquillo: str = "JQ-01", tipo_vidrio: str = "Templado",
                         espesor_vidrio_mm: float = 6.0, **_) -> DespieceVentana:
        reglas = reglas or ReglasFabricacion()

        despiece = DespieceVentana(ventana_id, self.nombre, ancho_total_mm, alto_total_mm)

        despiece.piezas_aluminio += marco_perimetral(
            ventana_id, "marco", ancho_total_mm, alto_total_mm, reglas, perfil_marco)

        ancho_util = ancho_total_mm - 2 * reglas.ancho_perfil_marco_mm
        alto_util = alto_total_mm - 2 * reglas.ancho_perfil_marco_mm

        piezas_alu, piezas_vidrio, piezas_herrajes = seccion_batientes(
            ventana_id, "batiente", ancho_util, alto_util, 1, reglas,
            perfil_hoja, perfil_junquillo, perfil_marco, tipo_vidrio, espesor_vidrio_mm)
        despiece.piezas_aluminio += piezas_alu
        despiece.piezas_vidrio += piezas_vidrio
        despiece.piezas_herrajes += piezas_herrajes

        return despiece
