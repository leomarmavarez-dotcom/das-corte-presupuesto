# DAS Aluminios y Vidrios — Sistema de Cálculo, Presupuesto y Optimización de Corte

Este archivo es contexto persistente para Claude Code en este repo. Léelo antes de tocar cualquier archivo. Si tomas una decisión de diseño nueva, documéntala aquí antes de cerrar la tarea — la intención debe viajar en escritura al ejecutor.

## Qué es esto

Sistema en Python para DAS Aluminios y Vidrios (fabricante de ventanas/puertas/mamparas en Maracaibo). Dado el tipo de producto y las medidas de un trabajo, calcula: despiece de materiales → plan de corte optimizado (aluminio 1D + vidrio 2D) → costo y presupuesto → lista de compras vs. inventario → PDFs de presupuesto y etiquetas de corte → descuento de inventario con retazos reutilizables.

Dueño del negocio y del criterio final: Leo. Ejecución técnica vía Claude Code. Este documento existe para que no haya que re-explicar el contexto en cada sesión.

## Estado actual

- **Fase 1 completa**: motor de cálculo end-to-end funcionando, 20 tests pasando, caso de aceptación (corrediza 2h+fijo 1.20×1.50m) validado end-to-end.
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

1. `catalogo/*.json` — precios ($) de TODOS los perfiles, vidrio y herrajes siguen siendo ilustrativos (marcados con `"_nota"` en cada archivo), incluyendo los perfiles ALD-70x/72x agregados 2026-07-03 (ver punto 3). Reemplazar con costos reales del proveedor (Simes, Aldoca u otro) antes de presupuestar de verdad.
2. `plantillas/comun.py: ReglasFabricacion` — para las plantillas **batientes/proyectante** (`batiente_1h`, `batiente_4h_1proyectante`) los anchos de perfil, holguras y traslapes siguen siendo valores de referencia genéricos SIN validar — el manual de Leo no dio perfiles reales para el sistema batiente con bisagra. Para las plantillas **corredizas** ver punto 3, parcialmente validado.
3. **Geometría de la Serie Normal corrediza (agregada 2026-07-03)** — Leo pegó un manual técnico Aldoca (texto, NO el PDF — nunca llegó adjunto a la sesión, buscado en el filesystem y no está) con códigos ALD-701/702/703/704/706/709 (corrediza) y ALD-722/723/724 (proyectante): dimensiones y peso Kg/ml sí están cargados en `catalogo/perfiles.json` y son fieles a esa tabla. Pero:
   - **`costo_por_barra` de los ALD-* sigue siendo placeholder**: se calculó como `peso_kg_ml x 6.1m x $3.00/kg`, con $3.00/kg inventado (no es un precio real). Falta que Leo dé el $/kg real o el costo por barra de factura.
   - **La asignación de qué cota de cada perfil "come" hacia el vano es una interpretación mía de la tabla de texto**, no una lectura de los diagramas de corte (páginas 24/26 que Leo pidió revisar) — no vi esas páginas. Si Leo consigue mandar el PDF de verdad, hay que confirmar `ancho_cabezal_mm` (30), `ancho_sillar_mm` (41), `ancho_jamba_mm` (30), `ancho_vertical_liso_mm` (25), `ancho_vertical_gancho_mm` (38), `alto_horizontal_hoja_mm` (43) en `ReglasFabricacion` contra el plano real.
   - **`traslape_hojas_mm` (20) y `holgura_vidrio_mm` (5) siguen siendo placeholders puros** — el manual no da esos números (harían falta los diagramas de "cuánto muerde el vidrio").
   - **La generalización a 3+ hojas** (hojas de extremo = 1 liso + 1 gancho, hojas intermedias = 2 gancho) es una extrapolación mía de la fórmula del manual, que solo cubre 2 hojas explícitamente — sin confirmar con Leo.
   - **El junquillo de la Serie Normal corrediza sigue siendo `JQ-01` genérico** — el manual no dice qué perfil sostiene el vidrio ahí. `ALD-707 "Perfil Tapa"` es candidato por el nombre pero no está confirmado, no asignarlo sin que Leo lo diga.
   - **Cantidades de accesorios de corredera** (2 ruedas RUEDA-CORREDIZA por hoja, 1 CERRADURA-CORREDIZA por sección) ahora sí se cuentan (antes no se contaban nada), pero son cantidades supuestas típicas de la industria, no confirmadas por Leo. FELPA y "gomas" que Leo mencionó siguen sin implementar (gomas ni siquiera tiene código en `herrajes.json` todavía).
   - **Puerta de baño (página 99 del catálogo Aldoca)**: el manual que pegó Leo NO trae códigos/dimensiones para ese sistema, solo dice "ver págs. 98-99". `corrediza_nh` se sigue usando como aproximación para puerta de baño corrediza, sin perfiles propios.
   - **El marco de `proyectante_4h_1p`** sigue en `MC-01` genérico — ALD-723 (perfil marco proyectante real) está en el catálogo pero no wireado, porque ese marco se comparte con las hojas batientes de la misma plantilla (sin perfil real para esas todavía).

