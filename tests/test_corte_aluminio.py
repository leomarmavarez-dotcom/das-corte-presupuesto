from motor.corte_aluminio import RetazoAluminio, optimizar_corte_perfil


def test_optimiza_a_dos_barras_sin_kerf():
    # 4000+2000=6000 cabe justo en una barra de 6100; con 4 piezas de esas
    # medidas el óptimo son 2 barras (no 3, 4, etc.)
    piezas = [4000, 4000, 2000, 2000]
    resultado = optimizar_corte_perfil("MC-01", piezas, longitud_barra_nueva_mm=6100, kerf_mm=0)
    assert resultado.barras_nuevas_usadas == 2
    assert sum(len(b.piezas_mm) for b in resultado.barras) == 4
    for barra in resultado.barras:
        assert sum(barra.piezas_mm) <= barra.longitud_barra_mm


def test_prioriza_retazos_antes_de_barra_nueva():
    piezas = [1500, 1500]
    retazos = [RetazoAluminio(id="1", perfil_codigo="MC-01", longitud_mm=3100)]
    resultado = optimizar_corte_perfil("MC-01", piezas, longitud_barra_nueva_mm=6100, kerf_mm=3, retazos=retazos)
    assert resultado.retazos_usados == ["1"]
    assert resultado.barras_nuevas_usadas == 0


def test_pieza_mas_larga_que_barra_lanza_error():
    try:
        optimizar_corte_perfil("MC-01", [7000], longitud_barra_nueva_mm=6100)
    except ValueError:
        pass
    else:
        raise AssertionError("Se esperaba ValueError")


def test_lista_vacia():
    resultado = optimizar_corte_perfil("MC-01", [], longitud_barra_nueva_mm=6100)
    assert resultado.barras == []
    assert resultado.barras_nuevas_usadas == 0
