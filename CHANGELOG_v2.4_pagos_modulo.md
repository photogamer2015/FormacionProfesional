# Versión 2.4 — Visual binario en Pagos por Módulo + fix de exports

Fecha: 09/05/2026

## Resumen

Dos arreglos en la pantalla **`/pagos/por-modulo/`** y sus
exportaciones a Excel y PDF.

> *El equipo y el cliente solo necesitan ver, módulo por módulo, si
> está pagado o no. Los detalles de cuánto se ha abonado parcial van
> en una notita pequeña debajo.*

---

## Bug 1 — Excel y PDF reventaban con filtro de estado por módulo

`pagos_por_modulo_export_excel` y `pagos_por_modulo_export_pdf`
pasaban un `kwarg` que la función receptora no aceptaba:

```python
# ANTES (TypeError)
_construir_matriz_pagos(..., estado_modulo_filtro=filtros['estado_modulo'])

# AHORA
_construir_matriz_pagos(..., filtro_modulo_estado=filtros['filtro_modulo_estado'])
```

Adicionalmente, el helper `_export_pagos_modulo_filtros` leía la clave
GET equivocada (`estado_modulo`) cuando el formulario manda
`filtro_modulo_estado`. Resultado neto: hacer click en 📊 Excel o 📄
PDF con cualquier filtro de estado activo crasheaba.

Ahora ambos endpoints devuelven 200 OK y respetan el filtro.

---

## Bug 2 — Las celdas de "Parcial" confundían al equipo y al cliente

**Antes:** un abono de $20 sobre un módulo de $25 (curso $100 / 4
módulos) se renderizaba como un cuadro **amarillo** con `◐ $20,00 de
$25,00`. Visualmente parecía que ese módulo "ya tenía avance" cuando
la realidad financiera es que el módulo no estaba cubierto todavía.

**Ahora:** la matriz muestra solo **2 estados visuales** —
✓ Pagado (verde) o ○ Sin pagar (rojo). Cuando hay un abono parcial
que no cubre el módulo, la celda se muestra como Sin pagar pero con
una nota pequeña en gris debajo:

```
○ Sin pagar
$25,00
abonó $20,00
09/05/2026
```

Así el equipo no se confunde ("¿está pagado o no?") y al mismo tiempo
no se pierde la trazabilidad del dinero que sí entró.

### Lo que NO cambió (a propósito)

A petición expresa, los siguientes lugares **siguen mostrando los 3
estados** porque siguen siendo útiles para reportes y filtros:

- Las **tarjetas resumen del top** (`✓ X · ◐ Y · ○ Z` por módulo).
- El **filtro "Estado por Módulo"** del formulario, que permite
  filtrar por Pagado, Parcial o Pendiente.
- Las exportaciones a Excel y PDF mantienen los 3 estados detallados
  para la contabilidad.
- El método del modelo `desglose_pagos_por_modulo()` sigue devolviendo
  los 3 estados — solo el render del template colapsa "Parcial" a
  "Sin pagar + nota".

---

## Aclaración importante sobre la lógica de la matriz

La lógica **NO distribuye** la reserva al Módulo 1 ni derrama
excedentes al siguiente módulo. Solo se cuentan en la matriz los
abonos asignados explícitamente a un módulo (tipo `por_modulo` o
`recuperacion` con `numero_modulo`). Los abonos libres (tipo `abono` o
`pago_completo` sin módulo) suman al saldo total pero no entran a la
matriz; quedan visibles como "Reservado: $X" debajo del valor
pagado de la fila.

Una versión preliminar de este CHANGELOG describía una lógica de
distribución/derrame que **nunca se implementó así** — fue una
documentación errónea que se corrigió en v2.5. Si necesita la lógica
correcta y oficial, consulte la sección "💵 Pagos por Módulo" del
README.

---

## Archivos tocados

```
academia/
└── views_pagos.py           # Corrige los kwargs de los exports Excel/PDF
                            # Corrige el nombre de la GET-key en _export_pagos_modulo_filtros

templates/pagos/
└── por_modulo.html          # Visual binario en la matriz: Parcial → Sin pagar + nota
```

Sin migraciones nuevas.
