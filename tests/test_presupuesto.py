from catalogo.loader import cargar_catalogo
from modelos import PiezaHerraje
from motor.corte_aluminio import ResultadoCorteAluminio
from motor.corte_vidrio import ResultadoCorteVidrio
from presupuesto.calculo import calcular_costo_material, calcular_presupuesto


def test_calculo_costo_material_y_presupuesto():
    catalogo = cargar_catalogo()
    perfil = catalogo.perfiles()[0]
    vidrio = catalogo.vidrios()[0]

    resultados_aluminio = {perfil.codigo: ResultadoCorteAluminio(perfil.codigo, barras_nuevas_usadas=3)}
    resultados_vidrio = {(vidrio.tipo, vidrio.espesor_mm): ResultadoCorteVidrio(
        vidrio.tipo, vidrio.espesor_mm, laminas_nuevas_usadas=2)}
    herrajes = [PiezaHerraje("RUEDA-CORREDIZA", "Rueda corrediza", 4, "V-TEST")]

    costo = calcular_costo_material(catalogo, resultados_aluminio, resultados_vidrio, herrajes)

    assert costo.costo_aluminio == 3 * perfil.costo_por_barra
    area_m2 = 2 * (vidrio.ancho_lamina_mm * vidrio.alto_lamina_mm) / 1_000_000
    assert round(costo.costo_vidrio, 6) == round(area_m2 * vidrio.costo_m2, 6)
    herraje = catalogo.obtener_herraje("RUEDA-CORREDIZA")
    assert costo.costo_herrajes == 4 * herraje.costo_unitario

    presupuesto = calcular_presupuesto(costo, pct_mano_obra=30, pct_margen=25)
    assert round(presupuesto.monto_mano_obra, 6) == round(costo.total * 0.30, 6)
    subtotal = costo.total + presupuesto.monto_mano_obra
    assert round(presupuesto.precio_final, 6) == round(subtotal * 1.25, 6)
    assert presupuesto.precio_final > costo.total
