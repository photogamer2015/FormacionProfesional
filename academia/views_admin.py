"""
Registro Administrativo: dashboard financiero.

Solo accesible por administradores. Muestra:
- KPIs del mes (ingresos, egresos, balance)
- Gráfico de barras: ingresos vs egresos por mes (últimos 6 meses)
- Top egresos del mes por categoría
- Movimientos recientes (egresos + ingresos mezclados)
- CRUD de egresos
"""
import calendar
import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EgresoForm
from .models import (
    Abono, AbonoArchivado, Adicional, AdicionalArchivado, CategoriaEgreso,
    CierreAdministrativo, CierreCurso, Comprobante, Egreso, Matricula,
)
from .permisos import admin_requerido


MESES_ES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


def _rango_mes(anio, mes):
    """Devuelve (primer_dia, ultimo_dia) del mes dado."""
    primer = date(anio, mes, 1)
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    ultimo = date(anio, mes, ultimo_dia)
    return primer, ultimo


def _ingresos_periodo(desde, hasta):
    """
    Suma todos los ingresos en el rango de fechas.
    Combina:
      - Abonos (de matrículas registradas en el sistema): por fecha de abono.
      - Abonos ARCHIVADOS (de cursos cerrados): por fecha de abono. Esto es
        clave: cuando se cierra un curso, los Abonos vivos se borran, pero el
        dinero que entró NO debe desaparecer del registro administrativo. Por
        eso sumamos también los AbonoArchivado del periodo.
      - Comprobantes "manuales" (cargados desde el módulo Comprobantes sin
        crear matrícula): por fecha de inscripción, solo el pago_abono.
        IMPORTANTE: se EXCLUYEN los comprobantes vinculados a una matrícula,
        porque su pago_abono refleja el valor_pagado de esa matrícula y ese
        dinero ya está contado en `abonos`. Si no se excluyera, cada Abono
        contaría doble (una vez en `abonos` y otra en `ventas`).
      - Adicionales (certificados, examen supletorio, camisas extra): por fecha.
    """
    abonos = Abono.objects.filter(
        fecha__gte=desde, fecha__lte=hasta
    ).aggregate(s=Sum('monto'))['s'] or Decimal('0.00')

    # Abonos archivados (de cierres de curso) — conservan su fecha original
    abonos_archivados = AbonoArchivado.objects.filter(
        fecha__gte=desde, fecha__lte=hasta
    ).aggregate(s=Sum('monto'))['s'] or Decimal('0.00')

    # Solo comprobantes manuales (sin matrícula vinculada).
    # Los comprobantes-espejo de matrículas ya están contados via Abonos.
    ventas = Comprobante.objects.filter(
        fecha_inscripcion__gte=desde, fecha_inscripcion__lte=hasta,
        matricula__isnull=True,
    ).aggregate(s=Sum('pago_abono'))['s'] or Decimal('0.00')

    adicionales_vivos = Adicional.objects.filter(
        fecha__gte=desde, fecha__lte=hasta
    ).aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    adicionales_archivados = AdicionalArchivado.objects.filter(
        fecha__gte=desde, fecha__lte=hasta
    ).aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    adicionales = adicionales_vivos + adicionales_archivados

    return {
        'abonos': abonos,
        'abonos_archivados': abonos_archivados,
        'ventas': ventas,
        'adicionales': adicionales,
        'adicionales_vivos': adicionales_vivos,
        'adicionales_archivados': adicionales_archivados,
        'total': abonos + abonos_archivados + ventas + adicionales,
    }


def _cierres_curso_periodo(desde, hasta):
    """
    Devuelve los cierres de curso ejecutados dentro del periodo, con sus totales.
    Sirve para reflejar en el dashboard administrativo qué cursos se cerraron
    y cuánto dinero representaron.
    """
    qs = CierreCurso.objects.filter(
        fecha_cierre__date__gte=desde, fecha_cierre__date__lte=hasta
    ).order_by('-fecha_cierre')

    cierres = list(qs)
    total_cobrado = sum((c.total_cobrado for c in cierres), Decimal('0.00'))
    total_facturado = sum((c.total_facturado for c in cierres), Decimal('0.00'))
    total_matriculas = sum((c.total_matriculas for c in cierres), 0)

    return {
        'cierres': cierres,
        'count': len(cierres),
        'total_cobrado': total_cobrado,
        'total_facturado': total_facturado,
        'total_matriculas': total_matriculas,
    }


