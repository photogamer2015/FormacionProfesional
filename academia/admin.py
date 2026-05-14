from django.contrib import admin
from .models import (
    Adicional, Categoria, Comprobante, Curso, JornadaCurso,
    Estudiante, Matricula, PersonaExterna, RecuperacionPendiente,
    AssistantQueryLog,
)


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
    fields = ('modalidad', 'descripcion', 'fecha_inicio', 'hora_inicio', 'hora_fin', 'ciudad', 'activo')


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
        'curso', 'modalidad', 'descripcion', 'fecha_inicio',
        'hora_inicio', 'hora_fin', 'ciudad', 'activo',
    )
    list_filter = ('modalidad', 'activo', 'ciudad', 'curso')
    search_fields = ('curso__nombre', 'descripcion', 'ciudad')


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