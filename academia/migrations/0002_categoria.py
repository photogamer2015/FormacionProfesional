# Migración manual: agrega Categoria y enlaza Curso con FK
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('color', models.CharField(
                    choices=[
                        ('#1a237e', 'Azul'),
                        ('#2e7d32', 'Verde'),
                        ('#c62828', 'Rojo'),
                        ('#f0ad4e', 'Naranja'),
                        ('#6a1b9a', 'Morado'),
                        ('#00838f', 'Cian'),
                        ('#5d4037', 'Marrón'),
                        ('#455a64', 'Gris'),
                    ],
                    default='#1a237e',
                    help_text='Color con el que se identifica la categoría.',
                    max_length=7,
                )),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden de aparición (menor = primero).')),
                ('activo', models.BooleanField(default=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.AddField(
            model_name='curso',
            name='categoria',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cursos', to='academia.categoria',
            ),
        ),
        migrations.AlterModelOptions(
            name='curso',
            options={
                'ordering': ['categoria__orden', 'nombre'],
                'verbose_name': 'Curso',
                'verbose_name_plural': 'Cursos',
            },
        ),
    ]
