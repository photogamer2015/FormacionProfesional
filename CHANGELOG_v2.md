# CHANGELOG — v2 (Mayo 2026)

Cambios pedidos por Jesús, sin romper nada de lo existente. Migración 0014 aplica
sobre la BD actual sin pérdida de datos.

## 1. Cursos: número de módulos configurable

- Nuevo campo `Curso.numero_modulos` (default 4). Lo defines tú al crear/editar
  el curso. Online típico: 2 (Tributación / Asistente Contable / Talento Humano: 1).
  Presencial típico: 4 (algunos llegan a 5).
- Visible en la pantalla de crear/editar curso.

## 2. Matrícula con descuento

- Nuevo campo `Matricula.descuento` (opcional, USD).
- En el formulario de matrícula aparece junto al valor del curso. Se calcula
  EN VIVO con JS el "Valor a pagar (con descuento)".
- El saldo, las barras de progreso y los reportes ahora calculan contra el
  **valor neto** (valor_curso − descuento).
- El comprobante de venta refleja el saldo neto.
- Validación: el descuento no puede ser negativo ni mayor al valor del curso.

## 3. "Registrar Abono" → "Registrar Pago" con tipos

El modal en pagos/matrícula ahora tiene un selector "Tipo de pago":

- **Abono**: pago parcial libre (lo que había antes; default).
- **Pago Completo**: paga todo el saldo restante.
- **Por Módulo**: cubre un módulo específico → aparece selector de módulo
  (1, 2, 3... según `numero_modulos` del curso).
- **Clase de Recuperación**: pago de una clase recuperada → aparece selector
  de módulo + bloque "¿Suma al pago del curso?":
    - Sí (default): el monto se suma al `valor_pagado` y reduce el saldo.
    - No: se registra como ingreso aparte y NO afecta el saldo.

Las columnas "Tipo" y "Módulo" aparecen en el historial de pagos, y los
pagos cobrados aparte (no afectan saldo) se muestran con fondo amarillito.

## 4. Vista nueva: Pagos por Módulo

`/pagos/por-modulo/` — la vista MATRIZ que querías para el control semanal.

- Selecciona un curso → ves todos los estudiantes con una columna por módulo.
- Cada celda muestra estado (✓ Pagado / ◐ Parcial / ○ Pendiente) + monto.
- Tarjetas resumen arriba: por módulo, cuántos pagaron y cuánto se recaudó.
- Filtros: curso, modalidad, ciudad.
- Botón directo "Ver pagos" por estudiante.

Acceso: botón "📊 Por Módulo" en `/pagos/`.

## 5. Vista nueva: Clases en Recuperación

`/recuperaciones/` — gestión central de las clases por recuperar.

- Tabla con: estudiante, curso, módulo, fecha de la falta, **saldo arrastrado**
  (lo que debía cuando faltó), estado.
- Filtros: pendientes / pagadas, búsqueda por cédula o nombre, por curso.
- Botón "Cobrar" → flujo de cobro con el monto sugerido $25 (libre) y la
  decisión de si suma al saldo o se cobra aparte.

### Cómo se marca una recuperación

En la página de pagos del estudiante (`/matricula/<pk>/abonos/`) hay un
botón "✱ Marcar clase a recuperación". Llena módulo + fecha + observaciones,
y queda registrada con el saldo del momento.

Acceso: botón "✱ Recuperaciones" en `/pagos/`.

## 6. Hoja de Recaudación imprimible

`/pagos/hoja-recaudacion/` — replica el formato del PDF físico que enviaste.

- Filtros: fecha (obligatoria) + ciudad + curso.
- Si no filtras curso, genera UNA HOJA POR CADA CURSO con clases ese día.
- Encabezado con día de la semana, fecha, ciudad, responsable.
- Tabla con: nombre, módulo, recaudar, recaudado, forma de pago, banco,
  asistencia, recuperación.
- Totales abajo: a recaudar / efectivo / transferencia / total recaudado.
- Botón "🖨️ Imprimir todas" usa CSS con saltos de página (una hoja por curso).

Acceso: botón "🖨️ Hoja Recaudación" en `/pagos/`.

## 7. Validación de celular duplicado en Estudiante

Si registras un estudiante con un celular que YA pertenece a otra persona
(cédula distinta), el formulario lo rechaza con un mensaje claro:

> ⚠ Este número ya está registrado a [Nombre del otro] (cédula XXX).
> Si es la misma persona usa esa cédula; si es un número compartido (familiar),
> usa otro número de contacto.

No bloquea la edición del MISMO estudiante.

---

## Archivos modificados

- `academia/models.py` — Curso, Matricula, Abono + nuevo modelo RecuperacionPendiente
- `academia/migrations/0014_abono_cuenta_para_saldo_abono_numero_modulo_and_more.py` (NUEVA)
- `academia/forms.py` — CursoForm, MatriculaForm, EstudianteForm, AbonoForm + nuevo RecuperacionPendienteForm
- `academia/urls.py` — 5 rutas nuevas
- `academia/views_pagos.py` — 6 vistas nuevas (pagos_por_modulo, recuperaciones_lista, recuperacion_marcar, recuperacion_cobrar, recuperacion_eliminar, hoja_recaudacion)
- `templates/cursos/form.html` — campo numero_modulos
- `templates/matricula/form.html` — campo descuento + cálculo en vivo de valor neto
- `templates/pagos/lista.html` — botones de acceso a las nuevas vistas
- `templates/pagos/matricula_abonos.html` — modal "Registrar Pago" rediseñado, tabla con columnas Tipo/Módulo, banner de recuperaciones pendientes
- `templates/pagos/por_modulo.html` (NUEVO)
- `templates/pagos/recuperaciones.html` (NUEVO)
- `templates/pagos/recuperacion_marcar.html` (NUEVO)
- `templates/pagos/recuperacion_cobrar.html` (NUEVO)
- `templates/pagos/hoja_recaudacion.html` (NUEVO)

## Compatibilidad con datos existentes

- Todos los abonos viejos quedan con `tipo_pago='abono'` y `cuenta_para_saldo=True`
  (default), por lo que se siguen comportando exactamente igual que antes.
- Los cursos viejos quedan con `numero_modulos=4` por defecto. Edita cada curso
  online de Tributación / Contable / Talento Humano y bájalo a 1, los otros online
  a 2, los presenciales a 4 o 5 según corresponda.
- Las matrículas viejas quedan con `descuento=0` (sin descuento). El saldo se
  sigue calculando igual.
