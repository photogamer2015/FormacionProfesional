from django.urls import path, re_path
from . import views, views_pagos, views_comprobantes, views_admin, views_adicional

app_name = 'academia'

# Las URLs de cursos y matrícula reciben la modalidad como parte del path:
#   /matricula/presencial/...
#   /matricula/online/...
#   /cursos/presencial/
#   /cursos/online/

urlpatterns = [
    path('bienvenida/', views.bienvenida, name='bienvenida'),

    # ── Ayuda ──────────────────────────────────────────────────
    path('ayuda/', views.ayuda, name='ayuda'),

    # ── Matrícula (presencial u online) ────────────────────────
    path('matricula/<str:modalidad>/',
         views.matricula_menu, name='matricula_menu'),
    path('matricula/<str:modalidad>/registrar/',
         views.matricula_registrar, name='matricula_registrar'),
    path('matricula/<str:modalidad>/lista/',
         views.matricula_lista, name='matricula_lista'),
    path('matricula/<str:modalidad>/editar/<int:pk>/',
         views.matricula_editar, name='matricula_editar'),
    path('matricula/<str:modalidad>/eliminar/<int:pk>/',
         views.matricula_eliminar, name='matricula_eliminar'),
    # ↓ NUEVOS: exportación de la lista de matrículas
    path('matricula/<str:modalidad>/exportar/excel/',
         views.matricula_export_excel, name='matricula_export_excel'),
    path('matricula/<str:modalidad>/exportar/pdf/',
         views.matricula_export_pdf, name='matricula_export_pdf'),

    # ── Cursos: rutas específicas ANTES del catch-all de modalidad ──
    path('cursos/crear/', views.curso_crear, name='curso_crear'),
    path('cursos/<int:pk>/editar/', views.curso_editar, name='curso_editar'),
    path('cursos/<int:pk>/eliminar/', views.curso_eliminar, name='curso_eliminar'),
    path('cursos/<int:pk>/jornadas/', views.curso_jornadas, name='curso_jornadas'),
    path('cursos/<int:pk>/jornadas/eliminar/<int:jornada_pk>/',
         views.jornada_eliminar, name='jornada_eliminar'),
    path('cursos/<int:pk>/jornadas/editar/<int:jornada_pk>/',
         views.jornada_editar, name='jornada_editar'),

    # ── Cursos: lista por modalidad (catch-all, va al final) ────────
    path('cursos/<str:modalidad>/',
         views.cursos_lista, name='cursos_lista'),

    # ── Pagos ──────────────────────────────────────────────────
    path('pagos/', views_pagos.pagos_lista, name='pagos_lista'),
    path('pagos/exportar/', views_pagos.pagos_export, name='pagos_export'),
    path('pagos/exportar/pdf/', views_pagos.pagos_export_pdf, name='pagos_export_pdf'),

    # ── Pagos por Módulo (control semanal) ─────────────────────
    path('pagos/por-modulo/', views_pagos.pagos_por_modulo, name='pagos_por_modulo'),
    path('pagos/por-modulo/exportar/excel/',
         views_pagos.pagos_por_modulo_export_excel, name='pagos_por_modulo_export_excel'),
    path('pagos/por-modulo/exportar/pdf/',
         views_pagos.pagos_por_modulo_export_pdf, name='pagos_por_modulo_export_pdf'),

    # ── Hoja de Recaudación imprimible ─────────────────────────
    path('pagos/hoja-recaudacion/', views_pagos.hoja_recaudacion, name='hoja_recaudacion'),
    path('pagos/hoja-recaudacion/exportar/excel/',
         views_pagos.hoja_recaudacion_export_excel, name='hoja_recaudacion_export_excel'),
    path('pagos/hoja-recaudacion/exportar/pdf/',
         views_pagos.hoja_recaudacion_export_pdf, name='hoja_recaudacion_export_pdf'),

    # ── Alertas de pago pendiente ──────────────────────────────
    path('alertas/<int:matricula_pk>/revisar/',
         views_pagos.alerta_marcar_revisada, name='alerta_marcar_revisada'),

    # ── Clases en Recuperación ─────────────────────────────────
    path('recuperaciones/',
         views_pagos.recuperaciones_lista, name='recuperaciones_lista'),
    path('recuperaciones/exportar/excel/',
         views_pagos.recuperaciones_export_excel, name='recuperaciones_export_excel'),
    path('recuperaciones/exportar/pdf/',
         views_pagos.recuperaciones_export_pdf, name='recuperaciones_export_pdf'),
    path('recuperaciones/marcar/<int:matricula_pk>/',
         views_pagos.recuperacion_marcar, name='recuperacion_marcar'),
    path('recuperaciones/<int:recup_pk>/cobrar/',
         views_pagos.recuperacion_cobrar, name='recuperacion_cobrar'),
    path('recuperaciones/<int:recup_pk>/eliminar/',
         views_pagos.recuperacion_eliminar, name='recuperacion_eliminar'),

    # ── Abonos (sistema de pagos por matrícula) ───────────────
    path('matricula/<int:pk>/abonos/',
         views_pagos.matricula_abonos, name='matricula_abonos'),
    path('matricula/<int:pk>/retiro/',
         views_pagos.matricula_activar_retiro, name='matricula_activar_retiro'),
    path('matricula/<int:matricula_pk>/abonos/crear/',
         views_pagos.abono_crear, name='abono_crear'),
    path('matricula/<int:matricula_pk>/abonos/<int:abono_pk>/editar/',
         views_pagos.abono_editar, name='abono_editar'),
    path('matricula/<int:matricula_pk>/abonos/<int:abono_pk>/eliminar/',
         views_pagos.abono_eliminar, name='abono_eliminar'),
    path('abonos/exportar/', views_pagos.abonos_export, name='abonos_export'),
    path('abonos/<int:abono_pk>/recibo/',
         views_pagos.abono_recibo, name='abono_recibo'),

    # ── Historial de matriculados ──────────────────────────────
    path('historial/', views_pagos.historial_lista, name='historial_lista'),
    path('historial/exportar/', views_pagos.historial_export, name='historial_export'),

    # ── Estudiantes ───────────────────────────────────────────
    path('estudiantes/', views_pagos.estudiantes_lista, name='estudiantes_lista'),
    path('estudiantes/por-curso/', views_pagos.estudiantes_por_curso, name='estudiantes_por_curso'),
    path('estudiantes/exportar/', views_pagos.estudiantes_export, name='estudiantes_export'),
    path('estudiantes/<int:pk>/', views_pagos.estudiante_detalle, name='estudiante_detalle'),
    path('estudiantes/<int:pk>/exportar/', views_pagos.estudiante_export, name='estudiante_export'),

    # ── Comprobantes de Venta ─────────────────────────────────
    path('comprobantes/', views_comprobantes.comprobante_menu, name='comprobante_menu'),
    path('comprobantes/registrar/', views_comprobantes.comprobante_registrar, name='comprobante_registrar'),
    path('comprobantes/lista/', views_comprobantes.comprobante_lista, name='comprobante_lista'),
    path('comprobantes/totales/', views_comprobantes.comprobante_totales, name='comprobante_totales'),
    path('comprobantes/<int:pk>/editar/', views_comprobantes.comprobante_editar, name='comprobante_editar'),
    path('comprobantes/<int:pk>/eliminar/', views_comprobantes.comprobante_eliminar, name='comprobante_eliminar'),

    # ── Endpoints AJAX ─────────────────────────────────────────
    path('api/curso/<int:pk>/', views.api_curso_detalle, name='api_curso_detalle'),
    path('api/curso/<int:pk>/jornadas/',
         views.api_curso_jornadas, name='api_curso_jornadas'),
    path('api/categoria/crear/',
         views.api_categoria_crear, name='api_categoria_crear'),
    # ↓ NUEVOS: listar y eliminar categorías (para el selector custom del form de cursos)
    path('api/categoria/listar/',
         views.api_categoria_listar, name='api_categoria_listar'),
    path('api/categoria/<int:pk>/eliminar/',
         views.api_categoria_eliminar, name='api_categoria_eliminar'),
    # ↓ NUEVO: autocompletar datos del estudiante por cédula
    path('api/estudiante/<str:cedula>/',
         views.api_estudiante_por_cedula, name='api_estudiante_por_cedula'),
    # ↓ NUEVO: buscar estudiantes que comparten un mismo celular
    path('api/estudiantes-por-celular/<str:celular>/',
         views.api_estudiantes_por_celular, name='api_estudiantes_por_celular'),

    # ── Registro Administrativo ────────────────────────────────
    path('admin-panel/',
         views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/egresos/',
         views_admin.egresos_lista, name='admin_egresos_lista'),
    path('admin-panel/egresos/nuevo/',
         views_admin.egreso_crear, name='admin_egreso_crear'),
    path('admin-panel/egresos/<int:pk>/editar/',
         views_admin.egreso_editar, name='admin_egreso_editar'),
    path('admin-panel/egresos/<int:pk>/eliminar/',
         views_admin.egreso_eliminar, name='admin_egreso_eliminar'),

    # ── Exportación CSV ───────────────────────────────────────
    path('admin-panel/export/reporte/',
         views_admin.export_reporte_mes, name='admin_export_reporte'),
    path('admin-panel/export/egresos/',
         views_admin.export_egresos, name='admin_export_egresos'),

    # ── Adicional (Certificados, Examen Supletorio, Camisas extra) ──
    path('adicional/',
         views_adicional.adicional_menu, name='adicional_menu'),
    path('adicional/lista/',
         views_adicional.adicional_lista, name='adicional_lista'),
    path('adicional/registrar/interno/',
         views_adicional.adicional_crear_interno, name='adicional_crear_interno'),
    path('adicional/registrar/externo/',
         views_adicional.adicional_crear_externo, name='adicional_crear_externo'),
    path('adicional/<int:pk>/editar/',
         views_adicional.adicional_editar, name='adicional_editar'),
    path('adicional/<int:pk>/eliminar/',
         views_adicional.adicional_eliminar, name='adicional_eliminar'),

    # ── Personas Externas ──
    path('adicional/personas-externas/',
         views_adicional.personas_externas_lista, name='personas_externas_lista'),
    path('adicional/personas-externas/registrar/',
         views_adicional.persona_externa_crear, name='persona_externa_crear'),
    path('adicional/personas-externas/<int:pk>/editar/',
         views_adicional.persona_externa_editar, name='persona_externa_editar'),
    path('adicional/personas-externas/<int:pk>/eliminar/',
         views_adicional.persona_externa_eliminar, name='persona_externa_eliminar'),

    # ── API auxiliares para autocompletar ──
    path('api/adicional/estudiante/<str:cedula>/',
         views_adicional.api_estudiante_existe, name='api_adicional_estudiante'),
    path('api/adicional/persona-externa/<str:cedula>/',
         views_adicional.api_persona_externa, name='api_adicional_persona_externa'),

    # ── Examen Supletorio rápido (desde matrícula) ──
    path('matricula/<int:matricula_pk>/supletorio/',
         views_adicional.supletorio_marcar, name='supletorio_marcar'),

     # ── Bot simple (keyword-based) ──────────────────────────────
     path('assistant/simple-chat/', views.assistant_simple_chat, name='assistant_simple_chat'),
     path('assistant/chat/', views.assistant_llm_chat, name='assistant_llm_chat'),
]