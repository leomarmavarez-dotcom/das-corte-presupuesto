"""Cálculo de costo de material puro y presupuesto final al cliente.

Decisión de diseño: el costo de material solo cuenta las barras/láminas
NUEVAS que hay que comprar para este trabajo (barras_nuevas_usadas /
laminas_nuevas_usadas que devuelve el motor de corte). Los retazos que ya
están en almacén se consideran costo hundido de un trabajo anterior y no se
recargan de nuevo aquí. Si prefieres valorizar también el material que sale
de retazos, avisa para agregar esa opción.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from catalogo.loader import Catalogo
from modelos import PiezaHerraje
from motor.corte_aluminio import ResultadoCorteAluminio
from motor.corte_vidrio import ResultadoCorteVidrio


@dataclass
class CostoMaterial:
    costo_aluminio: float = 0.0
    costo_vidrio: float = 0.0
    costo_herrajes: float = 0.0
    detalle_aluminio: dict = field(default_factory=dict)
    detalle_vidrio: dict = field(default_factory=dict)
    detalle_herrajes: dict = field(default_factory=dict)

    @property
    def total(self) -> float:
        return self.costo_aluminio + self.costo_vidrio + self.costo_herrajes


def calcular_costo_material(catalogo: Catalogo,
                             resultados_aluminio: dict[str, ResultadoCorteAluminio],
                             resultados_vidrio: dict[tuple[str, float], ResultadoCorteVidrio],
                             herrajes_necesarios: list[PiezaHerraje]) -> CostoMaterial:
    costo = CostoMaterial()

    for perfil_codigo, resultado in resultados_aluminio.items():
        perfil = catalogo.obtener_perfil(perfil_codigo)
        n_barras = resultado.barras_nuevas_usadas
        subtotal = n_barras * perfil.costo_por_barra
        costo.detalle_aluminio[perfil_codigo] = {
            "barras_nuevas": n_barras,
            "costo_barra": perfil.costo_por_barra,
            "subtotal": subtotal,
        }
        costo.costo_aluminio += subtotal

    for (tipo, espesor), resultado in resultados_vidrio.items():
        vidrio = catalogo.obtener_vidrio(tipo, espesor)
        n_laminas = resultado.laminas_nuevas_usadas
        area_m2 = n_laminas * (vidrio.ancho_lamina_mm * vidrio.alto_lamina_mm) / 1_000_000
        subtotal = area_m2 * vidrio.costo_m2
        costo.detalle_vidrio[(tipo, espesor)] = {
            "laminas_nuevas": n_laminas,
            "area_m2": area_m2,
            "costo_m2": vidrio.costo_m2,
            "subtotal": subtotal,
        }
        costo.costo_vidrio += subtotal

    necesidades: dict[str, int] = {}
    for h in herrajes_necesarios:
        necesidades[h.codigo] = necesidades.get(h.codigo, 0) + h.cantidad
    for codigo, cantidad in necesidades.items():
        herraje = catalogo.obtener_herraje(codigo)
        subtotal = cantidad * herraje.costo_unitario
        costo.detalle_herrajes[codigo] = {
            "cantidad": cantidad,
            "costo_unitario": herraje.costo_unitario,
            "subtotal": subtotal,
        }
        costo.costo_herrajes += subtotal

    return costo


@dataclass
class Presupuesto:
    costo_material: CostoMaterial
    pct_mano_obra: float
    pct_margen: float

    @property
    def monto_mano_obra(self) -> float:
        return self.costo_material.total * self.pct_mano_obra / 100

    @property
    def subtotal_con_mano_obra(self) -> float:
        return self.costo_material.total + self.monto_mano_obra

    @property
    def monto_margen(self) -> float:
        return self.subtotal_con_mano_obra * self.pct_margen / 100

    @property
    def precio_final(self) -> float:
        return self.subtotal_con_mano_obra + self.monto_margen


def calcular_presupuesto(costo_material: CostoMaterial, pct_mano_obra: float, pct_margen: float) -> Presupuesto:
    return Presupuesto(costo_material, pct_mano_obra, pct_margen)
