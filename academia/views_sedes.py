"""
Gestión de Sedes / Campus.

Solo accesible por administradores. Permite crear, editar y activar/desactivar
sedes (campus) sin tocar el código, de modo que el software pueda escalar a
nuevas ciudades o países (ej. Caracas, Venezuela) de forma autónoma.

Las sedes se agrupan por país en el listado.
"""
from collections import OrderedDict

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SedeForm
from .models import JornadaCurso, Sede
from .permisos import admin_requerido


@admin_requerido
def sedes_lista(request):
    """Listado de sedes agrupadas por país, con conteo de jornadas que las usan."""
    sedes = (
        Sede.objects
        .annotate(num_jornadas=Count('jornadas'))
        .order_by('pais', 'orden', 'nombre')
    )

    # Agrupar por país manteniendo el orden alfabético de países
    grupos = OrderedDict()
    for s in sedes:
        grupos.setdefault(s.pais or 'Sin país', []).append(s)

    grupos_lista = [
        {'pais': pais, 'sedes': lista, 'total': len(lista)}
        for pais, lista in grupos.items()
    ]

    return render(request, 'sedes/lista.html', {
        'grupos': grupos_lista,
        'total': sedes.count(),
        'total_activas': sedes.filter(activa=True).count(),
    })


@admin_requerido
def sede_crear(request):
    """Crea una nueva sede."""
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            sede = form.save()
            messages.success(
                request,
                f'Sede "{sede.nombre}" ({sede.pais}) creada correctamente.'
            )
            return redirect('academia:sedes_lista')
    else:
        form = SedeForm(initial={'pais': 'Ecuador', 'activa': True, 'orden': 0})

    return render(request, 'sedes/form.html', {
        'form': form,
        'modo': 'crear',
    })


@admin_requerido
def sede_editar(request, pk):
    """Edita una sede existente."""
    sede = get_object_or_404(Sede, pk=pk)
    if request.method == 'POST':
        form = SedeForm(request.POST, instance=sede)
        if form.is_valid():
            form.save()
            # Resincronizar el texto `ciudad` de las jornadas que usan esta sede,
            # por si cambió el nombre.
            for j in sede.jornadas.all():
                if j.ciudad != sede.nombre:
                    j.ciudad = sede.nombre
                    j.save(update_fields=['ciudad'])
            messages.success(request, f'Sede "{sede.nombre}" actualizada.')
            return redirect('academia:sedes_lista')
    else:
        form = SedeForm(instance=sede)

    return render(request, 'sedes/form.html', {
        'form': form,
        'modo': 'editar',
        'sede': sede,
        'num_jornadas': sede.jornadas.count(),
    })


@admin_requerido
@require_POST
def sede_toggle(request, pk):
    """Activa o desactiva una sede (no la borra, para no perder el historial)."""
    sede = get_object_or_404(Sede, pk=pk)
    sede.activa = not sede.activa
    sede.save(update_fields=['activa'])
    estado = 'activada' if sede.activa else 'desactivada'
    messages.success(request, f'Sede "{sede.nombre}" {estado}.')
    return redirect('academia:sedes_lista')


@admin_requerido
@require_POST
def sede_eliminar(request, pk):
    """
    Elimina una sede. Si hay jornadas que la usan, NO se borra: se desactiva
    para conservar la integridad histórica (las jornadas guardan también el
    nombre de ciudad en texto, así que no se pierde el dato).
    """
    sede = get_object_or_404(Sede, pk=pk)
    num = sede.jornadas.count()
    if num > 0:
        sede.activa = False
        sede.save(update_fields=['activa'])
        messages.warning(
            request,
            f'La sede "{sede.nombre}" tiene {num} jornada(s) asociada(s); '
            f'se desactivó en lugar de eliminarse para conservar el historial.'
        )
    else:
        nombre = sede.nombre
        sede.delete()
        messages.success(request, f'Sede "{nombre}" eliminada.')
    return redirect('academia:sedes_lista')
