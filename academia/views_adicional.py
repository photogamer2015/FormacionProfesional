"""
Vistas del módulo ADICIONAL.

Maneja la venta/registro de servicios y productos adicionales:
- Certificados (matrícula, asistencia, antiguo)
- Examen supletorio
- Camisas extra

Las personas pueden ser:
- Estudiantes INTERNOS de la academia (FK Estudiante)
- Personas EXTERNAS no matriculadas (FK PersonaExterna)

Estos ingresos suman al total del mes en el dashboard administrativo
y aparecen como un KPI separado con el "+".
"""
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    AdicionalInternoForm, AdicionalExternoForm,
    AdicionalSupletorioRapidoForm, PersonaExternaForm,
)
from .models import (
    Adicional, Estudiante, EstudianteArchivado, Matricula, MatriculaArchivada,
    PersonaExterna,
)
from .permisos import matricula_requerida, admin_requerido


def _buscar_estudiante_archivado(cedula):
    archivado = (
        EstudianteArchivado.objects
        .filter(cedula=cedula)
        .order_by('-archivado_en')
        .first()
    )
    if archivado:
        return archivado
    return (
        MatriculaArchivada.objects
        .filter(cedula=cedula)
        .order_by('-archivado_en')
        .first()
    )


# ─────────────────────────────────────────────────────────
# Menú principal del módulo Adicional
# ─────────────────────────────────────────────────────────

@matricula_requerida
def adicional_menu(request):
    """Menú principal del módulo Adicional."""
    total_adicionales = Adicional.objects.count()
    total_externas = PersonaExterna.objects.count()
    total_valor = Adicional.objects.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

    # Conteo por tipo
    por_tipo = (Adicional.objects
                .values('tipo_adicional')
                .annotate(count=Count('id'), total=Sum('valor'))
                .order_by('-total'))
    tipos_dict = {t[0]: t[1] for t in Adicional.TIPOS_ADICIONAL}
    desglose = []
    for t in por_tipo:
        desglose.append({
            'tipo': t['tipo_adicional'],
            'label': tipos_dict.get(t['tipo_adicional'], t['tipo_adicional']),
            'count': t['count'],
            'total': t['total'] or Decimal('0.00'),
        })

    return render(request, 'adicional/menu.html', {
        'total_adicionales': total_adicionales,
        'total_externas': total_externas,
        'total_valor': total_valor,
        'desglose_tipos': desglose,
    })


# ─────────────────────────────────────────────────────────
# Lista de Adicionales
# ─────────────────────────────────────────────────────────

@matricula_requerida
def adicional_lista(request):
    """Lista todos los adicionales con filtros."""
    qs = Adicional.objects.select_related(
        'estudiante', 'persona_externa', 'curso',
        'matricula_origen', 'registrado_por',
    )

    # Filtros
    tipo = (request.GET.get('tipo') or '').strip()
    origen = (request.GET.get('origen') or '').strip()  # interno / externo
    desde = (request.GET.get('desde') or '').strip()
    hasta = (request.GET.get('hasta') or '').strip()
    q = (request.GET.get('q') or '').strip()

    if tipo:
        qs = qs.filter(tipo_adicional=tipo)
    if origen == 'interno':
        qs = qs.filter(estudiante__isnull=False)
    elif origen == 'externo':
        qs = qs.filter(persona_externa__isnull=False)
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)
    if q:
        qs = qs.filter(
            Q(estudiante__cedula__icontains=q) |
            Q(estudiante__apellidos__icontains=q) |
            Q(estudiante__nombres__icontains=q) |
            Q(persona_externa__cedula__icontains=q) |
            Q(persona_externa__apellidos__icontains=q) |
            Q(persona_externa__nombres__icontains=q) |
            Q(curso__nombre__icontains=q)
        )

    qs = qs.order_by('-fecha', '-creado')

    total_filtrado = qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

    return render(request, 'adicional/lista.html', {
        'adicionales': qs[:300],
        'total_filtrado': total_filtrado,
        'count': qs.count(),
        'tipos_choices': Adicional.TIPOS_ADICIONAL,
        'filtros': {
            'tipo': tipo,
            'origen': origen,
            'desde': desde,
            'hasta': hasta,
            'q': q,
        },
    })