def _adicionales_periodo(desde, hasta):
    """
    Estadísticas de Adicionales registrados en el rango.
    Incluye activos y archivados para que el dashboard no pierda ingresos
    después de ejecutar un cierre adicional.
    """
    qs = Adicional.objects.filter(fecha__gte=desde, fecha__lte=hasta)
    arch_qs = AdicionalArchivado.objects.filter(fecha__gte=desde, fecha__lte=hasta)

    total_vivos = qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    total_archivados = arch_qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    total = total_vivos + total_archivados
    count = qs.count() + arch_qs.count()
    interno = (
        (qs.filter(estudiante__isnull=False).aggregate(s=Sum('valor'))['s'] or Decimal('0.00'))
        + (arch_qs.filter(origen_label='Estudiante interno').aggregate(s=Sum('valor'))['s'] or Decimal('0.00'))
    )
    externo = (
        (qs.filter(persona_externa__isnull=False).aggregate(s=Sum('valor'))['s'] or Decimal('0.00'))
        + (arch_qs.filter(origen_label='Persona externa').aggregate(s=Sum('valor'))['s'] or Decimal('0.00'))
    )

    # Desglose por tipo
    por_tipo_qs = (qs.values('tipo_adicional')
                     .annotate(total=Sum('valor'), count=Count('id'))
                     .order_by('-total'))
    por_tipo_arch_qs = (
        arch_qs.values('tipo_adicional')
        .annotate(total=Sum('valor'), count=Count('id'))
        .order_by('-total')
    )
    tipos_dict = {t[0]: t[1] for t in Adicional.TIPOS_ADICIONAL}
    por_tipo_map = {}
    for r in por_tipo_qs:
        codigo = r['tipo_adicional']
        por_tipo_map[codigo] = {
            'codigo': codigo,
            'label': tipos_dict.get(codigo, codigo),
            'total': r['total'] or Decimal('0.00'),
            'count': r['count'] or 0,
        }
    for r in por_tipo_arch_qs:
        codigo = r['tipo_adicional']
        item = por_tipo_map.setdefault(codigo, {
            'codigo': codigo,
            'label': tipos_dict.get(codigo, codigo),
            'total': Decimal('0.00'),
            'count': 0,
        })
        item['total'] += r['total'] or Decimal('0.00')
        item['count'] += r['count'] or 0
    por_tipo = sorted(por_tipo_map.values(), key=lambda item: item['total'], reverse=True)

    return {
        'total': total,
        'activos': total_vivos,
        'archivados': total_archivados,
        'count': count,
        'interno': interno,
        'externo': externo,
        'por_tipo': por_tipo,
    }


def _adicionales_archivados_periodo(desde, hasta):
    """Adicionales movidos al archivo durante el mes seleccionado."""
    qs = AdicionalArchivado.objects.filter(
        archivado_en__date__gte=desde,
        archivado_en__date__lte=hasta,
    )
    total = qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    interno = qs.filter(origen_label='Estudiante interno').aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    externo = qs.filter(origen_label='Persona externa').aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
    return {
        'total': total,
        'count': qs.count(),
        'interno': interno,
        'externo': externo,
    }


# ─────────────────────────────────────────────────────────
# Análisis por TIPO DE PAGO (Abono / Pago Completo / Por
# Módulo / Clase de Recuperación)  ─ usado en gráficos
# ─────────────────────────────────────────────────────────

# Etiquetas oficiales y colores para cada tipo de pago.
# Usamos los mismos códigos de Abono.TIPOS_PAGO.
TIPOS_PAGO_INFO = [
    ('abono',          'Abono',                 '#1a237e'),  # azul
    ('pago_completo',  'Pago Completo',         '#2e7d32'),  # verde
    ('por_modulo',     'Por Módulo',            '#f0ad4e'),  # naranja
    ('recuperacion',   'Clase de Recuperación', '#c62828'),  # rojo
]


def _tipos_pago_periodo(desde, hasta):
    """
    Devuelve un dict {codigo_tipo: {'label', 'total', 'count', 'color'}}
    con la suma y conteo de abonos por tipo de pago en el rango.

    Solo se cuentan abonos cuyo cuenta_para_saldo=True para coherencia con
    los ingresos del mes (las recuperaciones cobradas aparte se reportan
    por separado en `recuperaciones_aparte`).
    """
    qs = (Abono.objects
          .filter(fecha__gte=desde, fecha__lte=hasta)
          .values('tipo_pago')
          .annotate(total=Sum('monto'), count=Count('id')))

    base = {
        codigo: {
            'codigo': codigo,
            'label': label,
            'color': color,
            'total': Decimal('0.00'),
            'count': 0,
        }
        for codigo, label, color in TIPOS_PAGO_INFO
    }
    for r in qs:
        c = r['tipo_pago']
        if c in base:
            base[c]['total'] = r['total'] or Decimal('0.00')
            base[c]['count'] = r['count'] or 0
    return base


