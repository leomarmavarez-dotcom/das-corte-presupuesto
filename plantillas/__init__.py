"""Registro de plantillas paramétricas de productos.

Importar este paquete registra automáticamente todas las plantillas
disponibles (cada módulo se auto-registra con @registrar_plantilla).
Para agregar un producto nuevo: crear un archivo aquí con una clase que
extienda PlantillaVentana, decorarla con @registrar_plantilla("clave") e
importarlo abajo.
"""
from plantillas import batiente_1h, corrediza_2h_fijo, corrediza_nh, proyectante_4h_1p  # noqa: F401
from plantillas.registro import listar_plantillas, obtener_plantilla, registrar_plantilla

__all__ = ["listar_plantillas", "obtener_plantilla", "registrar_plantilla"]
