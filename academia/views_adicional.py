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

from .forms import (
    AdicionalInternoForm, AdicionalExternoForm,
    AdicionalSupletorioRapidoForm, PersonaExternaForm,
)
from .models import Adicional, Estudiante, Matricula, PersonaExterna
from .permisos import matricula_requerida, admin_requerido


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
        form = PersonaExternaForm()

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


# ─────────────────────────────────────────────────────────
# API para autocompletar
# ─────────────────────────────────────────────────────────

@matricula_requerida
def api_estudiante_existe(request, cedula):
    """Endpoint AJAX: devuelve datos del estudiante por cédula (para autocompletar)."""
    try:
        est = Estudiante.objects.get(cedula=cedula.strip())
        return JsonResponse({
            'existe': True,
            'apellidos': est.apellidos,
            'nombres': est.nombres,
            'correo': est.correo or '',
            'celular': est.celular or '',
            'ciudad': est.ciudad or '',
        })
    except Estudiante.DoesNotExist:
        return JsonResponse({'existe': False})


@matricula_requerida
def api_persona_externa(request, cedula):
    """Endpoint AJAX: devuelve datos de una persona externa por cédula."""
    try:
        p = PersonaExterna.objects.get(cedula=cedula.strip())
        return JsonResponse({
            'existe': True,
            'apellidos': p.apellidos,
            'nombres': p.nombres,
            'correo': p.correo or '',
            'celular': p.celular or '',
            'ciudad': p.ciudad or '',
        })
    except PersonaExterna.DoesNotExist:
        return JsonResponse({'existe': False})


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
