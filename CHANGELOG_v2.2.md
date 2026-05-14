# Cambios v2.2 — Mayo 2026

## Resumen

Mejoras en los apartados de **Pagos**, **Por Módulo**, **Recuperaciones** y
**Registro Administrativo** solicitadas por Jesús.

## ✅ Pagos (Estado de Pagos — `/pagos/`)

- Nuevas columnas en la tabla: **Jornada**, **Día** (fecha de inicio de la
  jornada) y **Asistencia** (línea en blanco para firma).
- Nuevo botón **📄 PDF** que descarga toda la lista filtrada en formato A3
  horizontal con la columna de Asistencia subrayada para firmar.
- Nuevo botón **🖨️ Imprimir** que aprovecha estilos `@media print` para
  ocultar menús y mantener la línea de firma visible.
- La exportación a Excel ahora incluye `Jornada`, `Día (inicio jornada)`,
  `Horario` y `Asistencia` (columna en blanco).

## ✅ Por Módulo (`/pagos/por-modulo/`)

- La columna combinada *Jornada / día* se separó en **Jornada** y **Día**
  para mejor lectura.
- Se agregó la columna **Asistencia** a la matriz estudiantes × módulos y a
  la hoja de recaudación interna del curso. Línea en blanco lista para firmar.
- Excel y PDF actualizados: Día separado y nueva columna Asistencia.
- En el PDF la línea de firma se imprime con un trazo gris en la última
  columna de cada fila de datos.

## ✅ Clases en Recuperación (`/recuperaciones/`)

- Nueva columna **Asistencia** con línea de firma.
- Excel y PDF incluyen la nueva columna (vacía, lista para firmar a mano).

## ✅ Registro Administrativo (`/admin-panel/`)

### Nueva tarjeta KPI: ✱ Clases de Recuperación
Muestra el monto total cobrado en clases de recuperación durante el mes,
desglosado en lo que suma al saldo y lo que se cobró aparte. Incluye
variación porcentual contra el mes anterior.

### Gráfico de barras (últimos 6 meses)
Ahora con **4 barras** por mes:
- Verde — Ingresos
- Rojo — Egresos
- Gris — Retiros
- Naranja — **Clases de Recuperación** ← nuevo

### Nueva sección: 🎯 Tipos de Pago — mes seleccionado
Gráfico circular (pie chart) + desglose con barras de progreso para los
4 tipos de pago: **Abono**, **Pago Completo**, **Por Módulo** y
**Clase de Recuperación**. Cada uno con su color y el porcentaje de
participación en el total registrado del mes.

### Nueva sección: 📊 Distribución por mes (últimos 6 meses)
6 mini gráficos circulares, uno por mes, mostrando cómo cambia la mezcla
de tipos de pago a lo largo del tiempo. Cada pie incluye el total del mes.

## Archivos modificados

- `templates/pagos/lista.html`
- `templates/pagos/por_modulo.html`
- `templates/pagos/recuperaciones.html`
- `templates/admin_panel/dashboard.html`
- `academia/views_pagos.py` (nueva función `pagos_export_pdf`,
  exports actualizados)
- `academia/views_admin.py` (nuevos helpers `_tipos_pago_periodo`,
  `_recuperaciones_periodo`)
- `academia/urls.py` (nueva ruta `pagos_export_pdf`)