# ─────────────────────────────────────────────────────────
# Crear Adicional — INTERNO
# ─────────────────────────────────────────────────────────

@matricula_requerida
@transaction.atomic
def adicional_crear_interno(request):
    """Registrar un Adicional para un estudiante interno de la academia."""
    if request.method == 'POST':
        form = AdicionalInternoForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.registrado_por = request.user
            ad.save()
            messages.success(
                request,
                f'Adicional registrado: {ad.get_tipo_adicional_display()} para '
                f'{ad.estudiante.nombre_completo} (${ad.valor:.2f}).'
            )
            return redirect('academia:adicional_lista')
    else:
        form = AdicionalInternoForm(initial={'fecha': date.today()})

    return render(request, 'adicional/form_interno.html', {
        'form': form,
        'modo': 'crear',
        'titulo': 'Registrar Adicional — Estudiante Interno',
    })


# ─────────────────────────────────────────────────────────
# Crear Adicional — EXTERNO
# ─────────────────────────────────────────────────────────

@matricula_requerida
@transaction.atomic
def adicional_crear_externo(request):
    """Registrar un Adicional para una persona externa."""
    if request.method == 'POST':
        form = AdicionalExternoForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.registrado_por = request.user
            ad.save()
            messages.success(
                request,
                f'Adicional registrado: {ad.get_tipo_adicional_display()} para '
                f'{ad.persona_externa.nombre_completo} (${ad.valor:.2f}).'
            )
            return redirect('academia:adicional_lista')
    else:
        form = AdicionalExternoForm(initial={'fecha': date.today()})

    return render(request, 'adicional/form_externo.html', {
        'form': form,
        'modo': 'crear',
        'titulo': 'Registrar Adicional — Persona Externa',
    })


# ─────────────────────────────────────────────────────────
# Editar / Eliminar Adicional
# ─────────────────────────────────────────────────────────