def _recuperaciones_periodo(desde, hasta):
    """
    Devuelve estadísticas de clases de recuperación cobradas en el rango.
    Suma TODOS los abonos tipo recuperación (cuenten o no para saldo) para
    dar visibilidad real a cuánto se está facturando por recuperaciones.
    """
    qs = Abono.objects.filter(
        tipo_pago='recuperacion',
        fecha__gte=desde, fecha__lte=hasta,
    )
    total = qs.aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    cuentan = qs.filter(cuenta_para_saldo=True).aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    aparte = qs.filter(cuenta_para_saldo=False).aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    return {
        'total': total,
        'cuentan_para_saldo': cuentan,
        'aparte': aparte,
        'count': qs.count(),
    }


def _egresos_periodo(desde, hasta):
    """Suma egresos en el rango."""
    return Egreso.objects.filter(
        fecha__gte=desde, fecha__lte=hasta
    ).aggregate(s=Sum('monto'))['s'] or Decimal('0.00')


def _retiros_periodo(desde, hasta):
    """Suma la deuda perdonada de las matrículas en retiro voluntario en el rango."""
    retiros_qs = Matricula.objects.filter(
        estado='retiro_voluntario',
        fecha_matricula__gte=desde, 
        fecha_matricula__lte=hasta
    )
    total = Decimal('0.00')
    for r in retiros_qs:
        total += (r.valor_curso or Decimal('0.00')) - (r.valor_pagado or Decimal('0.00'))
    return total


def _egresos_por_categoria_periodo(desde, hasta):
    """Devuelve lista [{categoria, total, color, icono}, …]."""
    qs = (Egreso.objects
          .filter(fecha__gte=desde, fecha__lte=hasta)
          .values('categoria__id', 'categoria__nombre',
                  'categoria__color', 'categoria__icono')
          .annotate(total=Sum('monto'))
          .order_by('-total'))
    return [
        {
            'id': r['categoria__id'],
            'nombre': r['categoria__nombre'],
            'color': r['categoria__color'],
            'icono': r['categoria__icono'],
            'total': r['total'] or Decimal('0.00'),
        }
        for r in qs
    ]




