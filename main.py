"""Punto de entrada / ejemplo de uso completo — Fase 1.

Caso de prueba (criterio de aceptación): ventana corrediza de 2 hojas +
paño fijo, vano de 1.20 m x 1.50 m.

Ejecutar con: python main.py
"""
from __future__ import annotations

from pathlib import Path

import plantillas  # noqa: F401  (importarlo registra las plantillas disponibles)
from catalogo.loader import cargar_catalogo
from etiquetas.pdf_etiquetas import generar_etiquetas_pdf
from inventario.db import (
    conectar,
    confirmar_consumo_trabajo,
    generar_lista_compras,
    inicializar_db,
    listar_retazos_aluminio,
    listar_retazos_vidrio,
    sembrar_datos_ejemplo,
)
from motor.corte_aluminio import optimizar_corte_aluminio
from motor.corte_vidrio import optimizar_corte_vidrio
from plantillas.registro import obtener_plantilla
from presupuesto.calculo import calcular_costo_material, calcular_presupuesto
from presupuesto.pdf_presupuesto import generar_pdf_presupuesto

DIR_SALIDA = Path(__file__).resolve().parent / "salida"


def main() -> None:
    catalogo = cargar_catalogo()

    conn = conectar(DIR_SALIDA / "almacen_demo.db")
    inicializar_db(conn)
    sembrar_datos_ejemplo(conn)

    ventana_id = "V-001"
    cliente = "Cliente de ejemplo, C.A."
    orden = "OC-2026-001"

    plantilla = obtener_plantilla("corrediza_2h_fijo")
    despiece = plantilla.calcular_piezas(
        ventana_id, ancho_total_mm=1200, alto_total_mm=1500, ancho_fijo_mm=400,
    )

    print(f"Trabajo: {despiece.plantilla} — {despiece.ancho_total_mm:.0f}x{despiece.alto_total_mm:.0f} mm\n")

    print("=== 1. Piezas de aluminio necesarias ===")
    for p in despiece.piezas_aluminio:
        print(f"  [{p.modulo:10s}] {p.perfil_codigo}: {p.cantidad} x {p.longitud_mm:.0f} mm — {p.descripcion}")

    print("\n    Piezas de vidrio necesarias")
    for p in despiece.piezas_vidrio:
        print(f"  [{p.modulo:10s}] {p.tipo} {p.espesor_mm:.0f}mm: {p.cantidad} x "
              f"{p.ancho_mm:.0f}x{p.alto_mm:.0f} mm — {p.descripcion}")

    # --- Retazos disponibles en almacén, por perfil / tipo de vidrio -----
    retazos_alu = {perfil.codigo: listar_retazos_aluminio(conn, perfil.codigo) for perfil in catalogo.perfiles()}

    resultados_aluminio = optimizar_corte_aluminio(
        despiece.piezas_aluminio,
        longitud_barra_mm=catalogo.config.longitud_barra_default_mm,
        kerf_mm=catalogo.config.kerf_aluminio_mm,
        retazos_por_perfil=retazos_alu,
    )

    print("\n=== 2. Plan de corte de aluminio (barras de "
          f"{catalogo.config.longitud_barra_default_mm:.0f} mm, kerf {catalogo.config.kerf_aluminio_mm:.0f} mm) ===")
    for perfil_codigo, resultado in resultados_aluminio.items():
        print(f"  Perfil {perfil_codigo}: {resultado.barras_nuevas_usadas} barra(s) nueva(s), "
              f"{len(resultado.retazos_usados)} retazo(s) reutilizado(s), "
              f"desperdicio total {resultado.desperdicio_total_mm:.0f} mm")
        for i, barra in enumerate(resultado.barras, 1):
            piezas_fmt = ", ".join(f"{p:.0f}" for p in barra.piezas_mm)
            print(f"    Barra {i} [{barra.origen}] ({barra.longitud_barra_mm:.0f} mm): "
                  f"piezas=[{piezas_fmt}] mm  desperdicio={barra.desperdicio_mm:.0f} mm")

    tipos_vidrio_usados = {(p.tipo, p.espesor_mm) for p in despiece.piezas_vidrio}
    retazos_vid = []
    for tipo, espesor in tipos_vidrio_usados:
        retazos_vid += listar_retazos_vidrio(conn, tipo, espesor)

    resultados_vidrio = {}
    for tipo, espesor in tipos_vidrio_usados:
        vidrio_cat = catalogo.obtener_vidrio(tipo, espesor)
        parcial = optimizar_corte_vidrio(
            [p for p in despiece.piezas_vidrio if p.tipo == tipo and p.espesor_mm == espesor],
            vidrio_cat.ancho_lamina_mm, vidrio_cat.alto_lamina_mm,
            kerf_mm=catalogo.config.kerf_vidrio_mm,
            retazos=[r for r in retazos_vid if r.tipo == tipo and r.espesor_mm == espesor],
        )
        resultados_vidrio.update(parcial)

    print("\n=== 3. Plan de corte de vidrio "
          f"(kerf {catalogo.config.kerf_vidrio_mm:.0f} mm) ===")
    for (tipo, espesor), resultado in resultados_vidrio.items():
        print(f"  Vidrio {tipo} {espesor:.0f}mm: {resultado.laminas_nuevas_usadas} lámina(s) nueva(s), "
              f"{len(resultado.retazos_usados)} retazo(s) reutilizado(s)")
        for i, lamina in enumerate(resultado.laminas, 1):
            print(f"    Lámina {i} [{lamina.origen}] ({lamina.ancho_lamina_mm:.0f}x{lamina.alto_lamina_mm:.0f} mm): "
                  f"{len(lamina.piezas)} pieza(s), desperdicio {lamina.area_desperdicio_m2:.2f} m2")

    costo_material = calcular_costo_material(catalogo, resultados_aluminio, resultados_vidrio, despiece.piezas_herrajes)
    print("\n=== 4. Costo de material puro ===")
    print(f"  Aluminio: {costo_material.costo_aluminio:.2f} {catalogo.config.moneda}")
    print(f"  Vidrio:   {costo_material.costo_vidrio:.2f} {catalogo.config.moneda}")
    print(f"  Herrajes: {costo_material.costo_herrajes:.2f} {catalogo.config.moneda}")
    print(f"  TOTAL:    {costo_material.total:.2f} {catalogo.config.moneda}")

    presupuesto = calcular_presupuesto(
        costo_material,
        pct_mano_obra=catalogo.config.pct_mano_obra_default,
        pct_margen=catalogo.config.pct_margen_default,
    )
    print("\n=== 5. Presupuesto final al cliente ===")
    print(f"  Mano de obra ({presupuesto.pct_mano_obra:.1f}%): {presupuesto.monto_mano_obra:.2f} {catalogo.config.moneda}")
    print(f"  Margen ({presupuesto.pct_margen:.1f}%): {presupuesto.monto_margen:.2f} {catalogo.config.moneda}")
    print(f"  PRECIO FINAL: {presupuesto.precio_final:.2f} {catalogo.config.moneda}")

    lista_compras = generar_lista_compras(conn, resultados_aluminio, resultados_vidrio, despiece.piezas_herrajes)
    print("\n=== 6. Lista de compras (inventario de ejemplo ya sembrado) ===")
    if not lista_compras:
        print("  Todo cubierto con el inventario actual, no hace falta comprar nada.")
    for item in lista_compras:
        print(f"  Comprar {item.cantidad} x {item.descripcion} ({item.tipo})")

    DIR_SALIDA.mkdir(exist_ok=True)
    ruta_presupuesto = DIR_SALIDA / f"presupuesto_{ventana_id}.pdf"
    ruta_etiquetas = DIR_SALIDA / f"etiquetas_{ventana_id}.pdf"
    generar_pdf_presupuesto(ruta_presupuesto, cliente, orden, ventana_id, catalogo.config.moneda,
                             costo_material, presupuesto)
    n_etiquetas = generar_etiquetas_pdf(ruta_etiquetas, cliente, orden,
                                         despiece.piezas_aluminio, despiece.piezas_vidrio)
    print(f"\n=== 7. PDFs generados en {DIR_SALIDA} ===")
    print(f"  {ruta_presupuesto.name}")
    print(f"  {ruta_etiquetas.name} ({n_etiquetas} etiquetas)")

    confirmar_consumo_trabajo(conn, resultados_aluminio, resultados_vidrio, despiece.piezas_herrajes, ventana_id)
    print("\nInventario actualizado: se descontó el consumo y se registraron los sobrantes reutilizables como retazos.")

    conn.close()


if __name__ == "__main__":
    main()
