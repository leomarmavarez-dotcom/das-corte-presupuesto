"""Demo de prueba pedida por Leo: presupuesto de una orden con 5 aberturas
(3 ventanas corredizas, 1 puerta de baño corrediza, 1 puerta batiente),
usando TODAVÍA los precios y medidas PLACEHOLDER del catálogo (ver
CLAUDE.md / README.md) — este número no es un presupuesto real hasta que
se carguen los precios y las ReglasFabricacion reales del taller.

Las 5 aberturas se cortan como una sola orden: el optimizador comparte
barras de aluminio entre las distintas ventanas/puertas cuando usan el
mismo perfil, en vez de calcular cada una por separado.

Ejecutar con: python demo_presupuesto_leo.py
"""
from __future__ import annotations

from pathlib import Path

import plantillas  # noqa: F401  (importarlo registra las plantillas disponibles)
from catalogo.loader import cargar_catalogo
from etiquetas.pdf_etiquetas import generar_etiquetas_pdf
from motor.corte_aluminio import optimizar_corte_aluminio
from motor.corte_vidrio import optimizar_corte_vidrio
from plantillas.registro import obtener_plantilla
from presupuesto.calculo import calcular_costo_material, calcular_presupuesto
from presupuesto.pdf_presupuesto import generar_pdf_presupuesto

DIR_SALIDA = Path(__file__).resolve().parent / "salida"

TRABAJOS = [
    dict(id="V-001", plantilla="corrediza_nh", ancho_mm=4250, alto_mm=1430,
         kwargs=dict(num_hojas=4), desc="Ventana corrediza 4 hojas"),
    dict(id="V-002", plantilla="corrediza_nh", ancho_mm=1500, alto_mm=1300,
         kwargs=dict(num_hojas=2), desc="Ventana corrediza 2 hojas"),
    dict(id="V-003", plantilla="corrediza_nh", ancho_mm=600, alto_mm=450,
         kwargs=dict(num_hojas=2), desc="Ventana corrediza 2 hojas (ventilación)"),
    dict(id="V-004", plantilla="corrediza_nh", ancho_mm=1600, alto_mm=1800,
         kwargs=dict(num_hojas=2, tipo_vidrio="Templado", espesor_vidrio_mm=6.0),
         desc="Puerta de baño corrediza 2 hojas"),
    dict(id="V-005", plantilla="batiente_1h", ancho_mm=800, alto_mm=2100,
         kwargs=dict(), desc="Puerta batiente 1 hoja"),
]


