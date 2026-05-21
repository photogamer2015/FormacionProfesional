# Changelog v2.6 — Cierre de Curso e Historial Archivado

## Resumen

Nueva funcionalidad: **Cierre de Curso**. Permite al administrador archivar
permanentemente un ciclo completo (curso o jornada específica) en el historial,
limpiar la operación viva (matrículas + pagos + recuperaciones + alertas) y
empezar un nuevo ciclo desde cero. Todo lo archivado se consulta, filtra y
exporta desde un apartado independiente "Cursos cerrados".

---

## Lo que se añadió

### 1. Modelos nuevos (`academia/models.py`)

- **`CierreCurso`** — Cabecera del cierre. Guarda totales congelados
  (facturado, cobrado, pendiente, conteos por estado pago), metadatos de
  alcance (jornada / curso entero), etiqueta de ciclo libre (ej. "Mayo 2026"),
  observaciones, y auditoría (fecha + usuario).
- **`MatriculaArchivada`** — Snapshot completo y denormalizado de cada
  matrícula del cierre. Guarda **TODO**: cédula, apellidos, nombres, edad,
  correo, celular, ciudad, nivel, curso (nombre + categoría), jornada legible,
  fecha de inicio, sede, modalidad, horario, tipo de matrícula, estado, valor,
  descuento, valor neto, pagado, saldo, estado pago, comprobante, factura,
  observaciones. Aunque luego se borre el curso o el estudiante, el archivo
  sigue siendo 100 % legible.
- **`AbonoArchivado`** — Snapshot completo de cada pago: fecha, monto, tipo
  pago, método, banco, módulo, recibo, observaciones.

### 2. Migración (`academia/migrations/0021_*.py`)

Generada y aplicada. Incluye índices en `(cierre, estado_pago)`,
`(cierre, modalidad)` y `cedula` para que los filtros del historial sean
rápidos.

### 3. Vistas (`academia/views_cierre.py`)

Archivo nuevo con 6 vistas:

- **`cierre_preview(curso_pk)`** — Vista previa del cierre. Selector de
  jornada o curso entero. Muestra resumen (cuántas matrículas, cuántos pagos,
  totales, chips de estado) y lista detallada de lo que se va a archivar.
- **`cierre_ejecutar(curso_pk)`** [POST, atómico] — Ejecuta el cierre.
  Crea `CierreCurso`, snapshotea cada `Matricula` + cada `Abono`, y borra las
  matrículas vivas (las alertas, recuperaciones y abonos caen en cascada).
  Todo dentro de `transaction.atomic()`: si algo falla, no se modifica nada.
- **`cierre_historial()`** — Lista todos los cierres agrupados por curso →
  cierres. Filtros: curso, modalidad, año del cierre, búsqueda libre.
- **`cierre_detalle(cierre_pk)`** — Detalle de un cierre con tabla idéntica
  a la lista de matrículas viva, y todos los filtros:
  - Estado de pago (Pagado / Parcial / Pendiente / Retiro) — clickeable en
    tarjetas-chip arriba o por dropdown.
  - Modalidad (Presencial / Online).
  - Sede (selector con las sedes distintas de ese cierre).
  - Búsqueda libre (cédula, apellido, nombre, correo, celular, jornada).
- **`cierre_export(cierre_pk)`** — Descarga Excel profesional con dos hojas:
  *Matrículas* (28 columnas con todos los datos) y *Abonos* (15 columnas).
  Respeta los filtros activos.
- **`cierre_eliminar(cierre_pk)`** [POST, solo admin] — Elimina un cierre
  del historial (cascada).

### 4. URLs (`academia/urls.py`)

```
/cursos/<curso_pk>/cierre/                          → preview
/cursos/<curso_pk>/cierre/ejecutar/   [POST]        → ejecutar
/historial/cierres/                                 → lista
/historial/cierres/<cierre_pk>/                     → detalle
/historial/cierres/<cierre_pk>/exportar/            → Excel
/historial/cierres/<cierre_pk>/eliminar/  [POST]    → eliminar
```

### 5. Templates

