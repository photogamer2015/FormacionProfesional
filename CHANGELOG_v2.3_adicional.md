# CHANGELOG — Módulo Adicional (v2.3)

Nueva sección **Adicional** para registrar servicios y productos extra:
certificados, examen supletorio y camisas adicionales, tanto para
estudiantes internos como para personas externas a la academia.

---

## 🆕 Funcionalidades nuevas

### 1. Sección "Adicional" en el menú principal
Nueva tarjeta `➕ Adicional` en `bienvenida.html`, visible para usuarios
con permiso de gestionar matrículas. Lleva al menú del módulo con cuatro
opciones:
- **＋ Agregar Adicional** (estudiante interno)
- **＋ Agregar Persona Externa** (no matriculado)
- **≡ Lista de Adicionales** (todos los registros)
- **📇 Lista de Personas Externas** (directorio)

### 2. Tipos de Adicional soportados
| Tipo | Pide curso | Pide modalidad | Pide talla | Pide módulo |
|------|:---:|:---:|:---:|:---:|
| Certificado de matrícula | ✓ | ✓ | — | — |
| Certificado de asistencia | ✓ | ✓ | — | — |
| Certificado antiguo | ✓ | ✓ | — | — |
| Examen supletorio | ✓ | ✓ | — | ✓ |
| Camisa | — | — | ✓ | — |

**Tallas disponibles:** S, M, L, XL y "Ninguna de las anteriores
(la academia solo cubre hasta XL)".

**El valor lo defines libremente en cada registro** — no hay precios fijos.

### 3. Examen Supletorio rápido desde la matrícula
En el detalle de pagos de cada matrícula (`/matricula/<pk>/abonos/`)
se añadió un botón:

> 📝 **Examen supletorio**

Al hacer clic abre un mini-formulario que **pide el valor al marcar Sí**.
Pre-llena automáticamente: estudiante, curso, modalidad y matrícula de
origen. Solo te pregunta:
- Módulo
- Fecha
- **Valor** (lo defines tú)
- Método de pago
- Observaciones

El registro queda en la sección Adicional y también aparece en una
tarjeta azul dentro del detalle de la matrícula original.

### 4. Personas Externas
Nuevo modelo `PersonaExterna` con CRUD propio. Se pide solo cédula,
apellidos y nombres como obligatorios; correo, celular, ciudad y
observaciones son opcionales. Una persona externa no puede eliminarse
si tiene Adicionales registrados (hay que eliminar los Adicionales primero).

### 5. Dashboard administrativo
- ➕ **Nuevo KPI "Adicionales del mes"** (con borde y signo `+$`,
  fondo en gradiente turquesa) que muestra total, conteo, internos vs
  externos, y variación contra el mes anterior.
- ✅ Los Adicionales **se suman al ingreso total del mes**. La tarjeta
  de Ingresos ahora desglosa: Abonos + Ventas + Adicionales.
- 📊 Nuevo bloque **"Desglose por tipo"** con barra de progreso por
  cada tipo de adicional del mes.
- 📈 Histórico actualizado: total acumulado de Adicionales suma al
  total general histórico.

### 6. Autocompletado por cédula
- En el formulario interno: escribe la cédula del estudiante y se
  autocompletan apellidos, nombres, celular, etc.
- En el formulario externo: escribe la cédula de la persona externa.
  Si no existe, te ofrece un botón para registrarla.

### 7. Lista de Adicionales con filtros
Filtros disponibles:
- Por tipo (cert_matricula, cert_asistencia, cert_antiguo, examen_supletorio, camisa)
- Por origen (interno / externo)
- Por rango de fechas (desde / hasta)
- Búsqueda libre (cédula, nombre, curso)

---

## 📁 Archivos creados

```
academia/migrations/0017_personaexterna_adicional.py
academia/views_adicional.py
templates/adicional/menu.html
templates/adicional/lista.html
templates/adicional/form_interno.html
templates/adicional/form_externo.html
templates/adicional/personas_externas.html
templates/adicional/persona_externa_form.html
templates/adicional/confirmar_eliminar.html
templates/adicional/persona_externa_confirmar_eliminar.html
templates/adicional/supletorio_marcar.html
```

## 📝 Archivos modificados

```
academia/models.py        — agregados PersonaExterna y Adicional al final
academia/forms.py         — agregados PersonaExternaForm, AdicionalInternoForm,
                            AdicionalExternoForm, AdicionalSupletorioRapidoForm
academia/urls.py          — 13 rutas nuevas (sección /adicional/...)
academia/admin.py         — registrados PersonaExterna y Adicional
academia/views_admin.py   — _ingresos_periodo() y serie_meses ahora suman
                            adicionales; nueva _adicionales_periodo();
                            contexto del dashboard con adicionales_mes y
                            var_adicionales
templates/bienvenida.html              — tarjeta nueva ➕ Adicional
templates/admin_panel/dashboard.html   — KPI nuevo + desglose por tipo
                                         + histórico actualizado
templates/pagos/matricula_abonos.html  — botón 📝 Examen supletorio +
                                         sección de supletorios registrados
```

---

## 🚀 Cómo levantar el proyecto

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Aplicar migraciones (incluye la 0017 nueva)
python manage.py migrate

# 3. Servidor
python manage.py runserver
```

La migración `0017_personaexterna_adicional` crea las dos tablas nuevas
sin tocar las existentes.

---

## ✅ Validación end-to-end

Todos los flujos fueron probados:
- ✓ Crear PersonaExterna por POST
- ✓ Crear Adicional EXTERNO (camisa, talla L)
- ✓ Crear Adicional INTERNO (certificado de matrícula)
- ✓ Marcar Examen Supletorio desde matrícula (con `matricula_origen` correcto)
- ✓ Dashboard renderiza con KPI "+$ Adicionales del mes" + desglose
- ✓ Bienvenida muestra la tarjeta `➕ Adicional`
- ✓ Pantalla de pagos muestra el botón `📝 Examen supletorio`
- ✓ `python manage.py check` → 0 errores
