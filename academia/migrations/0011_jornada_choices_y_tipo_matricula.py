"""
Migración 0011 — Cambios solicitados por GG (mayo 2026):

1. Jornada.descripcion ahora usa choices estandarizados:
   - lun_mie_vie  → "Lun, Mié, Vie."
   - mar_mie_jue  → "Mar, Mié, Jue."
   - mar_jue      → "Martes y Jueves"
   - sabados_intensivos   → "Sábados Intensivos"
   - domingos_intensivos  → "Domingos Intensivos"

2. Matrícula gana el campo `tipo_matricula`:
   - reserva_abono     → "Reserva / Abono"
   - reserva_modulo_1  → "Reserva + Módulo 1"
   - programa_completo → "Programa Completo"  (default)

Esta migración NO altera datos existentes en `JornadaCurso.descripcion`:
los registros con texto libre antiguo (ej. "Sábados intensivos") seguirán
guardados, y `get_descripcion_display()` cae al valor crudo si no encuentra
match en los choices. Aún así, recomendamos editar las jornadas viejas
para que adopten los nuevos códigos.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0010_remove_abono_tipo_registro_comprobante_tipo_registro_and_more'),
    ]

    operations = [
        # 1) Choices en JornadaCurso.descripcion (no cambia el schema, solo metadata)
        migrations.AlterField(
            model_name='jornadacurso',
            name='descripcion',
            field=models.CharField(
                choices=[
                    ('lun_mie_vie', 'Lun, Mié, Vie.'),
                    ('mar_mie_jue', 'Mar, Mié, Jue.'),
                    ('mar_jue', 'Martes y Jueves'),
                    ('sabados_intensivos', 'Sábados Intensivos'),
                    ('domingos_intensivos', 'Domingos Intensivos'),
                ],
                help_text='Días en que se dicta la jornada.',
                max_length=200,
            ),
        ),

        # 2) Nuevo campo tipo_matricula en Matrícula
        migrations.AddField(
            model_name='matricula',
            name='tipo_matricula',
            field=models.CharField(
                choices=[
                    ('reserva_abono', 'Reserva / Abono'),
                    ('reserva_modulo_1', 'Reserva + Módulo 1'),
                    ('programa_completo', 'Programa Completo'),
                ],
                default='programa_completo',
                help_text='Tipo de matrícula contratada por el estudiante.',
                max_length=30,
            ),
        ),
    ]
