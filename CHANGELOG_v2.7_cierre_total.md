# Changelog v2.7 — Cierre Total + Estudiantes Archivados

## Lo nuevo en v2.7 (sobre v2.6)

### Cierre TOTAL global

Antes solo se podía cerrar curso por curso o jornada por jornada. Ahora hay un
**botón de "Cierre TOTAL"** en la lista de cursos que archiva en una sola
operación **todas las matrículas y pagos de una modalidad** (presencial o
online) o de **todas las modalidades a la vez**.

- Ubicación: `Cursos → Presencial` o `Cursos → Online`, arriba a la derecha:
  botón rojo grande **🔒 Cierre TOTAL (presencial)** o **🔒 Cierre TOTAL (online)**.
- Flujo idéntico al cierre individual: vista previa con detalle por curso,
  confirmación con modal "¿Estás 100 % seguro?", ejecución atómica.
- Internamente crea **un `CierreCurso` por cada curso afectado** (no un único
  cierre gigante) para que el historial se pueda filtrar/consultar curso por
  curso de forma granular.
- Etiquetado como `alcance='global'` y `modalidad_global='presencial'/'online'/'todas'`.
- En la lista del historial se muestra con el badge rojo **"🌐 CIERRE GLOBAL"**.

### Limpieza del directorio de estudiantes

El cierre (tanto individual como global) acepta un checkbox opcional
**🧹 "Limpiar también el directorio de estudiantes"**.

Cuando se activa, después de archivar las matrículas:

1. Identifica los estudiantes que quedaron *huérfanos* — sin matrículas vivas
   en NINGÚN otro curso **Y** sin Adicionales (exámenes supletorios cobrados,
   certificados, camisetas) protegidos.
2. Los copia a `EstudianteArchivado` (snapshot con cédula, nombre, edad,
   correo, celular, ciudad, nivel formación, título).
3. Los borra del directorio vivo.

Los estudiantes que aún tienen matrículas en otros cursos o adicionales
asociados **no se tocan** (esto evita romper el histórico financiero).

En el cierre global, este checkbox viene **pre-marcado** porque es lo que
quieres al cerrar un mes completo.

### Apartado "Estudiantes archivados"

Nuevo listado independiente, separado del directorio vivo:

- URL: `/estudiantes/archivados/`
- Filtros: búsqueda libre (cédula, nombre, correo, celular), por cierre
  asociado y por año de archivo.
- Export Excel completo con todos los campos.
- Acceso desde:
  - **Inicio → tarjeta "Estudiantes archivados"** (tarjeta nueva).
  - **Estudiantes → botón "🗄️ Archivados"** arriba a la derecha.
  - **Detalle de un cierre** → enlace directo si ese cierre limpió el directorio.

### Mejoras al detalle del cierre

- Banner amarillo cuando el cierre limpió el directorio, con conteo de
  estudiantes archivados y enlace directo a los estudiantes de ese cierre.
- Lista de cierres muestra badge verde **"🧹 Directorio limpiado"** en los
  cierres que incluyeron limpieza.

---

## Modelos nuevos (v2.7)

### `EstudianteArchivado`

Snapshot de un estudiante archivado durante un cierre.

Campos: `cedula`, `apellidos`, `nombres`, `edad`, `correo`, `celular`,
`nivel_formacion`, `titulo_profesional`, `ciudad`, `creado_original`,
`archivado_en`, FK a `CierreCurso`.

### Campos añadidos a `CierreCurso`

- `modalidad_global` — para distinguir cierres globales de presencial/online/todas.
- `limpio_directorio` — bool, True si en este cierre se archivaron estudiantes.
- `total_estudiantes_archivados` — conteo.

---

## URLs nuevas (v2.7)

```
/cursos/cierre-global/<modalidad>/                    → preview cierre global
/cursos/cierre-global/<modalidad>/ejecutar/  [POST]   → ejecutar cierre global
/estudiantes/archivados/                              → lista archivados
/estudiantes/archivados/exportar/                     → Excel archivados
```

donde `<modalidad>` es `presencial`, `online` o `todas`.

---

## Migraciones aplicadas

- `0021_cierrecurso_matriculaarchivada_abonoarchivado_and_more.py` (v2.6)
- `0022_cierrecurso_limpio_directorio_and_more.py` (v2.7)

---

## Garantías técnicas

- **Atomicidad**: cada cierre global usa un único `transaction.atomic()`.
  Si falla la limpieza del directorio, no se borra ninguna matrícula.
- **Protección de FKs**: los estudiantes con `Adicional` asociado (exámenes
  supletorios cobrados, certificados, etc.) NUNCA se archivan, porque eso
  rompería el histórico financiero. Quedan en el directorio vivo.
- **Inmutabilidad**: igual que las matrículas archivadas, los estudiantes
  archivados son snapshots denormalizados que sobreviven a cambios o borrados
  posteriores.

---

## Cómo se usa (flujo completo)

### Caso: "Termina mayo, quiero empezar junio limpio"

1. Entras a *Cursos → Presencial*.
2. Pulsas **🔒 Cierre TOTAL (presencial)** arriba a la derecha.
3. Ves la vista previa: cuántos cursos afectados, cuántas matrículas, totales
   por curso, etc.
4. Pones etiqueta del ciclo (ej. "Cierre mensual Mayo 2026"), dejas marcado
   el checkbox **🧹 Limpiar directorio** y confirmas.
5. Se ejecuta:
   - Por cada curso con matrículas presenciales → 1 `CierreCurso` con todo
     archivado.
   - Las matrículas y pagos se eliminan de la operación viva.
   - Los estudiantes huérfanos pasan a `EstudianteArchivado`.
6. Te redirige al historial de cierres con un mensaje de éxito.
7. Lista de cursos: todas las jornadas siguen ahí (estructura) pero con
   0 matrículas — listas para el nuevo ciclo.
8. Directorio de estudiantes: vacío o casi vacío. Los archivados están en
   *Estudiantes → 🗄️ Archivados*.

### Caso: "Solo termina una jornada específica"

Igual que antes: *Cursos → [curso] → Jornadas → fila de la jornada → 🔒 Cerrar*.
Puedes marcar o no el checkbox de limpiar directorio según prefieras.
