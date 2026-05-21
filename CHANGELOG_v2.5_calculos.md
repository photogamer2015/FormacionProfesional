# Versión 2.5 — Corrección de cálculos financieros y validaciones

Fecha: 13/05/2026

## Resumen

Cuatro correcciones encontradas en una auditoría completa del sistema.
Dos eran bugs reales que afectaban dinero reportado; uno era una
validación faltante; el último era documentación que mentía sobre el
comportamiento del sistema.

---

## Bug 1 — Doble conteo de ingresos en el panel administrativo ⚠️ Crítico

**Síntoma:** cada vez que se editaba y guardaba una matrícula que ya
tenía abonos, los ingresos del mes en `/admin-panel/` subían
artificialmente — aunque no hubiera entrado un solo dólar nuevo.

**Reproducción:** matrícula con $15 pagados (un abono real). Editarla
sin cambios → los ingresos del mes pasaban de $115 a $130
(duplicación de $15).

**Causa raíz:**

1. Cuando se guarda una `Matricula`, su método `_sync_comprobante()`
   crea o actualiza un `Comprobante` espejo con `pago_abono =
   valor_pagado`.
2. `_ingresos_periodo` en `views_admin.py` sumaba SIN distinguir:
   - Todos los `Abono` (suma A)
   - Todos los `Comprobante.pago_abono` (suma B)
   - Todos los `Adicional.valor` (suma C)
3. Como los Comprobantes-espejo reflejan el `valor_pagado` que ya es
   la suma de los Abonos de esa matrícula, el dinero se contaba en A
   y otra vez en B.
4. Los Comprobantes-espejo recién creados arrancan con `pago_abono=0`
   (porque la matrícula nueva tiene `valor_pagado=0`), así que el bug
   solo se manifestaba cuando alguien volvía a guardar la matrícula
   después de que se hubieran registrado abonos.

**Solución:**

`_ingresos_periodo` y el cálculo del total histórico (`total_ventas_hist`)
ahora filtran **solo Comprobantes manuales** — los que NO tienen
matrícula vinculada (`matricula__isnull=True`):

```python
ventas = Comprobante.objects.filter(
    fecha_inscripcion__gte=desde, fecha_inscripcion__lte=hasta,
    matricula__isnull=True,
).aggregate(s=Sum('pago_abono'))['s'] or Decimal('0.00')
```

Los pagos de matrículas registradas en el sistema ya están contados
una sola vez, vía Abonos. Los Comprobantes manuales (cargados desde
el módulo Comprobantes sin crear matrícula) son una fuente
independiente y se siguen sumando.

**Por cobrar también se reescribió** para usar las dos fuentes que no
se solapan: saldos pendientes de matrículas activas (la fuente de
verdad para matrículas) + diferencias de comprobantes manuales.

El **export CSV mensual** (`export_reporte_mes`) ahora también
muestra solo los comprobantes manuales en la sección "VENTAS POR
COMPROBANTE", para que no haya conteo visual duplicado en el reporte.

---

## Bug 2 — Precisión decimal en el valor por módulo ⚠️ Crítico

**Síntoma:** en cursos cuyo valor neto no se divide exacto entre el
número de módulos (ej. $100 / 3 = $33.33333...), los módulos nunca
aparecían como "Pagado" aunque el estudiante hubiera pagado todo el
valor del curso.

**Reproducción:** curso $100, 3 módulos. Estudiante paga $33.33 +
$33.33 + $33.34 = $100 (saldo $0). El sistema mostraba:

| | Mód. 1 | Mód. 2 | Mód. 3 |
|---|---|---|---|
| Antes | ◐ Parcial $33.33 | ◐ Parcial $33.33 | ✓ Pagado $33.34 |

Los dos primeros nunca llegaban a Pagado porque `$33.33 < $33.333...`

**Causa raíz:** `valor_modulo` se calculaba como
`self.valor_neto / Decimal(n_mod)` sin redondear, conservando todos
los decimales del Decimal. Los pagos reales solo manejan 2 decimales
(USD), así que la comparación nunca cuadraba.

**Solución:** `desglose_pagos_por_modulo()` (y los cálculos paralelos
en `_construir_matriz_pagos` y `_calcular_alertas_pago`) ahora
redondean `valor_modulo` a 2 decimales con `.quantize(Decimal('0.01'))`.

Para el caso del ejemplo, ahora los tres módulos aparecen como Pagado.

