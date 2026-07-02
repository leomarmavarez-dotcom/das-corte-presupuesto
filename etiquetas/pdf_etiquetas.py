"""Generación de etiquetas de corte imprimibles (una por pieza) con reportlab."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from modelos import PiezaAluminio, PiezaVidrio

ANCHO_ETIQUETA = 65 * mm
ALTO_ETIQUETA = 35 * mm
MARGEN = 8 * mm
ESPACIO = 3 * mm


@dataclass
class EtiquetaPieza:
    cliente: str
    orden: str
    ventana_id: str
    modulo: str
    codigo: str
    descripcion: str
    medida: str


def _etiquetas_desde_despiece(cliente: str, orden: str, piezas_aluminio: list[PiezaAluminio],
                               piezas_vidrio: list[PiezaVidrio]) -> list[EtiquetaPieza]:
    etiquetas = []
    for p in piezas_aluminio:
        for _ in range(p.cantidad):
            etiquetas.append(EtiquetaPieza(
                cliente, orden, p.ventana_id, p.modulo, p.perfil_codigo, p.descripcion,
                f"{p.longitud_mm:.0f} mm"))
    for p in piezas_vidrio:
        for _ in range(p.cantidad):
            etiquetas.append(EtiquetaPieza(
                cliente, orden, p.ventana_id, p.modulo, f"{p.tipo} {p.espesor_mm:.0f}mm", p.descripcion,
                f"{p.ancho_mm:.0f} x {p.alto_mm:.0f} mm"))
    return etiquetas


def _dibujar_etiqueta(c: canvas.Canvas, x: float, y: float, etiqueta: EtiquetaPieza) -> None:
    c.rect(x, y, ANCHO_ETIQUETA, ALTO_ETIQUETA)
    tx = x + 3 * mm
    ty = y + ALTO_ETIQUETA - 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(tx, ty, etiqueta.cliente[:28])
    ty -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawString(tx, ty, f"Orden: {etiqueta.orden}   Ventana: {etiqueta.ventana_id}")
    ty -= 5 * mm
    c.drawString(tx, ty, f"Módulo: {etiqueta.modulo}")
    ty -= 5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(tx, ty, f"{etiqueta.codigo} - {etiqueta.descripcion}"[:38])
    ty -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(tx, ty, etiqueta.medida)


def generar_etiquetas_pdf(output_path: str | Path, cliente: str, orden: str,
                           piezas_aluminio: list[PiezaAluminio], piezas_vidrio: list[PiezaVidrio]) -> int:
    """Genera un PDF con una etiqueta por cada pieza cortada. Devuelve la
    cantidad de etiquetas generadas."""
    etiquetas = _etiquetas_desde_despiece(cliente, orden, piezas_aluminio, piezas_vidrio)
    if not etiquetas:
        raise ValueError("No hay piezas para generar etiquetas")

    ancho_pagina, alto_pagina = A4
    cols = int((ancho_pagina - 2 * MARGEN) // (ANCHO_ETIQUETA + ESPACIO))
    filas = int((alto_pagina - 2 * MARGEN) // (ALTO_ETIQUETA + ESPACIO))
    por_pagina = max(1, cols * filas)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)

    for indice, etiqueta in enumerate(etiquetas):
        pos_en_pagina = indice % por_pagina
        if indice > 0 and pos_en_pagina == 0:
            c.showPage()
        fila = pos_en_pagina // cols
        col = pos_en_pagina % cols
        x = MARGEN + col * (ANCHO_ETIQUETA + ESPACIO)
        y = alto_pagina - MARGEN - ALTO_ETIQUETA - fila * (ALTO_ETIQUETA + ESPACIO)
        _dibujar_etiqueta(c, x, y, etiqueta)

    c.save()
    return len(etiquetas)
