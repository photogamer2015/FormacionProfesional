# Migración: agregar link_comprobante al modelo Comprobante
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0007_jornada_opcional_y_abono_extra'),
    ]

    operations = [
        migrations.AddField(
            model_name='comprobante',
            name='link_comprobante',
            field=models.URLField(
                blank=True, max_length=500,
                verbose_name='Link del comprobante',
                help_text='Link a la foto del comprobante (Drive, Imgur, WhatsApp Web, etc.). Opcional.',
            ),
        ),
    ]
