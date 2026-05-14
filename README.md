# Formación Técnica y Profesional EC — Sistema Académico

Sistema interno para gestión de matrículas, pagos, abonos por módulo,
recibos y reportes de **Formación Técnica y Profesional EC**
(presencial y virtual, sedes Guayaquil y Quito).

Stack: **Django 5** · **SQLite** (por defecto) o **MySQL 8** (producción)
· Python 3.11+ · openpyxl + reportlab para exportaciones.

---

## 🚀 Quickstart (clonar desde GitHub)

### macOS / Linux

```bash
git clone https://github.com/<TU_USUARIO>/formacion-tecnica-profesional.git
cd formacion-tecnica-profesional

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copia el .env de ejemplo y edítalo
cp .env.example .env

# Crea las tablas
python manage.py migrate

# Carga roles iniciales (admin / asesor / etc.)
python manage.py setup_roles

# Crea tu superusuario
python manage.py createsuperuser

# Arranca
python manage.py runserver
```

Abre `http://127.0.0.1:8000` y entra con el usuario que acabas de
crear.

### Windows (PowerShell)

```powershell
git clone https://github.com/<TU_USUARIO>/formacion-tecnica-profesional.git
cd formacion-tecnica-profesional

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env

python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
python manage.py runserver
```

> 📄 La **Guía de Instalación detallada para Windows** está en
> [`Guia_Instalacion_Windows.pdf`](./Guia_Instalacion_Windows.pdf).

---

## 🗂 Estructura del proyecto

```
.
├── academia/                # App principal
│   ├── models.py            # Estudiante, Matricula, Abono, Curso, Jornada…
│   ├── views.py             # Vistas básicas (matrícula, cursos)
│   ├── views_pagos.py       # Pagos, abonos, recibos, hoja de recaudación
│   ├── views_admin.py       # Panel admin
│   ├── views_adicional.py   # Reportes adicionales
│   ├── views_comprobantes.py
│   ├── forms.py
│   ├── urls.py
│   ├── permisos.py          # Decoradores de roles
│   ├── context_processors.py
│   └── management/commands/ # setup_roles, etc.
├── core/                    # Configuración Django
│   ├── settings.py          # Lee .env via django-environ
│   └── urls.py
├── templates/               # Plantillas HTML
├── static/                  # CSS, imágenes, logo
├── requirements.txt
├── manage.py
└── .env.example             # Plantilla de variables de entorno
```

---

## 💵 Pagos por Módulo — cómo funciona la lógica

La pantalla `/pagos/por-modulo/` muestra una matriz **estudiante ×
módulo** con el avance de cobros. La regla es:

1. **Solo entran a la matriz los abonos asignados explícitamente a un
   módulo:** los de tipo `por_modulo` y los de tipo `recuperacion` que
   indiquen el `numero_modulo`. Cada módulo se cobra de forma
   independiente.
2. **La reserva y los abonos libres NO entran a la matriz.** Los abonos
   de tipo `abono` o `pago_completo` (sin número de módulo) sí suman al
   valor pagado total y al saldo del curso, pero no se asignan a un
   módulo específico. Quedan visibles como "Reservado: $X" debajo del
   valor pagado de la fila.
3. **Caso especial Programa Completo:** si la matrícula es de tipo
   `programa_completo` y el saldo está en $0, los módulos se muestran
   como "Programa Completo" en verde, porque el estudiante canceló el
   curso de una sola vez (no por módulos individuales).
4. **Estados de cada celda:**
   - **✓ Pagado** (verde): el módulo recibió al menos un pago directo
     que cubre su valor esperado.
   - **○ Sin pagar** (rojo): el módulo no recibió pagos directos, o los
     que recibió no cubren el valor esperado. En este último caso, se
     muestra una nota en gris debajo: `abonó $X`.

Toda esta lógica vive en `Matricula.desglose_pagos_por_modulo()`
(`academia/models.py`). Devuelve por cada módulo:

```python
{'numero': 1, 'pagado': Decimal('60.00'), 'esperado': Decimal('60.00'),
 'estado': 'Pagado', 'fecha_ultimo_pago': date(2026, 5, 9)}
```

**Ejemplo:** curso $120 / 2 módulos. Estudiante paga reserva $20 +
módulo 1 $50 (total $70 pagado, saldo total $50).

| | Mód. 1 ($60) | Mód. 2 ($60) |
|---|---|---|
| Estado | ◐ Parcial — $50 | ○ Sin pagar |
| Pagado | $50 | $0 |

La reserva ($20) NO se asigna al módulo 1; queda como abono libre que
suma al saldo total pero no aparece en la matriz. Si quiere que esos
$20 cuenten para el módulo 1, debe registrarlos como un abono de tipo
"Por Módulo" con `numero_modulo=1`.

> **Nota sobre decimales:** `esperado` se redondea a 2 decimales para
> que la comparación contra los pagos reales (que solo manejan 2
> decimales) funcione correctamente. Para cursos cuyo valor neto no
> sea divisible exacto entre el número de módulos (ej. $100 / 3), la
> suma de los `esperado` puede quedar 1 centavo arriba o abajo del
> valor neto. El saldo total real se calcula desde `valor_pagado` (que
> sí es exacto), no desde la suma de los módulos.

