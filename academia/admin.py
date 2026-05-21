from django.contrib import admin
from .models import (
    Adicional, Categoria, Comprobante, Curso, JornadaCurso,
    Estudiante, Matricula, PersonaExterna, RecuperacionPendiente,
    AssistantQueryLog, CierreCurso, MatriculaArchivada, AbonoArchivado,
    EstudianteArchivado, AdicionalArchivado, CierreAdministrativo, Sede,
)


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais', 'orden', 'activa', 'num_jornadas')
    list_editable = ('orden', 'activa')
    list_filter = ('pais', 'activa')
    search_fields = ('nombre', 'pais')

    def num_jornadas(self, obj):
        return obj.jornadas.count()
    num_jornadas.short_description = '# jornadas'


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'color', 'activo', 'cantidad_cursos')
    list_editable = ('orden', 'activo')
    search_fields = ('nombre',)

    def cantidad_cursos(self, obj):
        return obj.cursos.count()
    cantidad_cursos.short_description = '# cursos'


class JornadaCursoInline(admin.TabularInline):
    model = JornadaCurso
    extra = 1
    fields = ('modalidad', 'descripcion', 'descripcion_otros', 'fecha_inicio', 'hora_inicio', 'hora_fin', 'sede', 'activo')


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'categoria',
        'ofrece_presencial', 'valor_presencial',
        'ofrece_online', 'valor_online',
        'duracion', 'activo',
    )
    list_filter = ('categoria', 'activo', 'ofrece_presencial', 'ofrece_online')
    search_fields = ('nombre',)
    autocomplete_fields = ('categoria',)
    inlines = [JornadaCursoInline]
    fieldsets = (
        (None, {
            'fields': ('categoria', 'nombre', 'descripcion', 'duracion', 'activo'),
        }),
        ('Modalidad presencial', {
            'fields': ('ofrece_presencial', 'valor_presencial'),
        }),
        ('Modalidad online', {
            'fields': ('ofrece_online', 'valor_online'),
        }),
        ('Legado (no usar)', {
            'classes': ('collapse',),
            'fields': ('valor',),
            'description': 'Campo antiguo conservado por compatibilidad. Usa los valores por modalidad.',
        }),
    )


@admin.register(JornadaCurso)
class JornadaCursoAdmin(admin.ModelAdmin):
    list_display = (
        'curso', 'modalidad', 'descripcion', 'descripcion_otros', 'fecha_inicio',
        'hora_inicio', 'hora_fin', 'sede', 'ciudad', 'activo',
    )
    list_filter = ('modalidad', 'activo', 'sede', 'ciudad', 'curso')
    search_fields = ('curso__nombre', 'descripcion', 'descripcion_otros', 'ciudad')


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = (
        'cedula', 'apellidos', 'nombres', 'edad',
        'correo', 'celular', 'ciudad', 'nivel_formacion',
    )
    search_fields = ('cedula', 'apellidos', 'nombres', 'correo')
    list_filter = ('nivel_formacion', 'ciudad')


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_matricula', 'estudiante', 'curso', 'jornada',
        'modalidad', 'valor_curso', 'valor_pagado', 'estado_pago',
        'registrado_por',
    )
    list_filter = ('modalidad', 'curso', 'fecha_matricula', 'talla_camiseta', 'registrado_por')
    search_fields = (
        'estudiante__cedula', 'estudiante__apellidos',
        'estudiante__nombres', 'curso__nombre',
    )
    autocomplete_fields = ('estudiante', 'curso', 'jornada')
    readonly_fields = ('registrado_por', 'creado', 'actualizado')


@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_inscripcion', 'nombre_persona', 'curso',
        'modalidad', 'tipo_registro', 'pago_abono', 'diferencia',
        'vendedora_nombre', 'factura_realizada',
    )
    list_filter = ('modalidad', 'tipo_registro', 'factura_realizada', 'curso', 'vendedora')
    search_fields = (
        'nombre_persona', 'celular',
        'fact_nombres', 'fact_apellidos', 'fact_cedula', 'fact_correo',
        'curso__nombre',
    )
    autocomplete_fields = ('curso',)
    readonly_fields = ('vendedora_nombre', 'creado', 'actualizado')
    fieldsets = (
        ('Datos del curso', {
            'fields': ('curso', 'modalidad', 'jornada', 'inicio_curso',
                       'fecha_inscripcion'),
        }),
        ('Datos del cliente', {
            'fields': ('nombre_persona', 'celular'),
        }),
        ('Pago y Registro', {
            'fields': ('tipo_registro', 'pago_abono', 'diferencia'),
        }),
        ('Vendedora', {
            'fields': ('vendedora', 'vendedora_nombre'),
        }),
        ('Factura', {
            'fields': ('factura_realizada', 'fact_nombres', 'fact_apellidos',
                       'fact_cedula', 'fact_correo'),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('creado', 'actualizado'),
        }),
    )


