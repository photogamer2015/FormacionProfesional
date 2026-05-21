"""
Migración de datos: crea las categorías y cursos iniciales.
- Empresariales: 6 cursos
- Técnico: 8 cursos
- Vacacionales: vacía (lista para llenar)
"""
from django.db import migrations


CATEGORIAS_INICIALES = [
    {'nombre': 'Empresariales', 'color': '#1a237e', 'orden': 1,
     'descripcion': 'Cursos enfocados al ámbito profesional y empresarial.'},
    {'nombre': 'Técnico',       'color': '#2e7d32', 'orden': 2,
     'descripcion': 'Cursos técnicos y de oficios prácticos.'},
    {'nombre': 'Vacacionales',  'color': '#f0ad4e', 'orden': 3,
     'descripcion': 'Cursos vacacionales para temporadas específicas.'},
]


CURSOS_INICIALES = {
    'Empresariales': [
        'Tributación contable',
        'Gestión de Talento Humano',
        'Asistente Contable',
        'Excel',
        'Automatización con Python',
        'Marketing Digital',
    ],
    'Técnico': [
        'Servicio Técnico',
        'Refrigeración y Aires Acondicionados',
        'Electricidad Residencial',
        'Impresión 3D',
        'Mecánica de Motos',
        'Línea Blanca',
        'Corte y Confección',
        'Ebanistería Integral',
    ],
    'Vacacionales': [],
}


def crear_datos_iniciales(apps, schema_editor):
    Categoria = apps.get_model('academia', 'Categoria')
    Curso = apps.get_model('academia', 'Curso')

    cat_obj = {}
    for c in CATEGORIAS_INICIALES:
        obj, _ = Categoria.objects.get_or_create(
            nombre=c['nombre'],
            defaults={
                'color': c['color'],
                'orden': c['orden'],
                'descripcion': c['descripcion'],
            },
        )
        cat_obj[c['nombre']] = obj

    for nombre_cat, lista_cursos in CURSOS_INICIALES.items():
        categoria = cat_obj[nombre_cat]
        for nombre_curso in lista_cursos:
            Curso.objects.get_or_create(
                nombre=nombre_curso,
                defaults={'categoria': categoria, 'valor': 0},
            )


def borrar_datos_iniciales(apps, schema_editor):
    """Solo borra lo que no se haya tocado a mano."""
    Categoria = apps.get_model('academia', 'Categoria')
    Curso = apps.get_model('academia', 'Curso')
    nombres_cat = [c['nombre'] for c in CATEGORIAS_INICIALES]
    Curso.objects.filter(categoria__nombre__in=nombres_cat, valor=0).delete()
    Categoria.objects.filter(nombre__in=nombres_cat, cursos__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0002_categoria'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales, borrar_datos_iniciales),
    ]
