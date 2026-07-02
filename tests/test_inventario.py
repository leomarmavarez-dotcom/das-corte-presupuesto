import pytest

from inventario.db import (
    agregar_retazo_aluminio,
    ajustar_stock_barras,
    conectar,
    confirmar_consumo_trabajo,
    generar_lista_compras,
    inicializar_db,
    listar_retazos_aluminio,
    obtener_stock_barras,
)
from modelos import PiezaHerraje
from motor.corte_aluminio import BarraCortada, ResultadoCorteAluminio


@pytest.fixture
def conn():
    c = conectar(":memory:")
    inicializar_db(c)
    yield c
    c.close()


def test_agregar_y_listar_retazo_aluminio(conn):
    agregar_retazo_aluminio(conn, "MC-01", 1500)
    conn.commit()
    retazos = listar_retazos_aluminio(conn, "MC-01")
    assert len(retazos) == 1
    assert retazos[0].longitud_mm == 1500


def test_ajustar_stock_barras_es_acumulativo(conn):
    ajustar_stock_barras(conn, "MC-01", 5)
    ajustar_stock_barras(conn, "MC-01", -2)
    conn.commit()
    assert obtener_stock_barras(conn, "MC-01") == 3


def test_generar_lista_compras_respeta_stock_existente(conn):
    ajustar_stock_barras(conn, "MC-01", 1)
    conn.commit()
    resultados_aluminio = {"MC-01": ResultadoCorteAluminio("MC-01", barras_nuevas_usadas=3)}
    lista = generar_lista_compras(conn, resultados_aluminio, {}, [])
    assert len(lista) == 1
    assert lista[0].codigo == "MC-01"
    assert lista[0].cantidad == 2  # 3 necesarias - 1 en stock


def test_confirmar_consumo_registra_retazo_y_descuenta_stock(conn):
    ajustar_stock_barras(conn, "MC-01", 2)
    conn.commit()
    barra = BarraCortada(origen="nueva:1", longitud_barra_mm=6100, piezas_mm=[1000], desperdicio_mm=5000)
    resultados_aluminio = {"MC-01": ResultadoCorteAluminio("MC-01", barras=[barra], barras_nuevas_usadas=1)}
    herrajes = [PiezaHerraje("RUEDA-CORREDIZA", "Rueda corrediza", 2, "V-TEST")]

    confirmar_consumo_trabajo(conn, resultados_aluminio, {}, herrajes, "V-TEST",
                               umbral_retazo_aluminio_mm=150)

    assert obtener_stock_barras(conn, "MC-01") == 1
    retazos = listar_retazos_aluminio(conn, "MC-01")
    assert len(retazos) == 1
    assert retazos[0].longitud_mm == 5000