@admin.register(PersonaExterna)
class PersonaExternaAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'apellidos', 'nombres', 'celular', 'correo', 'ciudad', 'creado')
    search_fields = ('cedula', 'apellidos', 'nombres', 'correo', 'celular')
    list_filter = ('ciudad',)
    readonly_fields = ('creado', 'actualizado')


@admin.register(Adicional)
class AdicionalAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 'tipo_adicional', 'persona_nombre_admin',
        'curso', 'modalidad', 'valor', 'metodo_pago', 'registrado_por',
    )
    list_filter = ('tipo_adicional', 'modalidad', 'metodo_pago', 'fecha', 'registrado_por')
    search_fields = (
        'estudiante__cedula', 'estudiante__apellidos', 'estudiante__nombres',
        'persona_externa__cedula', 'persona_externa__apellidos', 'persona_externa__nombres',
        'curso__nombre', 'observaciones',
    )
    autocomplete_fields = ('estudiante', 'persona_externa', 'curso', 'matricula_origen')
    readonly_fields = ('creado', 'actualizado', 'registrado_por')
    fieldsets = (
        ('Tipo', {
            'fields': ('tipo_adicional',),
        }),
        ('Persona', {
            'fields': ('estudiante', 'persona_externa'),
            'description': 'Llenar UNO de los dos: estudiante (interno) o persona_externa.',
        }),
        ('Curso (para certificados / examen supletorio)', {
            'fields': ('curso', 'modalidad'),
        }),
        ('Camisa', {
            'fields': ('talla_camiseta',),
        }),
        ('Examen Supletorio', {
            'fields': ('matricula_origen', 'numero_modulo'),
        }),
        ('Cobro', {
            'fields': ('fecha', 'valor', 'metodo_pago', 'observaciones'),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('registrado_por', 'creado', 'actualizado'),
        }),
    )

    def persona_nombre_admin(self, obj):
        return obj.persona_nombre
    persona_nombre_admin.short_description = 'Persona'


@admin.register(RecuperacionPendiente)
class RecuperacionPendienteAdmin(admin.ModelAdmin):
    list_display = (
        'matricula', 'numero_modulo', 'fecha_marcada',
        'saldo_pendiente_al_marcar', 'pagada', 'fecha_recuperacion',
        'creado',
    )
    list_filter = ('pagada', 'numero_modulo', 'fecha_marcada')
    search_fields = (
        'matricula__estudiante__cedula',
        'matricula__estudiante__apellidos',
        'matricula__estudiante__nombres',
        'matricula__curso__nombre',
    )
    autocomplete_fields = ('matricula',)
    readonly_fields = ('creado', 'actualizado')
    date_hierarchy = 'fecha_marcada'
    fieldsets = (
        ('Datos de la clase a recuperar', {
            'fields': ('matricula', 'numero_modulo', 'fecha_marcada',
                       'saldo_pendiente_al_marcar'),
        }),
        ('Estado del cobro', {
            'fields': ('pagada', 'fecha_recuperacion', 'abono'),
        }),
        ('Notas', {
            'fields': ('observaciones',),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('creado', 'actualizado'),
        }),
    )


@admin.register(AssistantQueryLog)
class AssistantQueryLogAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'path', 'message_short')
    search_fields = ('message', 'reply', 'path', 'user__username')
    readonly_fields = ('user', 'path', 'message', 'reply', 'metadata', 'created')

    def message_short(self, obj):
        return (obj.message[:80] + '...') if len(obj.message) > 80 else obj.message
    message_short.short_description = 'Mensaje'

# ─────────────────────────────────────────────────────────
# Cierre de Curso (historial archivado)
# ─────────────────────────────────────────────────────────

class AbonoArchivadoInline(admin.TabularInline):
    model = AbonoArchivado
    extra = 0
    can_delete = False
    fields = ('fecha', 'numero_recibo', 'monto', 'tipo_pago_label',
              'metodo_label', 'banco_label', 'numero_modulo', 'cuenta_para_saldo')
    readonly_fields = fields
    verbose_name_plural = 'Abonos archivados (snapshot)'