Ver [`CHANGELOG_v2.4_pagos_modulo.md`](./CHANGELOG_v2.4_pagos_modulo.md)
para el detalle de los bugs corregidos en esta versión.

---

## 🔐 Variables de entorno (`.env`)

```env
SECRET_KEY=...                  # Genera una con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DEBUG=True                      # False en producción
DB_NAME=                        # vacío → SQLite (recomendado para empezar)
DB_USER=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

> ⚠️ El archivo `.env` real **nunca** debe subirse al repositorio. Ya
> está en `.gitignore`.

Para producción con MySQL: instala el driver y rellena las variables.

```bash
pip install mysqlclient
```

---

## 🗺 Rutas principales

| Ruta | Quién | Descripción |
|------|:-:|-------------|
| `/login/` | Todos | Inicio de sesión |
| `/bienvenida/` | Todos | Dashboard principal |
| `/cursos/` | Admin + Asesor | Listado y administración de cursos |
| `/matricula/` | Admin + Asesor | Registro de matrículas |
| `/pagos/` | Admin + Asesor | Listado general de pagos |
| `/pagos/por-modulo/` | Admin + Asesor | **Matriz de avance por módulo** |
| `/matricula/<id>/abonos/` | Admin + Asesor | Pantalla detallada de abonos |
| `/abonos/<id>/recibo/` | Admin + Asesor | Recibo imprimible |
| `/admin/` | Superuser | Admin de Django |

---

## 👥 Roles

Tres niveles de acceso (configurados con `python manage.py setup_roles`):

- **Administrador** — control total, edita todo.
- **Asesor** — registra matrículas, abonos, ve reportes.
- **Recepción** — consulta limitada (sin edición financiera).

Para asignar un rol a un usuario: entra al admin de Django, abre el
usuario, y agrégale el grupo correspondiente.

---

## 🛠 Comandos útiles

```bash
# Recalcular el valor pagado de TODAS las matrículas (si quedó descuadrado)
python manage.py shell
>>> from academia.models import Matricula
>>> for m in Matricula.objects.all(): m.recalcular_valor_pagado()

# Verificar que el sistema está bien configurado
python manage.py check

# Ver todas las migraciones
python manage.py showmigrations

# Backup de la base de datos (SQLite)
cp db.sqlite3 backup-$(date +%Y%m%d).sqlite3

# Backup en MySQL
mysqldump -u DB_USER -p DB_NAME > backup-$(date +%Y%m%d).sql
```

---

## 📦 Despliegue en producción

Resumen mínimo (no exhaustivo):

1. `DEBUG=False` y `SECRET_KEY` aleatoria en `.env`.
2. Agregar el dominio real a `ALLOWED_HOSTS` en `core/settings.py`.
3. `python manage.py collectstatic` para juntar estáticos en
   `staticfiles/`.
4. Servir con `gunicorn` + `nginx` (Linux) o `IIS` + `wfastcgi`
   (Windows). Para Windows ya tienes la guía paso a paso en
   `Guia_Instalacion_Windows.pdf`.

---

## 📝 Historial de versiones

- **v2.5** — Correcciones de cálculos financieros: arreglado el doble
  conteo de ingresos en el panel administrativo (los comprobantes
  vinculados a matrículas ya no se suman aparte de los abonos);
  arreglado el cálculo del valor por módulo con decimales no exactos
  (ej. $100/3); agregada validación de rango para el número de módulo
  en `AbonoForm`; reescrita la documentación de Pagos por Módulo para
  describir el comportamiento real (sin distribución de reserva al
  Mód.1, sin derrame).
  → [`CHANGELOG_v2.5_calculos.md`](./CHANGELOG_v2.5_calculos.md)
- **v2.4** — Pagos por Módulo: visual binario (Pagado / Sin pagar) en
  la matriz, manteniendo 3 estados internos para reportes/filtros;
  arreglados los crashes en exports Excel/PDF con filtro de estado
  activo.
  → [`CHANGELOG_v2.4_pagos_modulo.md`](./CHANGELOG_v2.4_pagos_modulo.md)
- **v2.3** — Reportes adicionales →
  [`CHANGELOG_v2.3_adicional.md`](./CHANGELOG_v2.3_adicional.md)
- **v2.2** — [`CHANGELOG_v2.2.md`](./CHANGELOG_v2.2.md)
- **v2.1** — [`CHANGELOG_v2.1.md`](./CHANGELOG_v2.1.md)
- **v2** — [`CHANGELOG_v2.md`](./CHANGELOG_v2.md)

---

## 🐛 ¿Encontraste un bug?

Reporta en GitHub Issues con:
1. La URL donde ocurrió.
2. Qué hiciste antes del error.
3. El mensaje exacto (o un screenshot).
4. La cédula del estudiante / número de matrícula afectada (si
   aplica).

---

**Mantenido por Yandri Guevara — Formación Técnica y Profesional EC.**