@admin_requerido
def admin_dashboard(request):
    """Panel principal del Registro Administrativo."""
    hoy = timezone.localdate()

    # Permite filtrar por mes/año via querystring (?anio=2026&mes=4)
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
        if not (1 <= mes <= 12):
            mes = hoy.month
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month

    desde, hasta = _rango_mes(anio, mes)

    # ── Datos del mes seleccionado ──
    ingresos = _ingresos_periodo(desde, hasta)
    egresos_total = _egresos_periodo(desde, hasta)
    balance = ingresos['total'] - egresos_total
    top_categorias = _egresos_por_categoria_periodo(desde, hasta)

    # ── NUEVO: Tipos de pago del mes (Abono / Pago Completo / Por Módulo / Recuperación) ──
    tipos_pago_mes_dict = _tipos_pago_periodo(desde, hasta)
    # Lista ordenada (mismo orden que TIPOS_PAGO_INFO) para iterar en el template
    tipos_pago_mes = [tipos_pago_mes_dict[c] for c, _l, _col in TIPOS_PAGO_INFO]
    total_tipos_pago_mes = sum(
        (x['total'] for x in tipos_pago_mes), Decimal('0.00')
    )
    # Datos para el gráfico circular (pie chart) por mes
    pie_tipos_pago = [
        {
            'codigo': x['codigo'],
            'label': x['label'],
            'color': x['color'],
            'total': float(x['total']),
            'count': x['count'],
        }
        for x in tipos_pago_mes
    ]

    # ── NUEVO: Estadísticas de Clases de Recuperación del mes ──
    recuperaciones_mes = _recuperaciones_periodo(desde, hasta)

    # ── NUEVO: Estadísticas de Adicionales del mes ──
    adicionales_mes = _adicionales_periodo(desde, hasta)
    adicionales_archivados_mes = _adicionales_archivados_periodo(desde, hasta)

    # ── Comparación con mes anterior ──
    if mes == 1:
        anio_prev, mes_prev = anio - 1, 12
    else:
        anio_prev, mes_prev = anio, mes - 1
    desde_prev, hasta_prev = _rango_mes(anio_prev, mes_prev)
    ing_prev = _ingresos_periodo(desde_prev, hasta_prev)['total']
    egr_prev = _egresos_periodo(desde_prev, hasta_prev)
    bal_prev = ing_prev - egr_prev
    recup_prev = _recuperaciones_periodo(desde_prev, hasta_prev)['total']
    adic_prev = _adicionales_periodo(desde_prev, hasta_prev)['total']

    def variacion(actual, anterior):
        if anterior == 0:
            return None
        return float(((actual - anterior) / abs(anterior)) * 100)

    # ── Datos para gráfico (últimos 6 meses) ──
    # Ahora incluimos también el monto facturado por clases de recuperación
    # y el desglose por tipo de pago para el gráfico circular por mes.
    serie_meses = []
    for i in range(5, -1, -1):
        # contar i meses hacia atrás desde el mes seleccionado
        m = mes - i
        a = anio
        while m <= 0:
            m += 12
            a -= 1
        d, h = _rango_mes(a, m)
        ing = _ingresos_periodo(d, h)['total']
        egr = _egresos_periodo(d, h)
        ret = _retiros_periodo(d, h)
        rec = _recuperaciones_periodo(d, h)['total']
        adic = _adicionales_periodo(d, h)['total']
        tp_dict = _tipos_pago_periodo(d, h)
        tipos_pago_mes_serie = [
            {
                'codigo': c,
                'label': tp_dict[c]['label'],
                'color': tp_dict[c]['color'],
                'total': float(tp_dict[c]['total']),
                'count': tp_dict[c]['count'],
            }
            for c, _l, _col in TIPOS_PAGO_INFO
        ]
        total_tp = sum((x['total'] for x in tipos_pago_mes_serie), 0.0)
        serie_meses.append({
            'label': f'{MESES_ES[m][:3]} {a}',
            'mes_nombre': f'{MESES_ES[m]} {a}',
            'ingresos': float(ing),
            'egresos': float(egr),
            'retiros': float(ret),
            'recuperaciones': float(rec),
            'adicionales': float(adic),
            'balance': float(ing - egr),
            'tipos_pago': tipos_pago_mes_serie,
            'total_tipos_pago': total_tp,
        })

    # ── Total acumulado histórico (todo el sistema) ──
    total_abonos_hist = Abono.objects.aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    # Sumar también los abonos archivados (de cursos cerrados) para que el
    # histórico financiero no baje al ejecutar cierres de curso.
    total_abonos_arch_hist = AbonoArchivado.objects.aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    # Mismo criterio que `_ingresos_periodo`: solo comprobantes manuales
    # (sin matrícula vinculada) para no duplicar lo que ya está en Abonos.
    total_ventas_hist = Comprobante.objects.filter(
        matricula__isnull=True
    ).aggregate(s=Sum('pago_abono'))['s'] or Decimal('0.00')
    total_adicionales_hist = (
        (Adicional.objects.aggregate(s=Sum('valor'))['s'] or Decimal('0.00'))
        + (AdicionalArchivado.objects.aggregate(s=Sum('valor'))['s'] or Decimal('0.00'))
    )
    total_egresos_hist = Egreso.objects.aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    total_ingresos_hist = (
        total_abonos_hist + total_abonos_arch_hist
        + total_ventas_hist + total_adicionales_hist
    )
    balance_hist = total_ingresos_hist - total_egresos_hist

    # Por cobrar: saldos pendientes (informativo, no se cuenta como ingreso).
    # Se compone de dos fuentes que no se solapan:
    #   - Saldos pendientes de matrículas activas (la fuente de verdad para
    #     matrículas registradas en el sistema).
    #   - Diferencias de comprobantes manuales (sin matrícula vinculada).
    por_cobrar_matriculas = Decimal('0.00')
    for m_ in Matricula.objects.exclude(estado='retiro_voluntario'):
        s = m_.saldo
        if s > 0:
            por_cobrar_matriculas += s
    por_cobrar_comprobantes_manuales = Comprobante.objects.filter(
        matricula__isnull=True
    ).aggregate(s=Sum('diferencia'))['s'] or Decimal('0.00')
    por_cobrar_comprobantes = por_cobrar_matriculas + por_cobrar_comprobantes_manuales

    # Retiros Voluntarios (acumulado histórico de saldo perdonado)
    # Calculamos la diferencia entre el valor del curso y lo que pagaron de las matrículas en retiro
    retiros_qs = Matricula.objects.filter(estado='retiro_voluntario')
    total_retiros = Decimal('0.00')
    for r in retiros_qs:
        vc = r.valor_curso or Decimal('0.00')
        vp = r.valor_pagado or Decimal('0.00')
        total_retiros += (vc - vp)

    # ── Movimientos recientes del mes (últimos 10 egresos) ──
    egresos_recientes = (Egreso.objects
                         .filter(fecha__gte=desde, fecha__lte=hasta)
                         .select_related('categoria', 'registrado_por')
                         .order_by('-fecha', '-creado')[:10])

    # Lista de meses para el selector (últimos 24 meses)
    meses_selector = []
    for i in range(0, 24):
        m = hoy.month - i
        a = hoy.year
        while m <= 0:
            m += 12
            a -= 1
        meses_selector.append({
            'anio': a, 'mes': m,
            'label': f'{MESES_ES[m]} {a}',
            'seleccionado': (a == anio and m == mes),
        })

    # ── Cierres de CURSO del periodo (reflejar su dinero en el panel admin) ──
    cierres_curso_mes = _cierres_curso_periodo(desde, hasta)

    # ── Cierres ADMINISTRATIVOS previos (cortes de caja ya hechos) ──
    cierres_admin = CierreAdministrativo.objects.all()[:12]
    # ¿Ya existe un cierre administrativo para este mes?
    cierre_admin_existente = CierreAdministrativo.objects.filter(
        anio=anio, mes=mes
    ).first()

    return render(request, 'admin_panel/dashboard.html', {
        'anio': anio,
        'mes': mes,
        'mes_nombre': MESES_ES[mes],
        'desde': desde,
        'hasta': hasta,
        'ingresos': ingresos,
        'egresos_total': egresos_total,
        'balance': balance,
        'top_categorias': top_categorias,
        'egresos_recientes': egresos_recientes,
        'meses_selector': meses_selector,
        # Comparativa
        'ing_prev': ing_prev,
        'egr_prev': egr_prev,
        'bal_prev': bal_prev,
        'var_ingresos': variacion(ingresos['total'], ing_prev),
        'var_egresos': variacion(egresos_total, egr_prev),
        'var_balance': variacion(balance, bal_prev),
        'var_recuperaciones': variacion(recuperaciones_mes['total'], recup_prev),
        # Histórico
        'total_ingresos_hist': total_ingresos_hist,
        'total_egresos_hist': total_egresos_hist,
        'balance_hist': balance_hist,
        'total_abonos_hist': total_abonos_hist,
        'total_ventas_hist': total_ventas_hist,
        'total_adicionales_hist': total_adicionales_hist,
        'por_cobrar': por_cobrar_comprobantes,
        'total_retiros': total_retiros,
        # NUEVO: Tipos de pago del mes + Recuperaciones
        'tipos_pago_mes': tipos_pago_mes,
        'total_tipos_pago_mes': total_tipos_pago_mes,
        'pie_tipos_pago_json': json.dumps(pie_tipos_pago),
        'recuperaciones_mes': recuperaciones_mes,
        # ★ NUEVO: Adicionales del mes (KPI con +)
        'adicionales_mes': adicionales_mes,
        'adicionales_archivados_mes': adicionales_archivados_mes,
        'var_adicionales': variacion(adicionales_mes['total'], adic_prev),
        # ★ NUEVO: Cierres de curso y administrativos
        'cierres_curso_mes': cierres_curso_mes,
        'cierres_admin': cierres_admin,
        'cierre_admin_existente': cierre_admin_existente,
        # Gráfico (JSON serializable)
        'serie_meses_json': json.dumps(serie_meses),
    })