@admin.register(CierreCurso)
class CierreCursoAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_cierre', 'curso_nombre', 'jornada_descripcion',
        'alcance', 'total_matriculas', 'total_facturado',
        'total_cobrado', 'cerrado_por',
    )
    list_filter = ('alcance', 'jornada_modalidad', 'fecha_cierre', 'cerrado_por')
    search_fields = ('curso_nombre', 'jornada_descripcion', 'ciclo_etiqueta', 'jornada_sede')
    readonly_fields = (
        'fecha_cierre', 'cerrado_por',
        'total_matriculas', 'total_facturado', 'total_cobrado', 'total_pendiente',
        'conteo_pagado', 'conteo_parcial', 'conteo_pendiente', 'conteo_retiro',
    )
    fieldsets = (
        ('Identidad', {
            'fields': ('curso', 'curso_nombre', 'curso_categoria',
                       'jornada', 'jornada_descripcion', 'jornada_modalidad',
                       'jornada_fecha_inicio', 'jornada_sede', 'alcance',
                       'ciclo_etiqueta', 'observaciones'),
        }),
        ('Totales (congelados)', {
            'fields': ('total_matriculas', 'total_facturado', 'total_cobrado', 'total_pendiente',
                       'conteo_pagado', 'conteo_parcial', 'conteo_pendiente', 'conteo_retiro'),
        }),
        ('Auditoría', {
            'fields': ('fecha_cierre', 'cerrado_por'),
        }),
    )


@admin.register(MatriculaArchivada)
class MatriculaArchivadaAdmin(admin.ModelAdmin):
    list_display = (
        'cedula', 'apellidos', 'nombres', 'curso_nombre',
        'jornada_descripcion', 'modalidad', 'valor_neto',
        'valor_pagado', 'estado_pago', 'cierre',
    )
    list_filter = ('estado_pago', 'modalidad', 'cierre__curso_nombre')
    search_fields = ('cedula', 'apellidos', 'nombres', 'correo', 'celular',
                     'curso_nombre', 'jornada_descripcion')
    readonly_fields = [f.name for f in MatriculaArchivada._meta.fields]
    inlines = [AbonoArchivadoInline]
    list_select_related = ('cierre',)


@admin.register(AbonoArchivado)
class AbonoArchivadoAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 'numero_recibo', 'monto', 'tipo_pago_label',
        'metodo_label', 'matricula_archivada', 'cierre',
    )
    list_filter = ('tipo_pago', 'metodo', 'fecha')
    search_fields = (
        'numero_recibo',
        'matricula_archivada__cedula',
        'matricula_archivada__apellidos',
        'matricula_archivada__curso_nombre',
    )
    readonly_fields = [f.name for f in AbonoArchivado._meta.fields]
    list_select_related = ('matricula_archivada', 'cierre')


@admin.register(EstudianteArchivado)
class EstudianteArchivadoAdmin(admin.ModelAdmin):
    list_display = (
        'cedula', 'apellidos', 'nombres', 'correo', 'celular',
        'ciudad', 'archivado_en', 'cierre',
    )
    list_filter = ('archivado_en', 'ciudad')
    search_fields = ('cedula', 'apellidos', 'nombres', 'correo', 'celular')
    readonly_fields = [f.name for f in EstudianteArchivado._meta.fields]
    list_select_related = ('cierre',)


@admin.register(AdicionalArchivado)
class AdicionalArchivadoAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 'tipo_adicional_label', 'persona_nombre', 'curso_nombre',
        'modalidad', 'valor', 'metodo_pago_label', 'archivado_en', 'cierre',
    )
    list_filter = ('tipo_adicional', 'modalidad', 'archivado_en')
    search_fields = ('persona_cedula', 'persona_nombre', 'persona_celular', 'curso_nombre', 'numero_recibo')
    readonly_fields = [f.name for f in AdicionalArchivado._meta.fields]
    list_select_related = ('cierre',)



@admin.register(CierreAdministrativo)
class CierreAdministrativoAdmin(admin.ModelAdmin):
    list_display = (
        'encabezado', 'anio', 'mes', 'ingreso_total', 'egreso_total',
        'balance_neto', 'fecha_cierre', 'cerrado_por',
    )
    list_filter = ('anio', 'mes', 'fecha_cierre')
    search_fields = ('etiqueta', 'observaciones')
    readonly_fields = ('fecha_cierre', 'cerrado_por')
