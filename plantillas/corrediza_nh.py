from __future__ import annotations

from modelos import DespieceVentana
from plantillas.base import PlantillaVentana
from plantillas.comun import ReglasFabricacion, marco_perimetral, seccion_corrediza
from plantillas.registro import registrar_plantilla


@registrar_plantilla("corrediza_nh")
class VentanaCorredizaNHojas(PlantillaVentana):
    """Ventana o puerta corrediza de N hojas, sin paño fijo (todo el ancho
    del vano se reparte entre las hojas corredizas, con traslape).

    ancho_total_mm / alto_total_mm son la medida del vano (marco a marco).
    num_hojas es la cantidad de hojas corredizas (mínimo 2).
    """
    nombre = "corrediza_nh"
    descripcion = "Ventana/puerta corrediza de N hojas sin paño fijo"

    def calcular_piezas(self, ventana_id: str, ancho_total_mm: float, alto_total_mm: float, *,
                         num_hojas: int = 2,
                         reglas: ReglasFabricacion | None = None,
                         perfil_marco: str = "MC-01", perfil_hoja: str = "HJ-01",
                         perfil_junquillo: str = "JQ-01", tipo_vidrio: str = "Claro",
                         espesor_vidrio_mm: float = 4.0, **_) -> DespieceVentana:
        reglas = reglas or ReglasFabricacion()

        despiece = DespieceVentana(ventana_id, self.nombre, ancho_total_mm, alto_total_mm)

        despiece.piezas_aluminio += marco_perimetral(
            ventana_id, "marco", ancho_total_mm, alto_total_mm, reglas, perfil_marco)

        ancho_util = ancho_total_mm - 2 * reglas.ancho_perfil_marco_mm
        alto_util = alto_total_mm - 2 * reglas.ancho_perfil_marco_mm

        piezas_alu, piezas_vidrio = seccion_corrediza(
            ventana_id, "corredizo", ancho_util, alto_util, num_hojas, reglas,
            perfil_hoja, perfil_junquillo, tipo_vidrio, espesor_vidrio_mm)
        despiece.piezas_aluminio += piezas_alu
        despiece.piezas_vidrio += piezas_vidrio

        return despiece