**Nota:** la suma de los `valor_modulo` redondeados puede quedar 1
centavo arriba o abajo del valor neto en cursos no divisibles
exactos. Eso es aceptable para el control por módulo — el saldo total
real se sigue calculando desde `valor_pagado` (que es exacto), no
desde la suma de los módulos.

---

## Bug 3 — `AbonoForm` no validaba que el número de módulo estuviera en rango

**Síntoma:** si alguien enviaba el formulario manualmente (con cURL,
desde el admin de Django, o desde shell) con `numero_modulo=99` y un
curso de 4 módulos, el `AbonoForm` lo aceptaba. El abono quedaba
"perdido" — no aparecía en la matriz por módulo, pero sí sumaba al
`valor_pagado` total.

**Por qué no se notaba en la práctica:** la UI lo previene en el
`<select>`, que solo muestra los módulos válidos del curso. Pero la
validación a nivel de formulario faltaba.

**Solución:** `AbonoForm.clean()` ahora valida que `numero_modulo` esté
entre 1 y `curso.get_numero_modulos(modalidad)` cuando el tipo de pago
es `por_modulo` o `recuperacion`. Para tipos `abono` o `pago_completo`
el campo se sigue limpiando a `None` (se ignora el valor enviado, lo
que era el comportamiento anterior).

Mensaje de error visible al usuario:
> *El módulo 99 no existe. Este curso tiene 4 módulo(s); elige uno
> entre 1 y 4.*

---

## Bug 4 — Documentación y comentarios que mentían sobre el comportamiento

El README, el CHANGELOG v2.4 y varios comentarios dentro de
`views_pagos.py` describían una lógica de "distribución de la reserva
al Módulo 1 con derrame al siguiente módulo" que **nunca se
implementó así**. El código real solo cuenta los abonos asignados
explícitamente a un módulo.

Esto confundía a quien leyera el código (incluyendo a otros
desarrolladores y al propio LLM-asistente que intentara entender el
flujo) y a quien intentara reproducir un caso reportado a partir del
README.

**Archivos actualizados:**

- `README.md` — sección "💵 Pagos por Módulo" reescrita para
  describir el comportamiento real: solo los abonos directos por
  módulo cuentan, los abonos libres aparecen como "Reservado: $X".
- `CHANGELOG_v2.4_pagos_modulo.md` — reescrito para sacar la
  descripción de la lógica de distribución que nunca se implementó.
  Se conservan los dos arreglos reales de v2.4 (kwargs de exports,
  visual binario en la matriz).
- `academia/views_pagos.py` — comentarios y docstrings de
  `_construir_matriz_pagos`, `pagos_por_modulo` y
  `_calcular_alertas_pago` actualizados.

---

## Archivos tocados

```
academia/
├── models.py                # Redondeo a 2 decimales en desglose_pagos_por_modulo
├── views_admin.py           # Fix doble conteo: _ingresos_periodo, total_ventas_hist,
│                            # por_cobrar, export_reporte_mes
├── views_pagos.py           # Redondeo en _construir_matriz_pagos y _calcular_alertas_pago
│                            # Docstrings y comentarios actualizados
└── forms.py                 # AbonoForm valida numero_modulo dentro de rango

README.md                    # Sección Pagos por Módulo reescrita + historial
CHANGELOG_v2.4_pagos_modulo.md  # Reescrito para describir lo que realmente cambió en v2.4
CHANGELOG_v2.5_calculos.md   # (este archivo)
```

Sin migraciones nuevas.

---

## Verificación

```python
# Bug 1: editar matrícula sin cambios NO debe inflar ingresos
m = Matricula.objects.get(pk=7)  # tiene $15 pagados
ing_antes = _ingresos_periodo(date(2026,5,1), date(2026,5,31))
m.save()
ing_despues = _ingresos_periodo(date(2026,5,1), date(2026,5,31))
assert ing_antes['total'] == ing_despues['total']  # ✓

# Bug 2: curso $100 / 3 módulos, paga $33.33+$33.33+$33.34
for d in mat.desglose_pagos_por_modulo():
    assert d['estado'] == 'Pagado'  # ✓ todos en Pagado

# Bug 3: AbonoForm rechaza módulo fuera de rango
form = AbonoForm({'tipo_pago':'por_modulo','numero_modulo':99,...}, matricula=mat)
assert not form.is_valid()  # ✓
```
