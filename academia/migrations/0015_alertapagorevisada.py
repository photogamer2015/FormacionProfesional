# Generated for v2.1 — alertas de pago pendiente
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0014_abono_cuenta_para_saldo_abono_numero_modulo_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertaPagoRevisada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_modulo', models.PositiveIntegerField(help_text='Módulo cuya alerta fue revisada.')),
                ('fecha', models.DateField(help_text='Día en que la alerta fue marcada como revisada.')),
                ('notas', models.TextField(blank=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('matricula', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='alertas_revisadas',
                    to='academia.matricula',
                )),
                ('revisada_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='alertas_revisadas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Alerta de pago revisada',
                'verbose_name_plural': 'Alertas de pago revisadas',
                'ordering': ['-fecha', '-creado'],
                'unique_together': {('matricula', 'numero_modulo', 'fecha')},
            },
        ),
    ]