@admin_requerido
def egresos_lista(request):
    """Lista de todos los egresos con filtros."""
    qs = Egreso.objects.select_related('categoria', 'registrado_por')

    # Filtros
    categoria_id = request.GET.get('categoria', '').strip()
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    q = request.GET.get('q', '').strip()

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)
    if q:
        qs = qs.filter(concepto__icontains=q)

    total_filtrado = qs.aggregate(s=Sum('monto'))['s'] or Decimal('0.00')

    return render(request, 'admin_panel/egresos_lista.html', {
        'egresos': qs[:200],  # limitar a 200 para no quemar render
        'total_filtrado': total_filtrado,
        'categorias': CategoriaEgreso.objects.filter(activo=True),
        'filtros': {
            'categoria': categoria_id,
            'desde': desde,
            'hasta': hasta,
            'q': q,
        },
    })


@admin_requerido
def egreso_crear(request):
    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            egreso = form.save(commit=False)
            egreso.registrado_por = request.user
            egreso.save()
            messages.success(
                request,
                f'Egreso registrado: {egreso.concepto} (${egreso.monto}).'
            )
            return redirect('academia:admin_egresos_lista')
    else:
        form = EgresoForm(initial={'fecha': timezone.localdate()})
    return render(request, 'admin_panel/egreso_form.html', {
        'form': form,
        'modo': 'crear',
        'titulo': 'Registrar nuevo egreso',
    })


