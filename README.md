# DAS Aluminios y Vidrios — Sistema de Cálculo, Presupuesto y Optimización de Corte

Fase 1: motor de cálculo por consola/script, sin interfaz gráfica todavía.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Corre el caso de prueba de aceptación (ventana corrediza de 2 hojas + paño
fijo, 1.20 x 1.50 m) de punta a punta: despiece de aluminio y vidrio, plan
de corte optimizado, costo de material, presupuesto final, lista de compras
contra un inventario de ejemplo, y PDFs de presupuesto/etiquetas en
`salida/`.

## Tests

```bash
pytest
```

## ⚠️ Antes de usar en producción

Todos los precios y medidas en `catalogo/*.json` son **placeholders de
ejemplo** (marcados con `"_nota"` en cada archivo) — reemplázalos con tus
perfiles, láminas, herrajes y costos reales del proveedor.

Las constantes de fabricación (anchos de perfil, holguras, traslapes) en
`plantillas/comun.py` (`ReglasFabricacion`) son valores típicos de
referencia — ajústalas según las plantillas de corte reales que usa el
taller antes de fabricar con estos números.

## Estructura

```
.
├── catalogo/       # perfiles, vidrio, herrajes, config general (JSON editable)
├── modelos.py      # dataclasses compartidas (piezas de aluminio/vidrio/herrajes)
├── plantillas/      # "recetas" paramétricas por tipo de ventana/puerta
├── motor/          # optimización de corte: aluminio 1D (OR-Tools), vidrio 2D (rectpack)
├── inventario/      # SQLite: retazos, stock, lista de compras, consumo
├── presupuesto/     # costo de material + presupuesto + PDF
├── etiquetas/       # PDF de etiquetas de corte
├── tests/           # pytest
└── main.py          # ejemplo de uso completo (caso de aceptación)
```

## Agregar una plantilla de producto nueva

1. Crear `plantillas/mi_producto.py` con una clase que extienda
   `PlantillaVentana` (ver `plantillas/base.py`) e implemente
   `calcular_piezas(...)`. Reutiliza los helpers de `plantillas/comun.py`
   (`marco_perimetral`, `panel_fijo`, `seccion_corrediza`, `panel_con_hoja`,
   `seccion_batientes`, `panel_proyectante`) cuando apliquen.
2. Decorarla con `@registrar_plantilla("mi_producto")`.
3. Importar el módulo nuevo en `plantillas/__init__.py`.

## Decisiones de diseño a tener presente

- **Kerf de aluminio**: se descuenta `kerf_mm` por cada pieza cortada de una
  barra (incluida la última). Es conservador — nunca deja una barra corta,
  pero puede sobrestimar el desperdicio en un par de mm por barra.
- **Kerf de vidrio**: se infla cada pieza `kerf_mm` en ancho/alto antes de
  empacar con `rectpack`, y se descuenta al reportar la medida de corte.
- **Retazos primero**: tanto el optimizador de aluminio como el de vidrio
  reciben los retazos en almacén como "contenedores" adicionales de costo
  cero y los llenan antes de abrir barra/lámina nueva.
- **Costo de material puro**: solo cuenta las barras/láminas **nuevas** que
  hay que comprar para el trabajo (no revaloriza los retazos ya en
  almacén, que se tratan como costo hundido). Ver `presupuesto/calculo.py`.
- **Retazos de vidrio al confirmar un trabajo**: se registra como retazo
  reutilizable la franja rectangular libre a la derecha o abajo del corte
  (heurística válida para layouts tipo guillotina simples). Layouts
  irregulares no generan retazo registrado, aunque sí queda desperdicio
  real en la lámina.
