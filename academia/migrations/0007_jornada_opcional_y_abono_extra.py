# Migración: jornada con campos opcionales + banco y tipo en Abono
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0006_comprobante'),
    ]

    operations = [
        # ── JornadaCurso: hora_inicio y hora_fin → opcionales ──
        # (ciudad se queda como estaba, obligatoria como antes)
        migrations.AlterField(
            model_name='jornadacurso',
            name='hora_inicio',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='jornadacurso',
            name='hora_fin',
            field=models.TimeField(blank=True, null=True),
        ),

        # ── Abono: agregar banco y tipo_registro ──
        migrations.AddField(
            model_name='abono',
            name='banco',
            field=models.CharField(
                blank=True, max_length=20,
                choices=[
                    ('pichincha', 'Banco Pichincha'),
                    ('guayaquil', 'Banco Guayaquil'),
                    ('produbanco', 'Produbanco'),
                    ('pacifico', 'Banco Pacífico'),
                    ('payphone', 'Payphone'),
                    ('interbancaria', 'Interbancaria'),
                ],
                help_text='Banco usado (solo si el método es Transferencia bancaria).',
            ),
        ),
        migrations.AddField(
            model_name='abono',
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
    ]
