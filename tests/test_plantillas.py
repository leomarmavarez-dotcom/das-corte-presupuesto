import plantillas  # noqa: F401  registra las plantillas
from plantillas.registro import listar_plantillas, obtener_plantilla


def test_plantillas_registradas():
    disponibles = listar_plantillas()
    assert "corrediza_2h_fijo" in disponibles
    assert "batiente_4h_1proyectante" in disponibles


def test_corrediza_2h_fijo_caso_aceptacion():
    plantilla = obtener_plantilla("corrediza_2h_fijo")
    despiece = plantilla.calcular_piezas("V-TEST", ancho_total_mm=1200, alto_total_mm=1500, ancho_fijo_mm=400)

    def longitudes(perfil, modulo=None):
        return sorted(
            round(p.longitud_mm) for p in despiece.piezas_aluminio
            if p.perfil_codigo == perfil and (modulo is None or p.modulo == modulo)
            for _ in range(p.cantidad)
        )

    assert longitudes("MC-01", "marco") == [1200, 1200, 1420, 1420, 1420]
    assert longitudes("JQ-01", "fijo") == [330, 330, 1410, 1410]
    assert longitudes("HJ-01", "corredizo") == [316, 316, 316, 316, 1420, 1420, 1420, 1420]
    assert longitudes("JQ-01", "corredizo") == [306, 306, 306, 306, 1346, 1346, 1346, 1346]

    vidrios = {(round(p.ancho_mm), round(p.alto_mm)): p.cantidad for p in despiece.piezas_vidrio}
    assert vidrios[(330, 1410)] == 1
    assert vidrios[(306, 1346)] == 2

    assert despiece.piezas_herrajes == []


def test_corrediza_ancho_fijo_invalido():
    plantilla = obtener_plantilla("corrediza_2h_fijo")
    try:
        plantilla.calcular_piezas("V-TEST", ancho_total_mm=1200, alto_total_mm=1500, ancho_fijo_mm=1500)
    except ValueError:
        pass
    else:
        raise AssertionError("Se esperaba ValueError con ancho_fijo_mm fuera de rango")


def test_batiente_4h_1proyectante():
    plantilla = obtener_plantilla("batiente_4h_1proyectante")
    despiece = plantilla.calcular_piezas("V-TEST-2", ancho_total_mm=2400, alto_total_mm=1800)

    conteos = {}
    for h in despiece.piezas_herrajes:
        conteos[h.codigo] = conteos.get(h.codigo, 0) + h.cantidad

    assert conteos["BISAGRA-BAT"] == 8   # 4 hojas x 2 bisagras
    assert conteos["CERRADURA-BAT"] == 4  # 4 hojas x 1 cerradura
    assert conteos["COMPAS-PROY"] == 2
    assert conteos["MANIJA-PROY"] == 1

    # 4 vidrios batientes + 1 vidrio proyectante
    assert sum(p.cantidad for p in despiece.piezas_vidrio) == 5
