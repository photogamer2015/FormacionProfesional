"""
Migración:
1. Crea el modelo Abono.
2. Para cada matrícula existente con valor_pagado > 0, crea un abono inicial
   (fecha = fecha_matricula, método = 'efectivo', recibo automático).

Esto preserva los datos: las matrículas que ya tenías pagadas siguen pagadas,
y cada pago previo queda registrado como un abono visible.
"""
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


def crear_abonos_iniciales(apps, schema_editor):
    """Convierte cada valor_pagado > 0 en un abono."""
    Matricula = apps.get_model('academia', 'Matricula')
    Abono = apps.get_model('academia', 'Abono')

    contador = 1
    for matricula in Matricula.objects.all().order_by('fecha_matricula', 'id'):
        if matricula.valor_pagado and matricula.valor_pagado > 0:
            if not Abono.objects.filter(matricula=matricula).exists():
                Abono.objects.create(
                    matricula=matricula,
                    fecha=matricula.fecha_matricula,
                    monto=matricula.valor_pagado,
                    metodo='efectivo',
                    numero_recibo=f'REC-{contador:04d}',
                    observaciones='Pago inicial migrado desde versión anterior.',
                    registrado_por=matricula.registrado_por,
                )
                contador += 1


def revertir_abonos_iniciales(apps, schema_editor):
    Abono = apps.get_model('academia', 'Abono')
    Abono.objects.filter(
        observaciones='Pago inicial migrado desde versión anterior.'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0004_modalidades'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Abono',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(help_text='Fecha en que se recibió el abono.')),
                ('monto', models.DecimalField(decimal_places=2, help_text='Cantidad recibida en este abono (USD).', max_digits=10)),
                ('metodo', models.CharField(
                    choices=[
                        ('efectivo', 'Efectivo'),
                        ('transferencia', 'Transferencia bancaria'),
                        ('tarjeta', 'Tarjeta de crédito/débito'),
                    ],
                    default='efectivo',
                    help_text='Forma en que se realizó el pago.',
                    max_length=20,
                )),
                ('numero_recibo', models.CharField(
                    blank=True, max_length=30, unique=True,
                    help_text='Número de comprobante. Si se deja vacío, se genera automáticamente.',
                )),
                ('observaciones', models.TextField(blank=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('matricula', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='abonos',
                    to='academia.matricula',
                )),
                ('registrado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='abonos_registrados',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Abono',
                'verbose_name_plural': 'Abonos',
                'ordering': ['-fecha', '-creado'],
            },
        ),
        migrations.RunPython(crear_abonos_iniciales, revertir_abonos_iniciales),
    ]
