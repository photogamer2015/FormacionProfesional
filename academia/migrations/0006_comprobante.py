"""
Migración: crea el modelo Comprobante (registro de venta por asesora).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0005_abonos'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comprobante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modalidad', models.CharField(
                    choices=[('virtual', 'Virtual'), ('presencial', 'Presencial')],
                    max_length=20, verbose_name='Modalidad',
                )),
                ('fecha_inscripcion', models.DateField(verbose_name='Fecha de inscripción')),
                ('jornada', models.CharField(
                    help_text='Ej.: Sábados 08:00–12:00, Domingos intensivos…',
                    max_length=200, verbose_name='Jornada',
                )),
                ('inicio_curso', models.DateField(verbose_name='Inicio del curso')),
                ('nombre_persona', models.CharField(
                    max_length=200, verbose_name='Nombre de la persona',
                )),
                ('celular', models.CharField(max_length=20, verbose_name='Celular')),
                ('pago_abono', models.DecimalField(
                    decimal_places=2, max_digits=10,
                    help_text='Monto recibido al momento de la venta.',
                    verbose_name='Pago o abono (USD)',
                )),
                ('diferencia', models.DecimalField(
                    decimal_places=2, max_digits=10,
                    help_text='Saldo pendiente.',
                    verbose_name='Diferencia (USD)',
                )),
                ('vendedora_nombre', models.CharField(
                    blank=True, max_length=150,
                    verbose_name='Nombre de la vendedora (registro)',
                )),
                ('factura_realizada', models.CharField(
                    choices=[('si', 'Sí'), ('no', 'No')],
                    default='no', max_length=2,
                    verbose_name='Factura realizada',
                )),
                ('fact_nombres', models.CharField(max_length=120, verbose_name='Nombres (factura)')),
                ('fact_apellidos', models.CharField(max_length=120, verbose_name='Apellidos (factura)')),
                ('fact_cedula', models.CharField(max_length=20, verbose_name='Número de cédula (factura)')),
                ('fact_correo', models.EmailField(max_length=254, verbose_name='Correo electrónico (factura)')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('curso', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='comprobantes',
                    to='academia.curso', verbose_name='Curso',
                )),
                ('vendedora', models.ForeignKey(
                    help_text='Asesor/admin que registró la venta. Se asigna automáticamente.',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='comprobantes_registrados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Vendedora',
                )),
            ],
            options={
                'verbose_name': 'Comprobante',
                'verbose_name_plural': 'Comprobantes',
                'ordering': ['-fecha_inscripcion', '-creado'],
            },
        ),
    ]
