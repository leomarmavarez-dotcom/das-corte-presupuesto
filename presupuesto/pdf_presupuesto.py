"""Generación del presupuesto en PDF para el cliente, con reportlab."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from presupuesto.calculo import CostoMaterial, Presupuesto


def generar_pdf_presupuesto(output_path: str | Path, cliente: str, orden: str, ventana_id: str,
                             moneda: str, costo_material: CostoMaterial, presupuesto: Presupuesto) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter)
    ancho, alto = letter
    y = alto - 25 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "DAS Aluminios y Vidrios — Presupuesto")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Cliente: {cliente}    Orden: {orden}    Ventana: {ventana_id}")
    y -= 12 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Costo de material puro")
    y -= 7 * mm
    c.setFont("Helvetica", 9)

    for codigo, det in costo_material.detalle_aluminio.items():
        c.drawString(24 * mm, y,
                     f"Aluminio {codigo}: {det['barras_nuevas']} barra(s) nueva(s) x "
                     f"{det['costo_barra']:.2f} {moneda} = {det['subtotal']:.2f} {moneda}")
        y -= 6 * mm
    for (tipo, esp), det in costo_material.detalle_vidrio.items():
        c.drawString(24 * mm, y,
                     f"Vidrio {tipo} {esp:.0f}mm: {det['laminas_nuevas']} lámina(s) nueva(s), "
                     f"{det['area_m2']:.2f} m2 x {det['costo_m2']:.2f} {moneda} = {det['subtotal']:.2f} {moneda}")
        y -= 6 * mm
    for codigo, det in costo_material.detalle_herrajes.items():
        c.drawString(24 * mm, y,
                     f"Herraje {codigo}: {det['cantidad']} x {det['costo_unitario']:.2f} {moneda} = "
                     f"{det['subtotal']:.2f} {moneda}")
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Subtotal material: {costo_material.total:.2f} {moneda}")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Mano de obra ({presupuesto.pct_mano_obra:.1f}%): "
                              f"{presupuesto.monto_mano_obra:.2f} {moneda}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Margen ({presupuesto.pct_margen:.1f}%): {presupuesto.monto_margen:.2f} {moneda}")
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, f"PRECIO FINAL: {presupuesto.precio_final:.2f} {moneda}")

    c.save()
