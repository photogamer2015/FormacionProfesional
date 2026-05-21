# Migración: Registro Administrativo (CategoriaEgreso + Egreso) + datos seed
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


CATEGORIAS_INICIALES = [
    {'nombre': 'Sueldos',           'color': '#1a237e', 'icono': '👥', 'orden': 1},
    {'nombre': 'Alquiler',          'color': '#5d4037', 'icono': '🏠', 'orden': 2},
    {'nombre': 'Servicios básicos', 'color': '#f0ad4e', 'icono': '💡', 'orden': 3},
    {'nombre': 'Materiales',        'color': '#00838f', 'icono': '📦', 'orden': 4},
    {'nombre': 'Comisiones',        'color': '#6a1b9a', 'icono': '💼', 'orden': 5},
    {'nombre': 'Marketing',         'color': '#2e7d32', 'icono': '📣', 'orden': 6},
    {'nombre': 'Otros',             'color': '#455a64', 'icono': '📌', 'orden': 7},
]


def crear_categorias_iniciales(apps, schema_editor):
    CategoriaEgreso = apps.get_model('academia', 'CategoriaEgreso')
    for c in CATEGORIAS_INICIALES:
        CategoriaEgreso.objects.get_or_create(
            nombre=c['nombre'],
            defaults={
                'color': c['color'],
                'icono': c['icono'],
                'orden': c['orden'],
            },
        )


def borrar_categorias_iniciales(apps, schema_editor):
    CategoriaEgreso = apps.get_model('academia', 'CategoriaEgreso')
    nombres = [c['nombre'] for c in CATEGORIAS_INICIALES]
    CategoriaEgreso.objects.filter(
        nombre__in=nombres, egresos__isnull=True
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0008_comprobante_link'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaEgreso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('color', models.CharField(
                    choices=[
                        ('#c62828', 'Rojo'), ('#f0ad4e', 'Naranja'),
                        ('#1a237e', 'Azul'), ('#2e7d32', 'Verde'),
                        ('#6a1b9a', 'Morado'), ('#00838f', 'Cian'),
                        ('#5d4037', 'Marrón'), ('#455a64', 'Gris'),
                    ],
                    default='#c62828', max_length=7,
                )),
                ('icono', models.CharField(
                    blank=True, max_length=4,
                    help_text='Emoji corto para mostrar (ej.: 💼, 🏠, 💡, 📦).',
                )),
                ('orden', models.PositiveIntegerField(default=0)),
                ('activo', models.BooleanField(default=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Categoría de egreso',
                'verbose_name_plural': 'Categorías de egresos',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='Egreso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(help_text='Fecha en que se efectuó el gasto.')),
                ('concepto', models.CharField(
                    max_length=200,
                    help_text='Descripción corta del gasto (ej.: "Sueldo Mayo - Ana").',
                )),
                ('monto', models.DecimalField(
                    decimal_places=2, max_digits=12,
                    help_text='Monto del gasto en USD.',
                )),
                ('notas', models.TextField(
                    blank=True,
                    help_text='Detalles adicionales: nº de factura, beneficiario, referencia, etc.',
                )),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('categoria', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='egresos', to='academia.categoriaegreso',
                )),
                ('registrado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='egresos_registrados',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Egreso',
                'verbose_name_plural': 'Egresos',
                'ordering': ['-fecha', '-creado'],
            },
        ),
        migrations.RunPython(crear_categorias_iniciales, borrar_categorias_iniciales),
    ]
