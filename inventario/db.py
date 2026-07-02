"""Inventario en SQLite: barras/láminas completas en almacén, retazos
reutilizables, lista de compras y descuento de consumo al confirmar un trabajo.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from modelos import PiezaHerraje
from motor.corte_aluminio import ResultadoCorteAluminio, RetazoAluminio
from motor.corte_vidrio import LaminaCortada, ResultadoCorteVidrio, RetazoVidrio

ESQUEMA = """
CREATE TABLE IF NOT EXISTS stock_barras (
    perfil_codigo TEXT PRIMARY KEY,
    cantidad INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS retazos_aluminio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil_codigo TEXT NOT NULL,
    longitud_mm REAL NOT NULL,
    fecha_ingreso TEXT NOT NULL,
    origen_ventana_id TEXT
);

CREATE TABLE IF NOT EXISTS stock_laminas (
    tipo TEXT NOT NULL,
    espesor_mm REAL NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (tipo, espesor_mm)
);

CREATE TABLE IF NOT EXISTS retazos_vidrio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    espesor_mm REAL NOT NULL,
    ancho_mm REAL NOT NULL,
    alto_mm REAL NOT NULL,
    fecha_ingreso TEXT NOT NULL,
    origen_ventana_id TEXT
);

CREATE TABLE IF NOT EXISTS stock_herrajes (
    codigo TEXT PRIMARY KEY,
    cantidad INTEGER NOT NULL DEFAULT 0
);
"""


def conectar(ruta_db: str | Path) -> sqlite3.Connection:
    if ruta_db != ":memory:":
        Path(ruta_db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ruta_db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db(conn: sqlite3.Connection) -> None:
    conn.executescript(ESQUEMA)
    conn.commit()


# --- Retazos -----------------------------------------------------------

def agregar_retazo_aluminio(conn: sqlite3.Connection, perfil_codigo: str, longitud_mm: float,
                             origen_ventana_id: str | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO retazos_aluminio (perfil_codigo, longitud_mm, fecha_ingreso, origen_ventana_id) "
        "VALUES (?, ?, ?, ?)",
        (perfil_codigo, longitud_mm, date.today().isoformat(), origen_ventana_id),
    )
    return cur.lastrowid


def listar_retazos_aluminio(conn: sqlite3.Connection, perfil_codigo: str) -> list[RetazoAluminio]:
    filas = conn.execute(
        "SELECT id, perfil_codigo, longitud_mm FROM retazos_aluminio WHERE perfil_codigo = ? ORDER BY longitud_mm",
        (perfil_codigo,),
    ).fetchall()
    return [RetazoAluminio(str(f["id"]), f["perfil_codigo"], f["longitud_mm"]) for f in filas]


def eliminar_retazo_aluminio(conn: sqlite3.Connection, retazo_id: int) -> None:
    conn.execute("DELETE FROM retazos_aluminio WHERE id = ?", (retazo_id,))


def agregar_retazo_vidrio(conn: sqlite3.Connection, tipo: str, espesor_mm: float, ancho_mm: float,
                           alto_mm: float, origen_ventana_id: str | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO retazos_vidrio (tipo, espesor_mm, ancho_mm, alto_mm, fecha_ingreso, origen_ventana_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (tipo, espesor_mm, ancho_mm, alto_mm, date.today().isoformat(), origen_ventana_id),
    )
    return cur.lastrowid


def listar_retazos_vidrio(conn: sqlite3.Connection, tipo: str, espesor_mm: float) -> list[RetazoVidrio]:
    filas = conn.execute(
        "SELECT id, tipo, espesor_mm, ancho_mm, alto_mm FROM retazos_vidrio "
        "WHERE tipo = ? AND espesor_mm = ? ORDER BY (ancho_mm * alto_mm)",
        (tipo, espesor_mm),
    ).fetchall()
    return [RetazoVidrio(str(f["id"]), f["tipo"], f["espesor_mm"], f["ancho_mm"], f["alto_mm"]) for f in filas]


def eliminar_retazo_vidrio(conn: sqlite3.Connection, retazo_id: int) -> None:
    conn.execute("DELETE FROM retazos_vidrio WHERE id = ?", (retazo_id,))


# --- Stock de material completo (barras/láminas/herrajes) --------------

def obtener_stock_barras(conn: sqlite3.Connection, perfil_codigo: str) -> int:
    fila = conn.execute(
        "SELECT cantidad FROM stock_barras WHERE perfil_codigo = ?", (perfil_codigo,)
    ).fetchone()
    return fila["cantidad"] if fila else 0


def ajustar_stock_barras(conn: sqlite3.Connection, perfil_codigo: str, delta: int) -> None:
    conn.execute(
        "INSERT INTO stock_barras (perfil_codigo, cantidad) VALUES (?, ?) "
        "ON CONFLICT(perfil_codigo) DO UPDATE SET cantidad = cantidad + excluded.cantidad",
        (perfil_codigo, delta),
    )


def obtener_stock_laminas(conn: sqlite3.Connection, tipo: str, espesor_mm: float) -> int:
    fila = conn.execute(
        "SELECT cantidad FROM stock_laminas WHERE tipo = ? AND espesor_mm = ?", (tipo, espesor_mm)
    ).fetchone()
    return fila["cantidad"] if fila else 0


def ajustar_stock_laminas(conn: sqlite3.Connection, tipo: str, espesor_mm: float, delta: int) -> None:
    conn.execute(
        "INSERT INTO stock_laminas (tipo, espesor_mm, cantidad) VALUES (?, ?, ?) "
        "ON CONFLICT(tipo, espesor_mm) DO UPDATE SET cantidad = cantidad + excluded.cantidad",
        (tipo, espesor_mm, delta),
    )


def obtener_stock_herraje(conn: sqlite3.Connection, codigo: str) -> int:
    fila = conn.execute("SELECT cantidad FROM stock_herrajes WHERE codigo = ?", (codigo,)).fetchone()
    return fila["cantidad"] if fila else 0


def ajustar_stock_herraje(conn: sqlite3.Connection, codigo: str, delta: int) -> None:
    conn.execute(
        "INSERT INTO stock_herrajes (codigo, cantidad) VALUES (?, ?) "
        "ON CONFLICT(codigo) DO UPDATE SET cantidad = cantidad + excluded.cantidad",
        (codigo, delta),
    )


# --- Lista de compras ----------------------------------------------------

@dataclass
class ItemCompra:
    tipo: str  # "barra_aluminio" | "lamina_vidrio" | "herraje"
    codigo: str
    descripcion: str
    cantidad: int


def generar_lista_compras(conn: sqlite3.Connection,
                           resultados_aluminio: dict[str, ResultadoCorteAluminio],
                           resultados_vidrio: dict[tuple[str, float], ResultadoCorteVidrio],
                           herrajes_necesarios: list[PiezaHerraje]) -> list[ItemCompra]:
    """Compara lo que requiere el trabajo (barras/láminas nuevas que el
    optimizador no pudo cubrir con retazos) contra las barras/láminas/herrajes
    completos que ya hay en almacén, y devuelve solo lo que falta comprar."""
    lista: list[ItemCompra] = []

    for perfil_codigo, resultado in resultados_aluminio.items():
        disponibles = obtener_stock_barras(conn, perfil_codigo)
        faltan = max(0, resultado.barras_nuevas_usadas - disponibles)
        if faltan > 0:
            lista.append(ItemCompra("barra_aluminio", perfil_codigo,
                                     f"Barra nueva de perfil {perfil_codigo}", faltan))

    for (tipo, espesor), resultado in resultados_vidrio.items():
        disponibles = obtener_stock_laminas(conn, tipo, espesor)
        faltan = max(0, resultado.laminas_nuevas_usadas - disponibles)
        if faltan > 0:
            lista.append(ItemCompra("lamina_vidrio", f"{tipo}-{espesor:.0f}mm",
                                     f"Lámina nueva de vidrio {tipo} {espesor:.0f}mm", faltan))

    necesidades_herrajes: dict[str, int] = {}
    for h in herrajes_necesarios:
        necesidades_herrajes[h.codigo] = necesidades_herrajes.get(h.codigo, 0) + h.cantidad
    for codigo, cantidad in necesidades_herrajes.items():
        disponibles = obtener_stock_herraje(conn, codigo)
        faltan = max(0, cantidad - disponibles)
        if faltan > 0:
            lista.append(ItemCompra("herraje", codigo, f"Herraje {codigo}", faltan))

    return lista


# --- Confirmar trabajo: descuenta consumo y registra sobrantes ----------

def _retazo_rectangular_aprovechable(lamina: LaminaCortada, minimo_mm: float) -> tuple[float, float] | None:
    """Heurística simple: si las piezas colocadas dejan una franja libre
    rectangular a la derecha o abajo de la lámina (layout tipo guillotina),
    se registra esa franja como retazo reutilizable. Si el layout es
    irregular no se puede garantizar un rectángulo libre limpio, así que no
    se registra nada (el desperdicio queda como recorte no reutilizable)."""
    if not lamina.piezas:
        return None
    max_x = max(p.x_mm + (p.alto_mm if p.rotado else p.ancho_mm) for p in lamina.piezas)
    max_y = max(p.y_mm + (p.ancho_mm if p.rotado else p.alto_mm) for p in lamina.piezas)
    resto_x = lamina.ancho_lamina_mm - max_x
    resto_y = lamina.alto_lamina_mm - max_y

    candidatos = []
    if resto_x >= minimo_mm:
        candidatos.append((resto_x, lamina.alto_lamina_mm))
    if resto_y >= minimo_mm:
        candidatos.append((lamina.ancho_lamina_mm, resto_y))
    if not candidatos:
        return None
    return max(candidatos, key=lambda c: c[0] * c[1])


def confirmar_consumo_trabajo(conn: sqlite3.Connection,
                               resultados_aluminio: dict[str, ResultadoCorteAluminio],
                               resultados_vidrio: dict[tuple[str, float], ResultadoCorteVidrio],
                               herrajes_necesarios: list[PiezaHerraje], ventana_id: str,
                               umbral_retazo_aluminio_mm: float = 150.0,
                               umbral_retazo_vidrio_mm: float = 150.0) -> None:
    """Al confirmar un trabajo: elimina del almacén los retazos que se
    consumieron, descuenta barras/láminas completas usadas, registra los
    sobrantes aprovechables como nuevos retazos, y descuenta los herrajes."""
    for perfil_codigo, resultado in resultados_aluminio.items():
        for rid in resultado.retazos_usados:
            eliminar_retazo_aluminio(conn, int(rid))
        if resultado.barras_nuevas_usadas:
            disponibles = obtener_stock_barras(conn, perfil_codigo)
            ajustar_stock_barras(conn, perfil_codigo, -min(resultado.barras_nuevas_usadas, disponibles))
        for barra in resultado.barras:
            if barra.desperdicio_mm >= umbral_retazo_aluminio_mm:
                agregar_retazo_aluminio(conn, perfil_codigo, barra.desperdicio_mm, ventana_id)

    for (tipo, espesor), resultado in resultados_vidrio.items():
        for rid in resultado.retazos_usados:
            eliminar_retazo_vidrio(conn, int(rid))
        if resultado.laminas_nuevas_usadas:
            disponibles = obtener_stock_laminas(conn, tipo, espesor)
            ajustar_stock_laminas(conn, tipo, espesor, -min(resultado.laminas_nuevas_usadas, disponibles))
        for lamina in resultado.laminas:
            retazo = _retazo_rectangular_aprovechable(lamina, umbral_retazo_vidrio_mm)
            if retazo:
                ancho_r, alto_r = retazo
                agregar_retazo_vidrio(conn, tipo, espesor, ancho_r, alto_r, ventana_id)

    necesidades_herrajes: dict[str, int] = {}
    for h in herrajes_necesarios:
        necesidades_herrajes[h.codigo] = necesidades_herrajes.get(h.codigo, 0) + h.cantidad
    for codigo, cantidad in necesidades_herrajes.items():
        ajustar_stock_herraje(conn, codigo, -cantidad)

    conn.commit()


def sembrar_datos_ejemplo(conn: sqlite3.Connection) -> None:
    """Carga inventario de ejemplo para el demo de main.py (no representa
    stock real)."""
    ajustar_stock_barras(conn, "MC-01", 2)
    ajustar_stock_barras(conn, "HJ-01", 1)
    ajustar_stock_laminas(conn, "Claro", 4.0, 1)
    ajustar_stock_herraje(conn, "RUEDA-CORREDIZA", 8)
    agregar_retazo_aluminio(conn, "JQ-01", 1800)
    agregar_retazo_vidrio(conn, "Claro", 4.0, 900, 700)
    conn.commit()
