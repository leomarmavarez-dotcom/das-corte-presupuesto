# DAS Aluminios y Vidrios — Sistema de Cálculo, Presupuesto y Optimización de Corte

Este archivo es contexto persistente para Claude Code en este repo. Léelo antes de tocar cualquier archivo. Si tomas una decisión de diseño nueva, documéntala aquí antes de cerrar la tarea — la intención debe viajar en escritura al ejecutor.

## Qué es esto

Sistema en Python para DAS Aluminios y Vidrios (fabricante de ventanas/puertas/mamparas en Maracaibo). Dado el tipo de producto y las medidas de un trabajo, calcula: despiece de materiales → plan de corte optimizado (aluminio 1D + vidrio 2D) → costo y presupuesto → lista de compras vs. inventario → PDFs de presupuesto y etiquetas de corte → descuento de inventario con retazos reutilizables.

Dueño del negocio y del criterio final: Leo. Ejecución técnica vía Claude Code. Este documento existe para que no haya que re-explicar el contexto en cada sesión.

## Estado actual

- **Fase 1 completa**: motor de cálculo end-to-end funcionando, 17 tests pasando, caso de aceptación (corrediza 2h+fijo 1.20×1.50m) validado end-to-end.
- **Fase 2** (pendiente, no empezar sin luz verde explícita de Leo): dashboard/configurador visual tipo "armar módulos" conectado en vivo al motor de la Fase 1.
- **Fase 3** (pendiente, no empezar sin luz verde explícita de Leo): integración con Blender (`bpy`) para simulación 3D del ensamble a partir de los datos de despiece.

**No avances de fase sin que Leo lo pida explícitamente** — cada fase se revisa y aprueba antes de seguir.

> Este repo (`das-corte-presupuesto`) contiene **solo** el sistema de cálculo/corte/presupuesto en Python. La página web/landing de DAS es un proyecto aparte, en el repo `ventanas-servicio` — no mezclar código de un repo en el otro.

## Arquitectura

```
.
├── catalogo/           # perfiles, vidrio, herrajes — JSON editable, con costos
├── plantillas/         # lógica paramétrica por tipo de producto
├── motor/              # optimización de corte (OR-Tools 1D aluminio, rectpack 2D vidrio)
├── inventario/         # SQLite — stock y retazos reutilizables
├── presupuesto/        # cálculo de costos + PDF (reportlab)
├── etiquetas/           # PDF de etiquetas de corte (reportlab)
├── tests/               # pytest, incluye caso de aceptación end-to-end
├── main.py              # punto de entrada / ejemplo de uso completo
└── README.md            # instrucciones + decisiones de diseño detalladas
```

Stack: Python 3.11+, Google OR-Tools (CP-SAT) para cutting stock 1D de aluminio, `rectpack` para nesting 2D de vidrio, `reportlab` para PDFs, SQLite para inventario.

Principio de librerías: si existe una librería madura y gratuita que resuelve el problema (OR-Tools, rectpack), se usa esa antes que escribir el algoritmo desde cero.

## ⚠️ Pendiente de validar con datos reales — NO asumir que están correctos

Estos valores son placeholders o aproximaciones puestas para que el sistema corra con cifras no-cero. Cualquier presupuesto real generado con los valores actuales no es confiable hasta que Leo los reemplace:

1. `catalogo/*.json` — precios de perfiles, vidrio y herrajes son ilustrativos (marcados con `"_nota"` en cada archivo). Reemplazar con costos reales del proveedor (Simes u otro) antes de presupuestar de verdad.
2. `plantillas/comun.py: ReglasFabricacion` — anchos de perfil, holguras, traslape entre hojas son valores típicos de referencia, no las medidas exactas de cómo fabrica DAS. Validar geometría de las 2 plantillas existentes contra la práctica real del taller.

Si una tarea futura toca estos archivos, señalar explícitamente en la respuesta que sigue habiendo valores sin validar, no asumir que ya se resolvió.

## Decisiones de diseño ya tomadas (no revisar sin motivo)

- Costo de material puro solo cuenta barras/láminas nuevas que hay que comprar; los retazos ya en almacén se tratan como costo hundido (no se revalorizan al consumirse). Alternativa documentada en README si Leo pide cambiarlo.
- Prioridad de retazos: el optimizador considera primero el stock de retazos en inventario antes de calcular barra/lámina nueva a comprar.
- Kerf (pérdida de material por corte) es configurable, no hardcodeado.
- Detalle completo de estas decisiones (kerf, heurística de retazos de vidrio, prioridad de stock) está en `README.md` — consultar ahí antes de cambiar comportamiento del motor.

## Cómo extender

- Agregar una plantilla nueva (tercer tipo de producto, ej. puerta batiente o mampara de baño): nueva clase en `plantillas/`, decorar con `@registrar_plantilla("clave")`, importar en `plantillas/__init__.py`. Reutilizar los helpers geométricos existentes en `plantillas/comun.py` — no duplicar lógica de cálculo de traslapes/holguras entre plantillas.
- Antes de tocar el motor de optimización (`motor/`): correr los 17 tests existentes primero (`pytest`), y no romper el caso de aceptación end-to-end.

## Convenciones de trabajo

- Español para nombres de negocio/dominio (catálogo, plantillas, presupuesto); inglés está bien para nombres técnicos genéricos si ya existen en el código.
- Cualquier decisión de diseño que no esté ya documentada aquí o en el README, documentarla al cerrarla — no dejarla solo en el mensaje de commit.
- Placeholders de datos (precios, medidas) siempre marcados explícitamente en el archivo mismo (ej. `"_nota"` en JSON), nunca silenciosos.
