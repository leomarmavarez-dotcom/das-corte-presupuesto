import plantillas  # noqa: F401  registra las plantillas
from plantillas.registro import listar_plantillas, obtener_plantilla


def test_plantillas_registradas():
    disponibles = listar_plantillas()
    assert "corrediza_2h_fijo" in disponibles
    assert "batiente_4h_1proyectante" in disponibles
    assert "corrediza_nh" in disponibles
    assert "batiente_1h" in disponibles


def test_corrediza_2h_fijo_caso_aceptacion():
    # Geometría Serie Normal (ALD-701..709) del manual técnico Aldoca que dio
    # Leo 2026-07-03 (dimensiones/pesos validados contra la tabla de texto,
    # SIN validar contra los diagramas del PDF — ver notas en comun.py).
    plantilla = obtener_plantilla("corrediza_2h_fijo")
    despiece = plantilla.calcular_piezas("V-TEST", ancho_total_mm=1200, alto_total_mm=1500, ancho_fijo_mm=400)

    def longitudes(perfil, modulo=None):
        return sorted(
            round(p.longitud_mm) for p in despiece.piezas_aluminio
            if p.perfil_codigo == perfil and (modulo is None or p.modulo == modulo)
            for _ in range(p.cantidad)
        )

    # Cabezal/sillar (ALD-702/706) horizontales pasantes; jamba (ALD-709)
    # lateral + parante central (misma jamba, sin perfil propio confirmado).
    assert longitudes("ALD-702", "marco") == [1200]
    assert longitudes("ALD-706", "marco") == [1200]
    assert longitudes("ALD-709", "marco") == [1429, 1429, 1429]

    assert longitudes("JQ-01", "fijo") == [345, 345, 1419, 1419]

    # Cada hoja: 1 vertical liso (ALD-703) + 1 vertical gancho (ALD-701)
    assert longitudes("ALD-703", "corredizo") == [1429, 1429]
    assert longitudes("ALD-701", "corredizo") == [1429, 1429]
    assert longitudes("ALD-704", "corredizo") == [324, 324, 324, 324]
    assert longitudes("JQ-01", "corredizo") == [314, 314, 314, 314, 1333, 1333, 1333, 1333]

    vidrios: dict[tuple[int, int], int] = {}
    for p in despiece.piezas_vidrio:
        clave = (round(p.ancho_mm), round(p.alto_mm))
        vidrios[clave] = vidrios.get(clave, 0) + p.cantidad
    assert vidrios[(345, 1419)] == 1  # paño fijo
    assert vidrios[(314, 1333)] == 2  # 2 hojas corredizas

    conteos_herrajes = {}
    for h in despiece.piezas_herrajes:
        conteos_herrajes[h.codigo] = conteos_herrajes.get(h.codigo, 0) + h.cantidad
    assert conteos_herrajes["RUEDA-CORREDIZA"] == 4  # 2 hojas x 2 ruedas (cantidad supuesta, sin confirmar)
    assert conteos_herrajes["CERRADURA-CORREDIZA"] == 1


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


def test_corrediza_nh_4_hojas():
    plantilla = obtener_plantilla("corrediza_nh")
    despiece = plantilla.calcular_piezas("V-TEST-3", ancho_total_mm=4250, alto_total_mm=1430, num_hojas=4)

    assert sum(p.cantidad for p in despiece.piezas_vidrio) == 4
    # sin paño fijo: no hay parante central, solo el marco perimetral + hojas
    assert {p.modulo for p in despiece.piezas_aluminio} == {"marco", "corredizo"}

    conteos = {}
    for h in despiece.piezas_herrajes:
        conteos[h.codigo] = conteos.get(h.codigo, 0) + h.cantidad
    assert conteos["RUEDA-CORREDIZA"] == 8   # 4 hojas x 2 ruedas (cantidad supuesta, sin confirmar)
    assert conteos["CERRADURA-CORREDIZA"] == 1

    # hojas de extremo (1 y 4): 1 liso + 1 gancho; hojas intermedias (2 y 3): 2 gancho
    verticales_liso = [p for p in despiece.piezas_aluminio if p.perfil_codigo == "ALD-703"]
    verticales_gancho = [p for p in despiece.piezas_aluminio if p.perfil_codigo == "ALD-701"]
    assert sum(p.cantidad for p in verticales_liso) == 2
    assert sum(p.cantidad for p in verticales_gancho) == 6


def test_corrediza_nh_default_2_hojas():
    plantilla = obtener_plantilla("corrediza_nh")
    despiece = plantilla.calcular_piezas("V-TEST-4", ancho_total_mm=600, alto_total_mm=450)
    assert sum(p.cantidad for p in despiece.piezas_vidrio) == 2


def test_batiente_1h():
    plantilla = obtener_plantilla("batiente_1h")
    despiece = plantilla.calcular_piezas("V-TEST-5", ancho_total_mm=800, alto_total_mm=2100)

    conteos = {}
    for h in despiece.piezas_herrajes:
        conteos[h.codigo] = conteos.get(h.codigo, 0) + h.cantidad

    assert conteos["BISAGRA-BAT"] == 2
    assert conteos["CERRADURA-BAT"] == 1
    assert sum(p.cantidad for p in despiece.piezas_vidrio) == 1