@matricula_requerida
@transaction.atomic
def adicional_editar(request, pk):
    """Editar un adicional existente."""
    ad = get_object_or_404(Adicional, pk=pk)

    # Detectamos si es interno o externo y usamos el form correcto
    es_interno = ad.estudiante_id is not None

    if request.method == 'POST':
        if es_interno:
            form = AdicionalInternoForm(request.POST, instance=ad)
        else:
            form = AdicionalExternoForm(request.POST, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.save()
            messages.success(request, 'Adicional actualizado.')
            return redirect('academia:adicional_lista')
    else:
        initial = {}
        if es_interno and ad.estudiante_id:
            initial['cedula_estudiante'] = ad.estudiante.cedula
            form = AdicionalInternoForm(instance=ad, initial=initial)
        else:
            if ad.persona_externa_id:
                initial['cedula_externa'] = ad.persona_externa.cedula
            form = AdicionalExternoForm(instance=ad, initial=initial)

    return render(
        request,
        'adicional/form_interno.html' if es_interno else 'adicional/form_externo.html',
        {
            'form': form,
            'modo': 'editar',
            'titulo': f'Editar Adicional #{ad.pk}',
            'adicional': ad,
        }
    )


@matricula_requerida
def adicional_eliminar(request, pk):
    """Eliminar un adicional."""
    ad = get_object_or_404(Adicional, pk=pk)
    if request.method == 'POST':
        nombre = ad.persona_nombre
        tipo = ad.get_tipo_adicional_display()
        ad.delete()
        messages.success(request, f'Adicional eliminado: {tipo} de {nombre}.')
        return redirect('academia:adicional_lista')

    return render(request, 'adicional/confirmar_eliminar.html', {
        'adicional': ad,
    })


@matricula_requerida
@transaction.atomic
def adicional_archivar(request, pk):
    """Archiva un adicional manualmente (lo mueve a AdicionalArchivado y lo borra)."""
    ad = get_object_or_404(Adicional, pk=pk)
    if request.method == 'POST':
        nombre = ad.persona_nombre
        tipo = ad.get_tipo_adicional_display()
        from .views_cierre import _snapshot_adicional
        _snapshot_adicional(ad, None)
        ad.delete()
        messages.success(request, f'Adicional archivado correctamente: {tipo} de {nombre}.')
        return redirect('academia:adicional_lista')

    return render(request, 'adicional/confirmar_archivar.html', {
        'adicional': ad,
    })


@admin_requerido
@transaction.atomic
def adicional_cierre(request):
    """Cierre masivo de adicionales: los mueve al archivo permanente."""
    origen = (request.GET.get('origen') or request.POST.get('origen') or '').strip()
    qs = Adicional.objects.select_related(
        'estudiante', 'persona_externa', 'curso', 'registrado_por',
    )

    if origen == 'interno':
        qs = qs.filter(estudiante__isnull=False)
        origen_label = 'interno'
        titulo = 'Cierre adicional interno'
    elif origen == 'externo':
        qs = qs.filter(persona_externa__isnull=False)
        origen_label = 'externo'
        titulo = 'Cierre adicional externo'
    else:
        origen = ''
        origen_label = 'todos'
        titulo = 'Cierre adicional'

    total_registros = qs.count()
    total_valor = qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    desglose = (
        qs.values('tipo_adicional')
        .annotate(count=Count('id'), total=Sum('valor'))
        .order_by('-total')
    )
    tipos_dict = {t[0]: t[1] for t in Adicional.TIPOS_ADICIONAL}
    desglose_tipos = [
        {
            'tipo': row['tipo_adicional'],
            'label': tipos_dict.get(row['tipo_adicional'], row['tipo_adicional']),
            'count': row['count'],
            'total': row['total'] or Decimal('0.00'),
        }
        for row in desglose
    ]

    if request.method == 'POST':
        adicionales = list(qs)
        if not adicionales:
            messages.warning(request, 'No hay adicionales activos para cerrar.')
            return redirect('academia:adicional_lista')

        from .views_cierre import _snapshot_adicional
        for ad in adicionales:
            _snapshot_adicional(ad, None)
        Adicional.objects.filter(pk__in=[ad.pk for ad in adicionales]).delete()

        messages.success(
            request,
            f'Cierre adicional completado: {len(adicionales)} registro(s) archivado(s).'
        )
        if origen in ('interno', 'externo'):
            return redirect(f'{reverse("academia:adicionales_archivados_lista")}?origen={origen}')
        return redirect('academia:adicionales_archivados_lista')

    return render(request, 'adicional/cierre_confirmar.html', {
        'titulo': titulo,
        'origen': origen,
        'origen_label': origen_label,
        'total_registros': total_registros,
        'total_valor': total_valor,
        'desglose_tipos': desglose_tipos,
        'adicionales': qs.order_by('-fecha', '-creado')[:80],
    })


# ─────────────────────────────────────────────────────────
# Personas Externas — CRUD
# ─────────────────────────────────────────────────────────

@matricula_requerida
def personas_externas_lista(request):
    """Lista de personas externas registradas."""
    qs = PersonaExterna.objects.all().order_by('apellidos', 'nombres')

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(cedula__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(nombres__icontains=q) |
            Q(correo__icontains=q) |
            Q(celular__icontains=q)
        )

    return render(request, 'adicional/personas_externas.html', {
        'personas': qs[:300],
        'count': qs.count(),
        'q': q,
    })


@matricula_requerida
@transaction.atomic
def persona_externa_crear(request):
    """Registrar una nueva persona externa."""
    if request.method == 'POST':
        form = PersonaExternaForm(request.POST)
        if form.is_valid():
            persona = form.save()
            messages.success(
                request,
                f'Persona externa registrada: {persona.nombre_completo} '
                f'(cédula {persona.cedula}).'
            )
            # Si vino de la pantalla "+ Adicional Externo", regresar allá con cédula prellenada
            redir = request.POST.get('redir_to_adicional')
            if redir:
                from django.urls import reverse
                base = reverse('academia:adicional_crear_externo')
                return redirect(f'{base}?cedula={persona.cedula}')
            return redirect('academia:personas_externas_lista')
    else:
        initial = {
            'cedula': request.GET.get('cedula', ''),
            'nombres': request.GET.get('nombres', ''),
            'apellidos': request.GET.get('apellidos', ''),
            'correo': request.GET.get('correo', ''),
            'celular': request.GET.get('celular', ''),
        }
        form = PersonaExternaForm(initial=initial)

    return render(request, 'adicional/persona_externa_form.html', {
        'form': form,
        'modo': 'crear',
        'titulo': 'Registrar Persona Externa',
    })


@matricula_requerida
@transaction.atomic
def persona_externa_editar(request, pk):
    """Editar persona externa."""
    persona = get_object_or_404(PersonaExterna, pk=pk)
    if request.method == 'POST':
        form = PersonaExternaForm(request.POST, instance=persona)
        if form.is_valid():
            form.save()
            messages.success(request, 'Persona externa actualizada.')
            return redirect('academia:personas_externas_lista')
    else:
        form = PersonaExternaForm(instance=persona)

    return render(request, 'adicional/persona_externa_form.html', {
        'form': form,
        'modo': 'editar',
        'titulo': f'Editar Persona Externa — {persona.nombre_completo}',
        'persona': persona,
    })


@matricula_requerida
def persona_externa_eliminar(request, pk):
    """Eliminar persona externa (solo si no tiene adicionales registrados)."""
    persona = get_object_or_404(PersonaExterna, pk=pk)
    if persona.adicionales.exists():
        messages.error(
            request,
            f'No se puede eliminar a {persona.nombre_completo}: tiene '
            f'{persona.adicionales.count()} adicional(es) registrado(s). '
            'Elimina primero los adicionales.'
        )
        return redirect('academia:personas_externas_lista')

    if request.method == 'POST':
        nombre = persona.nombre_completo
        persona.delete()
        messages.success(request, f'Persona externa eliminada: {nombre}.')
        return redirect('academia:personas_externas_lista')

    return render(request, 'adicional/persona_externa_confirmar_eliminar.html', {
        'persona': persona,
    })


@matricula_requerida
@transaction.atomic
def persona_externa_archivar(request, pk):
    """Archiva todos los adicionales de una persona externa y elimina a la persona."""
    persona = get_object_or_404(PersonaExterna, pk=pk)
    if request.method == 'POST':
        nombre = persona.nombre_completo
        adicionales = persona.adicionales.all()
        count = adicionales.count()
        from .views_cierre import _snapshot_adicional
        for ad in adicionales:
            _snapshot_adicional(ad, None)
            ad.delete()
        persona.delete()
        messages.success(request, f'Persona externa archivada correctamente: {nombre} ({count} adicionales archivados).')
        return redirect('academia:personas_externas_lista')

    return render(request, 'adicional/persona_externa_confirmar_archivar.html', {
        'persona': persona,
    })


# ─────────────────────────────────────────────────────────
# API para autocompletar
# ─────────────────────────────────────────────────────────

@matricula_requerida
def api_estudiante_existe(request, cedula):
    """Endpoint AJAX: devuelve datos del estudiante por cédula (para autocompletar)."""
    try:
        cedula = cedula.strip()
        est = Estudiante.objects.filter(cedula=cedula).first()
        if est:
            return JsonResponse({
                'existe': True,
                'desde_archivo': False,
                'apellidos': est.apellidos,
                'nombres': est.nombres,
                'correo': est.correo or '',
                'celular': est.celular or '',
                'ciudad': est.ciudad or '',
            })

        # Si fue archivado por cierre de curso, sigue siendo un estudiante interno:
        # se muestra aquí y el formulario lo recupera al guardar el adicional.
        est_arch = _buscar_estudiante_archivado(cedula)
        if est_arch:
            ciudad = getattr(est_arch, 'ciudad', getattr(est_arch, 'ciudad_estudiante', '')) or ''
            return JsonResponse({
                'existe': True,
                'desde_archivo': True,
                'apellidos': est_arch.apellidos,
                'nombres': est_arch.nombres,
                'correo': est_arch.correo or '',
                'celular': est_arch.celular or '',
                'ciudad': ciudad,
            })

        # Check if it's actually a Persona Externa
        p = PersonaExterna.objects.filter(cedula=cedula).first()
        if p:
            return JsonResponse({
                'existe': False,
                'es_externa': True,
                'nombre_externo': p.nombre_completo,
            })

        return JsonResponse({'existe': False, 'es_externa': False, 'es_archivado': False})
    except Exception as e:
        return JsonResponse({'existe': False, 'error': str(e)})


@matricula_requerida
def api_persona_externa(request, cedula):
    """Endpoint AJAX: devuelve datos de una persona externa por cédula."""
    try:
        cedula = cedula.strip()
        p = PersonaExterna.objects.filter(cedula=cedula).first()
        if p:
            return JsonResponse({
                'existe': True,
                'apellidos': p.apellidos,
                'nombres': p.nombres,
                'correo': p.correo or '',
                'celular': p.celular or '',
                'ciudad': p.ciudad or '',
            })
        
        # Check if it's actually an Estudiante Interno
        est = Estudiante.objects.filter(cedula=cedula).first()
        if est:
            return JsonResponse({
                'existe': False,
                'es_estudiante': True,
                'nombre_estudiante': est.nombre_completo,
            })

        est_arch = _buscar_estudiante_archivado(cedula)
        if est_arch:
            return JsonResponse({
                'existe': False,
                'es_estudiante': True,
                'es_archivado': True,
                'nombre_estudiante': est_arch.nombre_completo,
            })
            
        return JsonResponse({'existe': False, 'es_estudiante': False})
    except Exception as e:
        return JsonResponse({'existe': False, 'error': str(e)})


# ─────────────────────────────────────────────────────────
# Examen Supletorio rápido — desde matrícula
# ─────────────────────────────────────────────────────────

@matricula_requerida
@transaction.atomic
def supletorio_marcar(request, matricula_pk):
    """
    Crear un Adicional tipo 'examen_supletorio' desde la vista
    de detalle de pagos de una matrícula.

    Pre-llena el estudiante, curso, modalidad y matricula_origen.
    Solo pide módulo, fecha, valor y método de pago.
    """
    matricula = get_object_or_404(
        Matricula.objects.select_related('estudiante', 'curso'),
        pk=matricula_pk,
    )

    if request.method == 'POST':
        form = AdicionalSupletorioRapidoForm(request.POST, matricula=matricula)
        if form.is_valid():
            ad = Adicional.objects.create(
                tipo_adicional='examen_supletorio',
                estudiante=matricula.estudiante,
                persona_externa=None,
                curso=matricula.curso,
                modalidad=matricula.modalidad or '',
                matricula_origen=matricula,
                numero_modulo=form.cleaned_data['numero_modulo'],
                fecha=form.cleaned_data['fecha'],
                valor=form.cleaned_data['valor'],
                metodo_pago=form.cleaned_data['metodo_pago'],
                observaciones=form.cleaned_data.get('observaciones', ''),
                registrado_por=request.user,
            )
            messages.success(
                request,
                f'Examen supletorio registrado para {matricula.estudiante.nombre_completo} '
                f'(Módulo {ad.numero_modulo}, ${ad.valor:.2f}). '
                f'Aparece en la sección Adicional.'
            )
            return redirect('academia:matricula_abonos', pk=matricula.pk)
    else:
        form = AdicionalSupletorioRapidoForm(
            initial={
                'fecha': date.today(),
                'metodo_pago': 'efectivo',
            },
            matricula=matricula,
        )

    return render(request, 'adicional/supletorio_marcar.html', {
        'form': form,
        'matricula': matricula,
    })