@admin_requerido
def egreso_editar(request, pk):
    egreso = get_object_or_404(Egreso, pk=pk)
    if request.method == 'POST':
        form = EgresoForm(request.POST, instance=egreso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Egreso actualizado.')
            return redirect('academia:admin_egresos_lista')
    else:
        form = EgresoForm(instance=egreso)
    return render(request, 'admin_panel/egreso_form.html', {
        'form': form,
        'egreso': egreso,
        'modo': 'editar',
        'titulo': f'Editar egreso #{egreso.pk}',
    })


@admin_requerido
@require_POST
def egreso_eliminar(request, pk):
    egreso = get_object_or_404(Egreso, pk=pk)
    concepto = egreso.concepto
    monto = egreso.monto
    egreso.delete()
    messages.success(
        request,
        f'Egreso eliminado: {concepto} (${monto}).'
    )
    return redirect('academia:admin_egresos_lista')


# ─────────────────────────────────────────────────────────
# Exportación a CSV
# ─────────────────────────────────────────────────────────

import csv
from django.http import HttpResponse


def _csv_response(filename):
    """
    Crea una respuesta HTTP CSV. Usa BOM UTF-8 para que Excel
    abra bien las tildes y la ñ en Windows.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # BOM para Excel
    return response


@admin_requerido
def export_reporte_mes(request):
    """
    Exporta el reporte financiero completo del mes:
    - Resumen (ingresos, egresos, balance)
    - Detalle de egresos
    - Detalle de ingresos por abonos
    - Detalle de ingresos por ventas/comprobantes
    Todo en un solo CSV.
    """
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
        if not (1 <= mes <= 12):
            mes = hoy.month
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month

    desde, hasta = _rango_mes(anio, mes)
    nombre_mes = MESES_ES[mes]

    ingresos = _ingresos_periodo(desde, hasta)
    egresos_total = _egresos_periodo(desde, hasta)
    balance = ingresos['total'] - egresos_total

    response = _csv_response(
        f'reporte_{anio}_{mes:02d}_{nombre_mes.lower()}.csv'
    )
    w = csv.writer(response)

    # ── Encabezado ─────────────────────────────────────
    w.writerow([f'REPORTE FINANCIERO — {nombre_mes.upper()} {anio}'])
    w.writerow([f'Período: {desde.strftime("%d/%m/%Y")} a {hasta.strftime("%d/%m/%Y")}'])
    w.writerow([f'Generado: {timezone.now().strftime("%d/%m/%Y %H:%M")}'])
    w.writerow([])

    # ── Resumen ────────────────────────────────────────
    w.writerow(['RESUMEN'])
    w.writerow(['Concepto', 'Monto (USD)'])
    w.writerow(['Ingresos por abonos (matrículas)', f'{ingresos["abonos"]:.2f}'])
    w.writerow(['Ingresos por ventas (comprobantes)', f'{ingresos["ventas"]:.2f}'])
    w.writerow(['TOTAL INGRESOS', f'{ingresos["total"]:.2f}'])
    w.writerow(['TOTAL EGRESOS', f'{egresos_total:.2f}'])
    w.writerow([
        'BALANCE NETO',
        f'{balance:.2f}',
        '(GANANCIA)' if balance > 0 else ('(PÉRDIDA)' if balance < 0 else '(EQUILIBRIO)')
    ])
    w.writerow([])

    # ── Egresos detallados ─────────────────────────────
    w.writerow(['EGRESOS DETALLADOS'])
    w.writerow(['Fecha', 'Categoría', 'Concepto', 'Monto (USD)', 'Notas', 'Registrado por'])
    egresos = (Egreso.objects
               .filter(fecha__gte=desde, fecha__lte=hasta)
               .select_related('categoria', 'registrado_por')
               .order_by('fecha'))
    for e in egresos:
        registrador = ''
        if e.registrado_por:
            registrador = e.registrado_por.get_full_name() or e.registrado_por.username
        w.writerow([
            e.fecha.strftime('%d/%m/%Y'),
            e.categoria.nombre,
            e.concepto,
            f'{e.monto:.2f}',
            e.notas or '',
            registrador,
        ])
    if not egresos:
        w.writerow(['(Sin egresos en este período)'])
    w.writerow([])

    # ── Ingresos por abonos ────────────────────────────
    w.writerow(['INGRESOS — ABONOS DE MATRÍCULAS'])
    w.writerow(['Fecha', 'Recibo', 'Estudiante', 'Cédula', 'Curso', 'Método', 'Banco', 'Monto (USD)'])
    abonos = (Abono.objects
              .filter(fecha__gte=desde, fecha__lte=hasta)
              .select_related('matricula__estudiante', 'matricula__curso')
              .order_by('fecha'))
    for a in abonos:
        est = a.matricula.estudiante
        w.writerow([
            a.fecha.strftime('%d/%m/%Y'),
            a.numero_recibo or '',
            est.nombre_completo,
            est.cedula,
            a.matricula.curso.nombre,
            a.get_metodo_display(),
            a.get_banco_display() if a.banco else '',
            f'{a.monto:.2f}',
        ])
    if not abonos:
        w.writerow(['(Sin abonos en este período)'])
    w.writerow([])

    # ── Ingresos por comprobantes ──────────────────────
    # Listar solo comprobantes manuales (sin matrícula vinculada). Los
    # comprobantes-espejo de matrículas ya están reflejados en la sección
    # de ABONOS arriba; listarlos aquí duplicaría el ingreso al ojo del
    # lector del reporte.
    w.writerow(['INGRESOS — VENTAS POR COMPROBANTE (solo ventas manuales)'])
    w.writerow(['Fecha insc.', 'Cliente', 'Celular', 'Curso', 'Modalidad',
                'Pago/Abono (USD)', 'Diferencia (USD)', 'Vendedora'])
    comprobantes = (Comprobante.objects
                    .filter(fecha_inscripcion__gte=desde, fecha_inscripcion__lte=hasta,
                            matricula__isnull=True)
                    .select_related('curso', 'vendedora')
                    .order_by('fecha_inscripcion'))
    for c in comprobantes:
        vendedora = c.vendedora_nombre or (c.vendedora.username if c.vendedora else '')
        w.writerow([
            c.fecha_inscripcion.strftime('%d/%m/%Y'),
            c.nombre_persona,
            c.celular,
            c.curso.nombre,
            c.get_modalidad_display(),
            f'{c.pago_abono:.2f}',
            f'{c.diferencia:.2f}',
            vendedora,
        ])
    if not comprobantes:
        w.writerow(['(Sin comprobantes en este período)'])

    return response


@admin_requerido
def export_egresos(request):
    """
    Exporta los egresos respetando los filtros activos
    (mismos parámetros GET que la lista).
    """
    qs = Egreso.objects.select_related('categoria', 'registrado_por')

    categoria_id = request.GET.get('categoria', '').strip()
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    q = request.GET.get('q', '').strip()

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)
    if q:
        qs = qs.filter(concepto__icontains=q)

    qs = qs.order_by('-fecha', '-creado')

    response = _csv_response(
        f'egresos_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    )
    w = csv.writer(response)
    w.writerow(['EGRESOS — Exportación filtrada'])
    if desde or hasta or categoria_id or q:
        filtros = []
        if desde: filtros.append(f'desde {desde}')
        if hasta: filtros.append(f'hasta {hasta}')
        if categoria_id:
            cat = CategoriaEgreso.objects.filter(pk=categoria_id).first()
            if cat: filtros.append(f'categoría: {cat.nombre}')
        if q: filtros.append(f'búsqueda: "{q}"')
        w.writerow(['Filtros: ' + ', '.join(filtros)])
    w.writerow([f'Generado: {timezone.now().strftime("%d/%m/%Y %H:%M")}'])
    w.writerow([])

    w.writerow(['Fecha', 'Categoría', 'Concepto', 'Monto (USD)', 'Notas', 'Registrado por'])

    total = Decimal('0.00')
    for e in qs:
        registrador = ''
        if e.registrado_por:
            registrador = e.registrado_por.get_full_name() or e.registrado_por.username
        w.writerow([
            e.fecha.strftime('%d/%m/%Y'),
            e.categoria.nombre,
            e.concepto,
            f'{e.monto:.2f}',
            e.notas or '',
            registrador,
        ])
        total += e.monto

    w.writerow([])
    w.writerow(['', '', 'TOTAL', f'{total:.2f}'])

    return response


# ═════════════════════════════════════════════════════════════════
# CIERRE ADMINISTRATIVO (corte de caja del periodo)
# ═════════════════════════════════════════════════════════════════

@admin_requerido
def cierre_admin_preview(request):
    """
    Vista previa del cierre administrativo de un mes: muestra el detalle de
    ingresos (incluidos los archivados de cursos cerrados), egresos y balance,
    antes de congelarlo.
    """
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
        if not (1 <= mes <= 12):
            mes = hoy.month
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month

    desde, hasta = _rango_mes(anio, mes)

    ingresos = _ingresos_periodo(desde, hasta)
    egresos_total = _egresos_periodo(desde, hasta)
    egresos_categorias = _egresos_por_categoria_periodo(desde, hasta)
    cierres_curso = _cierres_curso_periodo(desde, hasta)
    balance = ingresos['total'] - egresos_total

    existente = CierreAdministrativo.objects.filter(anio=anio, mes=mes).first()

    meses_selector = []
    for i in range(0, 24):
        m = hoy.month - i
        a = hoy.year
        while m <= 0:
            m += 12
            a -= 1
        meses_selector.append({
            'anio': a, 'mes': m,
            'label': f'{MESES_ES[m]} {a}',
            'seleccionado': (a == anio and m == mes),
        })

    return render(request, 'admin_panel/cierre_admin_preview.html', {
        'anio': anio,
        'mes': mes,
        'mes_nombre': MESES_ES[mes],
        'desde': desde,
        'hasta': hasta,
        'ingresos': ingresos,
        'egresos_total': egresos_total,
        'egresos_categorias': egresos_categorias,
        'cierres_curso': cierres_curso,
        'balance': balance,
        'existente': existente,
        'meses_selector': meses_selector,
    })


@admin_requerido
@require_POST
def cierre_admin_ejecutar(request):
    """Congela el corte de caja del mes en un CierreAdministrativo."""
    try:
        anio = int(request.POST.get('anio'))
        mes = int(request.POST.get('mes'))
        if not (1 <= mes <= 12):
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, 'Periodo no válido.')
        return redirect('academia:admin_dashboard')

    etiqueta = (request.POST.get('etiqueta', '').strip())[:80]
    observaciones = request.POST.get('observaciones', '').strip()

    desde, hasta = _rango_mes(anio, mes)
    ingresos = _ingresos_periodo(desde, hasta)
    egresos_total = _egresos_periodo(desde, hasta)
    egresos_categorias = _egresos_por_categoria_periodo(desde, hasta)
    cierres_curso = _cierres_curso_periodo(desde, hasta)
    balance = ingresos['total'] - egresos_total

    # Serializar el desglose de egresos por categoría
    egresos_detalle = [
        {
            'categoria': e['nombre'],
            'total': float(e['total']),
            'color': e.get('color', ''),
            'icono': e.get('icono', ''),
        }
        for e in egresos_categorias
    ]

    # Si ya existe un cierre para este mes, lo actualizamos (re-corte)
    cierre, _creado = CierreAdministrativo.objects.update_or_create(
        anio=anio, mes=mes,
        defaults={
            'etiqueta': etiqueta,
            'fecha_desde': desde,
            'fecha_hasta': hasta,
            'ingreso_abonos': ingresos['abonos'],
            'ingreso_abonos_archivados': ingresos['abonos_archivados'],
            'ingreso_ventas': ingresos['ventas'],
            'ingreso_adicionales': ingresos['adicionales'],
            'ingreso_total': ingresos['total'],
            'egreso_total': egresos_total,
            'egresos_detalle_json': json.dumps(egresos_detalle),
            'balance_neto': balance,
            'cierres_curso_incluidos': cierres_curso['count'],
            'monto_cierres_curso': cierres_curso['total_cobrado'],
            'observaciones': observaciones,
            'cerrado_por': request.user if request.user.is_authenticated else None,
        }
    )

    messages.success(
        request,
        f'✅ Cierre administrativo de {MESES_ES[mes]} {anio} guardado. '
        f'Ingresos ${ingresos["total"]:.2f} − Egresos ${egresos_total:.2f} = '
        f'Balance ${balance:.2f}.'
    )
    return redirect('academia:cierre_admin_detalle', pk=cierre.pk)


@admin_requerido
def cierre_admin_historial(request):
    """Lista todos los cierres administrativos (cortes de caja)."""
    qs = CierreAdministrativo.objects.all()

    anio = request.GET.get('anio', '').strip()
    mes = request.GET.get('mes', '').strip()
    if anio.isdigit():
        qs = qs.filter(anio=int(anio))
    if mes.isdigit() and 1 <= int(mes) <= 12:
        # Filtramos por el campo `mes` del propio cierre cuando existe;
        # si el cierre es anual (mes=NULL), se descarta del filtrado por mes.
        qs = qs.filter(mes=int(mes))

    cierres = list(qs)
    total_ingresos = sum((c.ingreso_total for c in cierres), Decimal('0.00'))
    total_egresos = sum((c.egreso_total for c in cierres), Decimal('0.00'))
    total_balance = sum((c.balance_neto for c in cierres), Decimal('0.00'))

    anios = sorted(
        set(CierreAdministrativo.objects.values_list('anio', flat=True)),
        reverse=True
    )

    return render(request, 'admin_panel/cierre_admin_historial.html', {
        'cierres': cierres,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'total_balance': total_balance,
        'anios': anios,
        'filtro_anio': anio,
        'filtro_mes': mes,
    })


@admin_requerido
def cierre_admin_detalle(request, pk):
    """Detalle de un cierre administrativo congelado."""
    cierre = get_object_or_404(CierreAdministrativo, pk=pk)

    egresos_detalle = []
    if cierre.egresos_detalle_json:
        try:
            egresos_detalle = json.loads(cierre.egresos_detalle_json)
        except (ValueError, TypeError):
            egresos_detalle = []

    # Cierres de curso que cayeron en el mismo periodo (informativo)
    cierres_curso = _cierres_curso_periodo(cierre.fecha_desde, cierre.fecha_hasta)

    return render(request, 'admin_panel/cierre_admin_detalle.html', {
        'cierre': cierre,
        'egresos_detalle': egresos_detalle,
        'cierres_curso': cierres_curso,
    })


@admin_requerido
@require_POST
def cierre_admin_eliminar(request, pk):
    """Elimina un cierre administrativo."""
    cierre = get_object_or_404(CierreAdministrativo, pk=pk)
    nombre = cierre.encabezado
    cierre.delete()
    messages.success(request, f'Cierre administrativo eliminado: {nombre}.')
    return redirect('academia:cierre_admin_historial')