Si una tarea futura toca estos archivos, señalar explícitamente en la respuesta qué de esto sigue sin validar, no asumir que ya se resolvió.

## Decisiones de diseño ya tomadas (no revisar sin motivo)

- Costo de material puro solo cuenta barras/láminas nuevas que hay que comprar; los retazos ya en almacén se tratan como costo hundido (no se revalorizan al consumirse). Alternativa documentada en README si Leo pide cambiarlo.
- Prioridad de retazos: el optimizador considera primero el stock de retazos en inventario antes de calcular barra/lámina nueva a comprar.
- Kerf (pérdida de material por corte) es configurable, no hardcodeado.
- Detalle completo de estas decisiones (kerf, heurística de retazos de vidrio, prioridad de stock) está en `README.md` — consultar ahí antes de cambiar comportamiento del motor.

## Cómo extender

- Agregar una plantilla nueva (tercer tipo de producto, ej. puerta batiente o mampara de baño): nueva clase en `plantillas/`, decorar con `@registrar_plantilla("clave")`, importar en `plantillas/__init__.py`. Reutilizar los helpers geométricos existentes en `plantillas/comun.py` — no duplicar lógica de cálculo de traslapes/holguras entre plantillas.
- Antes de tocar el motor de optimización (`motor/`): correr los tests existentes primero (`pytest`), y no romper el caso de aceptación end-to-end.

## Plantillas registradas

- `corrediza_2h_fijo` — ventana corrediza de 2 hojas + paño fijo lateral (plantilla original, caso de aceptación).
- `batiente_4h_1proyectante` — ventana de 4 hojas batientes + 1 módulo proyectante superior (plantilla original).
- `corrediza_nh` (agregada 2026-07-02) — corrediza genérica de N hojas sin paño fijo (parámetro `num_hojas`, default 2). Reusa `seccion_corrediza` de `plantillas/comun.py` sin modificarla. Sirve tanto para ventanas corredizas como para puertas corredizas (ej. puerta de baño) — el sistema no distingue "ventana" de "puerta" a nivel de perfil todavía, es la misma geometría con distinto vidrio/tamaño.
- `batiente_1h` (agregada 2026-07-02) — batiente de 1 sola hoja (puerta o ventana), reusa `seccion_batientes` con `num_hojas=1`. Por defecto usa vidrio Templado 6mm (vidrio de seguridad, típico en puertas) en vez del Claro 4mm default de las demás plantillas. **No modela panel ciego inferior** — asume la hoja 100% vidrio sostenido por junquillo; si DAS fabrica puertas batientes con panel ciego (zócalo de aluminio sin vidrio en la parte baja), esta plantilla no lo captura todavía y hay que extenderla.
- Ninguna plantilla modela **color de perfil** (ej. "blanco") — el catálogo (`catalogo/perfiles.json`) no tiene variantes por color, solo un código de perfil con un costo. Si DAS cobra distinto por color, hace falta agregar esa dimensión al catálogo antes de presupuestar con color real.
- `demo_presupuesto_leo.py` en la raíz: script de prueba que arma una orden de 5 aberturas (tamaños reales que dio Leo) combinando el corte entre todas para mostrar el flujo completo con precios placeholder — no es parte del flujo de producción, es solo demo.
- **2026-07-03**: `corrediza_2h_fijo` y `corrediza_nh` pasaron de perfiles genéricos (`MC-01`/`HJ-01`) a los perfiles reales de la Serie Normal Aldoca (`ALD-701`..`709`) con roles distintos por pieza (cabezal/sillar/jamba en el marco; vertical liso/vertical gancho/horizontal en la hoja) — ver el punto 3 de "Pendiente de validar" arriba para el detalle de qué de esto está confirmado y qué no. `marco_perimetral()` y `seccion_corrediza()` en `plantillas/comun.py` cambiaron de firma (perfil único → perfiles por rol) — las plantillas batientes (`batiente_1h`, `batiente_4h_1proyectante`) siguen llamándolas con un solo perfil genérico y no cambiaron de comportamiento.

## Convenciones de trabajo

- Español para nombres de negocio/dominio (catálogo, plantillas, presupuesto); inglés está bien para nombres técnicos genéricos si ya existen en el código.
- Cualquier decisión de diseño que no esté ya documentada aquí o en el README, documentarla al cerrarla — no dejarla solo en el mensaje de commit.
- Placeholders de datos (precios, medidas) siempre marcados explícitamente en el archivo mismo (ej. `"_nota"` en JSON), nunca silenciosos.