- **`templates/cursos/cierre_preview.html`** — Vista previa con modal de
  confirmación final ("¿Estás 100 % seguro?").
- **`templates/historial/cierres_lista.html`** — Lista de cierres agrupados
  por curso con totales agregados y filtros.
- **`templates/historial/cierre_detalle.html`** — Detalle: tabla idéntica a
  pagos/lista.html (mismas columnas, mismos chips, mismos colores), banner
  superior con datos del cierre, tarjetas-chip de estado clickeables.

### 6. Botones añadidos en templates existentes

- **`templates/cursos/jornadas.html`** — Botón superior derecho
  "🔒 Cierre de curso" (cierra todo el curso) + "🗄️ Historial de cierres".
  Mini-botón "🔒 Cerrar" en cada fila de jornada con matrículas
  (cierra solo esa jornada).
- **`templates/cursos/lista.html`** — Botón "🔒 Cierre" en cada tarjeta de
  curso.
- **`templates/bienvenida.html`** — Nueva tarjeta "Cursos cerrados".
- **`templates/historial/lista.html`** — Cross-link "🗄️ Cursos cerrados" en
  la cabecera.

### 7. Admin de Django (`academia/admin.py`)

`CierreCurso`, `MatriculaArchivada` y `AbonoArchivado` registrados con sus
inlines y filtros, todos campos en `readonly_fields` porque son snapshots
inmutables.

---

## Cómo se usa (flujo del usuario)

1. **Cerrar una jornada específica.** Entra a *Cursos → [curso] → Jornadas*,
   localiza la jornada que terminó su ciclo, pulsa el botón rojo "🔒 Cerrar"
   en su fila. → Vista previa con resumen → Confirmación → Cierre ejecutado.
2. **Cerrar todo un curso.** En la misma pantalla, pulsa "🔒 Cierre de curso"
   arriba a la derecha (cierra TODAS las jornadas).
3. **Empezar un nuevo ciclo.** Después del cierre, la lista de matrículas y
   de pagos del curso queda en cero. Registras las matrículas del nuevo ciclo
   normalmente.
4. **Consultar el historial.** *Inicio → Cursos cerrados* o
   *Historial → Cursos cerrados*. Cada cierre se expande y muestra el detalle
   completo con todos los filtros.
5. **Exportar.** Botón "📥 Descargar Excel" en el detalle. Si tienes filtros
   activos, exporta solo lo filtrado.

---

## Permisos

- Solo **Administradores** pueden ejecutar cierres y eliminarlos.
- **Asesores** sí pueden consultar, filtrar y exportar el historial archivado.

---

## Garantías técnicas

- **Atomicidad**: todo el cierre va dentro de `transaction.atomic()`. Si falla
  un snapshot, no se borra nada.
- **Inmutabilidad**: las matrículas archivadas son denormalizadas (cédula,
  nombre, sede, jornada, etc. son strings copiados). Si más adelante se borra
  un estudiante o un curso, el historial sigue siendo legible al 100 %.
- **Cero pérdida de datos**: cada `Abono` se copia uno a uno a
  `AbonoArchivado`. Incluso si la matrícula original tenía recuperaciones o
  alertas, los pagos asociados quedan archivados.
- **Filtros congelados**: el detalle de un cierre expone los mismos filtros
  que ofrece la lista de matrículas viva (estado pago, modalidad, sede,
  búsqueda libre), garantizando paridad de UX.

---

## Archivos modificados

```
academia/models.py                                            (+250 líneas)
academia/admin.py                                             (+80 líneas)
academia/urls.py                                              (+15 líneas)
academia/views_cierre.py                                      NUEVO (+520 líneas)
academia/migrations/0021_cierrecurso_matriculaarchivada_*.py  NUEVO
templates/cursos/cierre_preview.html                          NUEVO
templates/cursos/jornadas.html                                (+30 líneas)
templates/cursos/lista.html                                   (+10 líneas)
templates/historial/cierres_lista.html                        NUEVO
templates/historial/cierre_detalle.html                       NUEVO
templates/historial/lista.html                                (+5 líneas)
templates/bienvenida.html                                     (+15 líneas)
```