def main() -> None:
    catalogo = cargar_catalogo()

    print("=== Despiece por abertura ===")
    despieces = []
    for t in TRABAJOS:
        plantilla = obtener_plantilla(t["plantilla"])
        despiece = plantilla.calcular_piezas(
            t["id"], ancho_total_mm=t["ancho_mm"], alto_total_mm=t["alto_mm"], **t["kwargs"])
        despieces.append(despiece)
        print(f"  [{t['id']}] {t['desc']} ({t['ancho_mm'] / 1000:.2f} x {t['alto_mm'] / 1000:.2f} m, "
              f"plantilla '{t['plantilla']}'): "
              f"{sum(p.cantidad for p in despiece.piezas_aluminio)} piezas de aluminio, "
              f"{sum(p.cantidad for p in despiece.piezas_vidrio)} piezas de vidrio, "
              f"{sum(p.cantidad for p in despiece.piezas_herrajes)} piezas de herraje")

    piezas_aluminio = [p for d in despieces for p in d.piezas_aluminio]
    piezas_vidrio = [p for d in despieces for p in d.piezas_vidrio]
    piezas_herrajes = [p for d in despieces for p in d.piezas_herrajes]

    resultados_aluminio = optimizar_corte_aluminio(
        piezas_aluminio,
        longitud_barra_mm=catalogo.config.longitud_barra_default_mm,
        kerf_mm=catalogo.config.kerf_aluminio_mm,
    )

    print(f"\n=== Plan de corte de aluminio (barras de {catalogo.config.longitud_barra_default_mm:.0f} mm, "
          f"kerf {catalogo.config.kerf_aluminio_mm:.0f} mm), combinando las {len(TRABAJOS)} aberturas ===")
    for perfil_codigo, resultado in resultados_aluminio.items():
        print(f"  Perfil {perfil_codigo}: {resultado.barras_nuevas_usadas} barra(s) nueva(s), "
              f"desperdicio total {resultado.desperdicio_total_mm:.0f} mm")

    tipos_vidrio_usados = {(p.tipo, p.espesor_mm) for p in piezas_vidrio}
    resultados_vidrio = {}
    for tipo, espesor in tipos_vidrio_usados:
        vidrio_cat = catalogo.obtener_vidrio(tipo, espesor)
        parcial = optimizar_corte_vidrio(
            [p for p in piezas_vidrio if p.tipo == tipo and p.espesor_mm == espesor],
            vidrio_cat.ancho_lamina_mm, vidrio_cat.alto_lamina_mm,
            kerf_mm=catalogo.config.kerf_vidrio_mm,
        )
        resultados_vidrio.update(parcial)

    print(f"\n=== Plan de corte de vidrio (kerf {catalogo.config.kerf_vidrio_mm:.0f} mm) ===")
    for (tipo, espesor), resultado in resultados_vidrio.items():
        print(f"  Vidrio {tipo} {espesor:.0f}mm: {resultado.laminas_nuevas_usadas} lámina(s) nueva(s)")

    costo_material = calcular_costo_material(catalogo, resultados_aluminio, resultados_vidrio, piezas_herrajes)
    print("\n=== Costo de material puro (toda la orden) ===")
    print(f"  Aluminio: {costo_material.costo_aluminio:.2f} {catalogo.config.moneda}")
    print(f"  Vidrio:   {costo_material.costo_vidrio:.2f} {catalogo.config.moneda}")
    print(f"  Herrajes: {costo_material.costo_herrajes:.2f} {catalogo.config.moneda}")
    print(f"  TOTAL:    {costo_material.total:.2f} {catalogo.config.moneda}")

    presupuesto = calcular_presupuesto(
        costo_material,
        pct_mano_obra=catalogo.config.pct_mano_obra_default,
        pct_margen=catalogo.config.pct_margen_default,
    )
    print("\n=== Presupuesto final al cliente (toda la orden) ===")
    print(f"  Mano de obra ({presupuesto.pct_mano_obra:.1f}%): {presupuesto.monto_mano_obra:.2f} {catalogo.config.moneda}")
    print(f"  Margen ({presupuesto.pct_margen:.1f}%): {presupuesto.monto_margen:.2f} {catalogo.config.moneda}")
    print(f"  PRECIO FINAL: {presupuesto.precio_final:.2f} {catalogo.config.moneda}")

    DIR_SALIDA.mkdir(exist_ok=True)
    ruta_presupuesto = DIR_SALIDA / "presupuesto_demo_leo.pdf"
    ruta_etiquetas = DIR_SALIDA / "etiquetas_demo_leo.pdf"
    generar_pdf_presupuesto(ruta_presupuesto, "Cliente de prueba", "DEMO-2026-001", "ORDEN-5-ABERTURAS",
                             catalogo.config.moneda, costo_material, presupuesto)
    n_etiquetas = generar_etiquetas_pdf(ruta_etiquetas, "Cliente de prueba", "DEMO-2026-001",
                                         piezas_aluminio, piezas_vidrio)
    print(f"\n=== PDFs generados en {DIR_SALIDA} ===")
    print(f"  {ruta_presupuesto.name}")
    print(f"  {ruta_etiquetas.name} ({n_etiquetas} etiquetas)")

    print("\n*** RECORDATORIO: precios de catalogo/*.json y medidas de ReglasFabricacion "
          "siguen siendo PLACEHOLDERS de ejemplo (ver CLAUDE.md) — esto NO es un "
          "presupuesto real todavía. ***")


if __name__ == "__main__":
    main()
