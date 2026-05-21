from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0026_adicionalarchivado'),
    ]

    operations = [
        migrations.AddField(
            model_name='adicional',
            name='factura_realizada',
            field=models.CharField(
                choices=[('si', 'Sí'), ('no', 'No')],
                default='no',
                help_text='¿Se emitió factura para este adicional?',
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name='adicional',
            name='fact_nombres',
            field=models.CharField(
                blank=True,
                help_text='Nombres del titular de la factura.',
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name='adicional',
            name='fact_apellidos',
            field=models.CharField(
                blank=True,
                help_text='Apellidos del titular de la factura.',
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name='adicional',
            name='fact_cedula',
            field=models.CharField(
                blank=True,
                help_text='Cédula o RUC para la factura.',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='adicional',
            name='fact_correo',
            field=models.EmailField(
                blank=True,
                help_text='Correo electrónico para enviar la factura.',
                max_length=254,
            ),
        ),
        migrations.AddField(
            model_name='adicionalarchivado',
            name='factura_realizada',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='adicionalarchivado',
            name='fact_nombres',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='adicionalarchivado',
            name='fact_apellidos',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='adicionalarchivado',
            name='fact_cedula',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='adicionalarchivado',
            name='fact_correo',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
