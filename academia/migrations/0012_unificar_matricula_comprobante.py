"""
Migración 0012 — Unificación Matrícula ↔ Comprobante (mayo 2026):

Agrega a Matricula los campos del Comprobante:
- tipo_registro (Central 1/2/IA/Seguimiento)
- factura_realizada (Sí/No, default No)
- fact_nombres / fact_apellidos / fact_cedula / fact_correo
- link_comprobante

Agrega a Comprobante el vínculo con Matrícula:
- matricula (OneToOne, nullable, CASCADE)

Al guardar una matrícula, se crea/actualiza automáticamente un Comprobante
asociado para que el ranking siga funcionando.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0011_jornada_choices_y_tipo_matricula'),
    ]

    operations = [
        # ── Matrícula: campos del comprobante integrados ─────────────
        migrations.AddField(
            model_name='matricula',
            name='tipo_registro',
            field=models.CharField(
                blank=True, max_length=20,
                choices=[
                    ('central_1', 'Central 1'),
                    ('central_2', 'Central 2'),
                    ('central_ia', 'Central IA'),
                    ('seguimiento', 'Seguimiento'),
                ],
                help_text='Origen del registro: Central 1, Central 2, Central IA o Seguimiento.',
            ),
        ),
        migrations.AddField(
            model_name='matricula',
            name='factura_realizada',
            field=models.CharField(
                default='no', max_length=2,
                choices=[('si', 'Sí'), ('no', 'No')],
                help_text='¿Se emitió factura para esta matrícula?',
            ),
        ),
        migrations.AddField(
            model_name='matricula',
            name='fact_nombres',
            field=models.CharField(blank=True, max_length=120,
                help_text='Nombres del titular de la factura.'),
        ),
        migrations.AddField(
            model_name='matricula',
            name='fact_apellidos',
            field=models.CharField(blank=True, max_length=120,
                help_text='Apellidos del titular de la factura.'),
        ),
        migrations.AddField(
            model_name='matricula',
            name='fact_cedula',
            field=models.CharField(blank=True, max_length=20,
                help_text='Cédula o RUC para la factura.'),
        ),
        migrations.AddField(
            model_name='matricula',
            name='fact_correo',
            field=models.EmailField(blank=True, max_length=254,
                help_text='Correo electrónico para enviar la factura.'),
        ),
        migrations.AddField(
            model_name='matricula',
            name='link_comprobante',
            field=models.URLField(blank=True, max_length=500,
                help_text='Link a la foto del comprobante de pago (Drive, Imgur, WhatsApp Web, etc.).'),
        ),

        # ── Comprobante: FK a Matrícula ───────────────────────────────
        migrations.AddField(
            model_name='comprobante',
            name='matricula',
            field=models.OneToOneField(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comprobante',
                to='academia.matricula',
                verbose_name='Matrícula vinculada',
                help_text='Si el comprobante se generó automáticamente desde una matrícula, '
                          'aquí queda el vínculo. Si fue cargado manualmente desde el '
                          'módulo Comprobantes, queda vacío.',
            ),
        ),
    ]
