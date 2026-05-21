# CHANGELOG v2.8 — Sedes administrables, jornadas "Otros", módulos y archivo en carpetas

Fecha: 2026-05-21

Esta versión agrupa cinco mejoras solicitadas. Todas fueron probadas con el
test client de Django (renderizado de páginas, flujos de creación, validaciones,
exports y permisos).

---

## 1. Jornadas: opción "Otros" con días personalizados

- Se agregó la opción **"Otros (especificar)"** al selector de días de la jornada.
- Al elegir "Otros" aparece un campo de texto libre (`descripcion_otros`) para
  escribir los días personalizados (ej. "Viernes y Sábado").
- Funciona tanto en el formulario "Nueva jornada" como en el modal de edición.
- Validación: si se elige "Otros" pero no se escribe nada, el formulario no se guarda.
- `descripcion_legible` ahora devuelve el texto personalizado cuando la
  descripción es "otros".

**Archivos:** `models.py` (constante `JORNADA_DIAS`, campo `descripcion_otros`),
`forms.py` (`JornadaCursoForm`), `templates/cursos/jornadas.html`, `views.py`
(endpoint AJAX de edición).

---

## 2. Directorio de estudiantes: columnas Jornada y Sede

- El **listado de estudiantes** muestra ahora dos columnas nuevas: **Jornada** y **Sede**.
- La vista **"Agrupados por curso"** también muestra Jornada y Sede por cada matrícula.
- Los **exports de Excel** (plano y por curso) incluyen estas columnas para
  imprimir o descargar.

**Archivos:** `views_pagos.py` (`estudiantes_lista`, `estudiantes_por_curso`,
`estudiantes_export`), `templates/estudiantes/lista.html`,
`templates/estudiantes/por_curso.html`.

---

## 3. Pagos por módulo: "Pagado" cuando el saldo total es $0

- Antes: si un estudiante pagaba todo el curso en un solo módulo (o como abono
  libre), los demás módulos seguían apareciendo como "Pendiente".
- Ahora: cuando el **saldo total llega a $0**, **todos los módulos** se muestran
  en verde "Pagado", sin importar cómo se distribuyó el dinero.
- El comportamiento parcial se mantiene intacto: si hay saldo pendiente, los
  módulos no cubiertos siguen mostrando "Parcial"/"Pendiente".

**Archivos:** `models.py` (`Matricula.desglose_pagos_por_modulo()` y
`Matricula.estado_modulo()`).

---

## 4. Sedes / Campus administrables (solo admin)

- Nuevo modelo **`Sede`**: nombre, país, dirección, teléfono, orden, activa.
- Las sedes se **agrupan por país** (escala a Venezuela, Colombia, etc.).
- Panel CRUD en **Dashboard Admin → 🏢 Sedes**: crear, editar, activar/desactivar
  y eliminar sedes **sin tocar el código**.
- Las jornadas presenciales ahora eligen su sede desde este catálogo en lugar de
  las ciudades fijas "Guayaquil/Quito" que estaban escritas en el código.
- Para no perder integridad histórica, el campo de texto `ciudad` de cada jornada
  se mantiene **sincronizado automáticamente** con la sede elegida. Así, todo lo
  que ya filtraba/mostraba/archivaba por `ciudad` (exports, control por módulo,
  cierres) sigue funcionando sin cambios.
- Seguridad: una sede con jornadas asociadas no se borra, solo se desactiva.

**Migración de datos (0025):** crea automáticamente Guayaquil y Quito a partir
de las ciudades existentes y vincula todas las jornadas presenciales a su sede.

**Archivos:** `models.py` (modelo `Sede`, FK `sede` y `save()` en `JornadaCurso`),
`forms.py` (`SedeForm`, `JornadaCursoForm`), `views_sedes.py` (nuevo),
`urls.py`, `admin.py`, `templates/sedes/lista.html`, `templates/sedes/form.html`,
`templates/admin_panel/dashboard.html`.

---

## 5. Archivo organizado en carpetas

- Nuevo índice de **Archivo** (`/historial/archivo/`) que organiza todo lo
  archivado en **carpetas**, para que no se mezcle todo en una sola lista:
  - 📁 **Estudiantes** (académico): Cursos cerrados + Estudiantes archivados.
  - 📁 **Administrativo** (financiero): Cortes de caja. Solo visible para admin.
- La tarjeta "Cursos cerrados" de la pantalla de inicio ahora se llama
  **"Archivo"** y abre este índice de carpetas.
- Los breadcrumbs de las páginas internas y el botón "Archivados" del directorio
  apuntan al índice de carpetas.

**Archivos:** `views_cierre.py` (`archivo_index`), `urls.py`,
`templates/historial/archivo_index.html` (nuevo), `templates/bienvenida.html`,
`templates/estudiantes/lista.html`, `templates/estudiantes/archivados_lista.html`,
`templates/historial/cierres_lista.html`,
`templates/admin_panel/cierre_admin_historial.html`.

---

## Migraciones incluidas

- `0024_jornadacurso_descripcion_otros_and_more.py` — esquema (modelo Sede + campos nuevos).
- `0025_poblar_sedes_desde_ciudades.py` — datos (crea sedes y vincula jornadas).

Para aplicar en tu servidor: `python manage.py migrate academia`

---

## 6. Recuperar estudiante archivado al hacer nueva matrícula

- Antes: si un estudiante había sido archivado (al cerrar un curso con "limpiar
  directorio"), al escribir su cédula en una matrícula nueva el sistema lo
  trataba como "Estudiante nuevo" y había que teclear todo de nuevo.
- Ahora: cuando la cédula no está en el directorio vivo, el sistema la busca en
  el **archivo histórico** y, si la encuentra, **autocompleta** los datos
  personales igual, mostrando el mensaje "📁 Estudiante recuperado del archivo —
  datos cargados".
- Al guardar la matrícula, el estudiante se recrea automáticamente en el
  directorio vivo (comportamiento que ya existía), sin conflictos.
- El nivel de formación se convierte correctamente del texto archivado al código
  del formulario.

**Archivos:** `views.py` (`api_estudiante_por_cedula`), `templates/matricula/form.html`.
