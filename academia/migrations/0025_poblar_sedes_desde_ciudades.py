# Migración de datos: crea sedes a partir de las ciudades que ya tienen
# las jornadas existentes y vincula cada jornada a su sede correspondiente.
#
# Esto preserva los datos actuales (Guayaquil, Quito, etc.) sin pérdida y
# permite que de aquí en adelante las jornadas se gestionen por el catálogo
# de sedes administrable.

from django.db import migrations


def poblar_sedes(apps, schema_editor):
    Sede = apps.get_model('academia', 'Sede')
    JornadaCurso = apps.get_model('academia', 'JornadaCurso')

    # 1) Recolectar todas las ciudades distintas (no vacías) de las jornadas
    ciudades = (
        JornadaCurso.objects
        .exclude(ciudad__isnull=True)
        .exclude(ciudad__exact='')
        .values_list('ciudad', flat=True)
        .distinct()
    )

    # 2) Crear una Sede por cada ciudad (país Ecuador por defecto)
    mapa = {}  # nombre_normalizado -> Sede
    orden = 0
    for ciudad in ciudades:
        nombre = (ciudad or '').strip()
        if not nombre:
            continue
        clave = nombre.lower()
        if clave in mapa:
            continue
        sede, _creada = Sede.objects.get_or_create(
            nombre=nombre,
            pais='Ecuador',
            defaults={'orden': orden, 'activa': True},
        )
        mapa[clave] = sede
        orden += 1

    # 3) Vincular cada jornada (presencial con ciudad) a su sede
    for jornada in JornadaCurso.objects.exclude(ciudad__isnull=True).exclude(ciudad__exact=''):
        clave = (jornada.ciudad or '').strip().lower()
        sede = mapa.get(clave)
        if sede and jornada.sede_id != sede.id:
            jornada.sede_id = sede.id
            jornada.save(update_fields=['sede'])


def revertir(apps, schema_editor):
    # Al revertir, simplemente desvinculamos las jornadas de las sedes.
    # No borramos las sedes para no perder datos creados manualmente luego.
    JornadaCurso = apps.get_model('academia', 'JornadaCurso')
    JornadaCurso.objects.update(sede=None)


class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0024_jornadacurso_descripcion_otros_and_more'),
    ]

    operations = [
        migrations.RunPython(poblar_sedes, revertir),
    ]
