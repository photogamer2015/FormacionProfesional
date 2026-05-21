# Changelog v2.1 — Pagos por Módulo + Alertas + Exportaciones

Fecha: 2026-05-09

## 1) Lógica de la reserva en Pagos por Módulo (PRIORIDAD)

**Problema anterior:** si un estudiante tipo "Reserva + Módulo 1" pagaba $20 de
reserva (sin módulo) y $60 al módulo 1 (curso de $80, 2 módulos de $40 c/u),
el módulo 1 aparecía como ◐ Parcial $60/$80 cuando en realidad ya había
pagado todo el curso.

**Solución:** nuevo método `Matricula.pagos_por_modulo_efectivo()` que
distribuye los pagos así:

1. Los pagos asignados a un módulo específico van directamente a ese módulo.
2. Los pagos sin módulo (reserva, abonos, pago_completo) entran a un "pool libre".
3. En una pasada secuencial módulo 1 → 2 → ... → N:
   - Si el módulo está sobrepagado, el excedente se "derrama" al siguiente.
   - Si el módulo está incompleto, se llena con el carry y luego con el pool libre.
4. Cualquier remanente final cae al último módulo (sobrepago real).

**Resultado para el ejemplo:** $20 reserva + $60 al Mód.1 → Mód.1: ✓ Pagado $40,
Mód.2: ✓ Pagado $40 (vino del derrame del 1 + reserva).

## 2) Filtros nuevos en Pagos por Módulo

- **Tipo de matrícula:** Reserva/Abono · Reserva + Módulo 1 · Programa Completo
- **Estado del Módulo 1:** Pagado · Parcial · Pendiente
- **(Existentes:) Curso, Modalidad, Ciudad**

Filtrar "Reserva/Abono" + "Pendiente" muestra los morosos del primer módulo
de un solo vistazo.

## 3) Columna "Inicio jornada"

Nueva columna en:
- Pagos por Módulo (pantalla, Excel y PDF)
- Hoja de Recaudación (pantalla, Excel y PDF)
- Lista de Matrícula (pantalla)

Toma el valor de `m.jornada.fecha_inicio`.

## 4) Exportar Excel · PDF · Imprimir

Nuevos botones en Pagos por Módulo y Hoja de Recaudación:

- 📊 Excel — usa openpyxl, formato consistente con otras exportaciones.
- 📄 PDF — usa reportlab, paisaje A4, una página por curso.
- 🖨️ Imprimir — usa `window.print()` con CSS `@media print` que oculta menús.

Nuevas URLs:
- `/pagos/por-modulo/exportar/excel/`
- `/pagos/por-modulo/exportar/pdf/`
- `/pagos/hoja-recaudacion/exportar/excel/`
- `/pagos/hoja-recaudacion/exportar/pdf/`

## 5) Alertas de pago pendiente del Módulo 1

Aparecen en el dashboard de **Bienvenida** para administradores y asesores.

**Reglas para que se dispare la alerta:**
- Tipo de matrícula = `reserva_abono` o `reserva_modulo_1`
- Jornada con `fecha_inicio < hoy` (la jornada ya empezó al menos 1 día antes)
- Módulo 1 sigue Pendiente o Parcial (no Pagado)
- Matrícula no está en Retiro voluntario

**Acciones por alerta:**
- 💬 **WhatsApp** — abre `wa.me/{celular_internacional}` con un mensaje
  predefinido que menciona el curso, fecha de inicio y monto adeudado.
  El celular se normaliza: `09xxxxxxxx` → `593xxxxxxxxx`.
- 👁 **Detalle** — va a la página de abonos del estudiante.
- ✓ **Ya revisado** — crea registro `AlertaPagoRevisada(matricula, módulo, fecha=hoy)`.
  Oculta la alerta hasta mañana. Si al día siguiente sigue impago, vuelve a aparecer.

**Nuevo modelo:** `AlertaPagoRevisada` (migración `0015_alertapagorevisada.py`).

**Nueva URL:** `POST /alertas/<matricula_pk>/revisar/`

Las primeras 3 alertas se muestran expandidas; el resto bajo un `<details>`
plegable para no abrumar el dashboard.

## 6) Archivos modificados

- `academia/models.py` — `pagos_por_modulo_efectivo()`, modelo `AlertaPagoRevisada`
- `academia/migrations/0015_alertapagorevisada.py` — nueva migración
- `academia/views.py` — `bienvenida()` ahora calcula alertas
- `academia/views_pagos.py` — vista refactorizada + 5 vistas nuevas
- `academia/urls.py` — 5 URLs nuevas
- `templates/bienvenida.html` — banner de alertas con botones
- `templates/pagos/por_modulo.html` — filtros + botones export + columna inicio
- `templates/pagos/hoja_recaudacion.html` — botones Excel/PDF + columna inicio
- `templates/matricula/lista.html` — columna "Inicio jornada"

## 7) Cómo aplicar los cambios

```bash
python manage.py migrate
```

No se requiere reiniciar nada más. Las dependencias (openpyxl, reportlab) ya
estaban en `requirements.txt`.

## 8) Compatibilidad

- El método `Matricula.pagos_por_modulo()` original se conserva intacto
  (lo usa `hoja_recaudacion` para determinar el "módulo actual" del día).
- `Matricula.estado_modulo()` ahora usa internamente la lógica nueva
  (con parámetro opcional `pagos_efectivos` para evitar recalcular en bucles).
- No hay cambios incompatibles en la base de datos: solo se AGREGA una
  tabla nueva (`alertapagorevisada`).
