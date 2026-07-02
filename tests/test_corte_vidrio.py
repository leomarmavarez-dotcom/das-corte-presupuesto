from modelos import PiezaVidrio
from motor.corte_vidrio import RetazoVidrio, optimizar_corte_vidrio


def _pieza(ancho, alto, cantidad=1, tipo="Claro", espesor=4.0):
    return PiezaVidrio(tipo, espesor, ancho, alto, cantidad, "V-TEST", "modulo")


def test_empaqueta_en_una_lamina():
    piezas = [_pieza(1000, 800), _pieza(900, 700)]
    resultados = optimizar_corte_vidrio(piezas, ancho_lamina_mm=2000, alto_lamina_mm=1600, kerf_mm=4)
    resultado = resultados[("Claro", 4.0)]
    assert resultado.laminas_nuevas_usadas == 1
    assert resultado.piezas_sin_ubicar == []


def test_prioriza_retazos_antes_de_lamina_nueva():
    piezas = [_pieza(500, 400)]
    retazos = [RetazoVidrio(id="1", tipo="Claro", espesor_mm=4.0, ancho_mm=600, alto_mm=500)]
    resultados = optimizar_corte_vidrio(
        piezas, ancho_lamina_mm=3600, alto_lamina_mm=2140, kerf_mm=4, retazos=retazos)
    resultado = resultados[("Claro", 4.0)]
    assert resultado.retazos_usados == ["1"]
    assert resultado.laminas_nuevas_usadas == 0


def test_pieza_no_cabe_en_ninguna_orientacion():
    piezas = [_pieza(4000, 500)]
    try:
        optimizar_corte_vidrio(piezas, ancho_lamina_mm=3600, alto_lamina_mm=2140, kerf_mm=4)
    except ValueError:
        pass
    else:
        raise AssertionError("Se esperaba ValueError")
