"""
Migración:
1. Agrega los nuevos campos de modalidad a Curso y JornadaCurso.
2. Copia el campo legado `valor` (de cada curso existente) al nuevo
   `valor_presencial`, asumiendo que las matrículas anteriores eran presenciales.
3. Marca todas las jornadas existentes como modalidad='presencial'.
4. Agrega el campo registrado_por en Matricula (para auditoría de asesores).
"""

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


def copiar_valor_a_presencial(apps, schema_editor):
    """Para cursos existentes, valor → valor_presencial (la lógica anterior asumía presencial)."""
    Curso = apps.get_model('academia', 'Curso')
    for curso in Curso.objects.all():
        if curso.valor and not curso.valor_presencial:
            curso.valor_presencial = curso.valor
            curso.save(update_fields=['valor_presencial'])


def revertir_valor_presencial(apps, schema_editor):
    """Reversión: copia valor_presencial → valor (no perdemos datos)."""
    Curso = apps.get_model('academia', 'Curso')
    for curso in Curso.objects.all():
        if curso.valor_presencial and not curso.valor:
            curso.valor = curso.valor_presencial
            curso.save(update_fields=['valor'])


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0003_seed_data'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Curso: agregar campos de modalidad ────────────────────
        migrations.AddField(
            model_name='curso',
            name='ofrece_presencial',
            field=models.BooleanField(
                default=True,
                help_text='Marcar si el curso se ofrece en modalidad presencial.'
            ),
        ),
        migrations.AddField(
            model_name='curso',
            name='ofrece_online',
            field=models.BooleanField(
                default=False,
                help_text='Marcar si el curso se ofrece en modalidad online.'
            ),
        ),
        migrations.AddField(
            model_name='curso',
            name='valor_presencial',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'),
                help_text='Costo del curso presencial (USD).',
                max_digits=10
            ),
        ),
        migrations.AddField(
            model_name='curso',
            name='valor_online',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'),
                help_text='Costo del curso online (USD).',
                max_digits=10
            ),
        ),
        # Cambia el help_text del campo legado pero NO lo elimina
        migrations.AlterField(
            model_name='curso',
            name='valor',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'),
                help_text='[Legado] Valor único anterior. Reemplazado por valor_presencial / valor_online.',
                max_digits=10
            ),
        ),

        # ── JornadaCurso: agregar modalidad ───────────────────────
        migrations.AddField(
            model_name='jornadacurso',
            name='modalidad',
            field=models.CharField(
                choices=[('presencial', 'Presencial'), ('online', 'Online')],
                default='presencial',
                help_text='Modalidad de esta jornada.',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='jornadacurso',
            name='ciudad',
            field=models.CharField(
                help_text='Ciudad (presencial) o zona horaria/plataforma (online).',
                max_length=100
            ),
        ),
        migrations.AlterModelOptions(
            name='jornadacurso',
            options={
                'ordering': ['curso', 'modalidad', 'fecha_inicio'],
                'verbose_name': 'Jornada',
                'verbose_name_plural': 'Jornadas',
            },
        ),

        # ── Matricula: campo de auditoría ─────────────────────────
        migrations.AddField(
            model_name='matricula',
            name='registrado_por',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Usuario que registró la matrícula (admin o asesor).',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matriculas_registradas',
                to=settings.AUTH_USER_MODEL
            ),
        ),

        # ── Migración de datos: valor → valor_presencial ──────────
        migrations.RunPython(copiar_valor_a_presencial, revertir_valor_presencial),
    ]
