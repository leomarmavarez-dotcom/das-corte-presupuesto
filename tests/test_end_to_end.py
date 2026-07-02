import plantillas  # noqa: F401
from catalogo.loader import cargar_catalogo
from etiquetas.pdf_etiquetas import generar_etiquetas_pdf
from inventario.db import conectar, confirmar_consumo_trabajo, generar_lista_compras, inicializar_db
from motor.corte_aluminio import optimizar_corte_aluminio
from motor.corte_vidrio import optimizar_corte_vidrio
from plantillas.registro import obtener_plantilla
from presupuesto.calculo import calcular_costo_material, calcular_presupuesto
from presupuesto.pdf_presupuesto import generar_pdf_presupuesto


def test_flujo_completo_corrediza_2h_fijo(tmp_path):
    catalogo = cargar_catalogo()
    conn = conectar(tmp_path / "almacen.db")
    inicializar_db(conn)

    plantilla = obtener_plantilla("corrediza_2h_fijo")
    despiece = plantilla.calcular_piezas("V-001", ancho_total_mm=1200, alto_total_mm=1500, ancho_fijo_mm=400)
    assert despiece.piezas_aluminio
    assert despiece.piezas_vidrio

    resultados_aluminio = optimizar_corte_aluminio(
        despiece.piezas_aluminio,
        longitud_barra_mm=catalogo.config.longitud_barra_default_mm,
        kerf_mm=catalogo.config.kerf_aluminio_mm,
    )
    assert resultados_aluminio
    for resultado in resultados_aluminio.values():
        for barra in resultado.barras:
            assert barra.desperdicio_mm >= 0

    tipos_vidrio = {(p.tipo, p.espesor_mm) for p in despiece.piezas_vidrio}
    resultados_vidrio = {}
    for tipo, espesor in tipos_vidrio:
        vidrio_cat = catalogo.obtener_vidrio(tipo, espesor)
        resultados_vidrio.update(optimizar_corte_vidrio(
            [p for p in despiece.piezas_vidrio if p.tipo == tipo and p.espesor_mm == espesor],
            vidrio_cat.ancho_lamina_mm, vidrio_cat.alto_lamina_mm,
            kerf_mm=catalogo.config.kerf_vidrio_mm,
        ))
    assert resultados_vidrio
    for resultado in resultados_vidrio.values():
        assert resultado.piezas_sin_ubicar == []

    costo_material = calcular_costo_material(catalogo, resultados_aluminio, resultados_vidrio, despiece.piezas_herrajes)
    assert costo_material.total > 0

    presupuesto = calcular_presupuesto(costo_material, pct_mano_obra=30, pct_margen=25)
    assert presupuesto.precio_final > costo_material.total

    lista_compras = generar_lista_compras(conn, resultados_aluminio, resultados_vidrio, despiece.piezas_herrajes)
    assert len(lista_compras) > 0  # almacén vacío: hay que comprar todo

    ruta_presupuesto = tmp_path / "presupuesto.pdf"
    ruta_etiquetas = tmp_path / "etiquetas.pdf"
    generar_pdf_presupuesto(ruta_presupuesto, "Cliente Test", "OC-1", "V-001", catalogo.config.moneda,
                             costo_material, presupuesto)
    n_etiquetas = generar_etiquetas_pdf(ruta_etiquetas, "Cliente Test", "OC-1",
                                         despiece.piezas_aluminio, despiece.piezas_vidrio)
    assert ruta_presupuesto.exists() and ruta_presupuesto.stat().st_size > 0
    assert ruta_etiquetas.exists() and ruta_etiquetas.stat().st_size > 0
    assert n_etiquetas == sum(p.cantidad for p in despiece.piezas_aluminio) + sum(p.cantidad for p in despiece.piezas_vidrio)

    confirmar_consumo_trabajo(conn, resultados_aluminio, resultados_vidrio, despiece.piezas_herrajes, "V-001")
    conn.close()
