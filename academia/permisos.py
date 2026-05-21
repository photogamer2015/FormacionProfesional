"""
Helpers de permisos basados en grupos de Django.

Roles:
- Administrador: acceso total (CRUD de cursos, jornadas, categorías, matrículas).
- Asesor: CRUD completo sobre matrículas. En jornadas se respetan los permisos
  asignados desde el admin de Django.

Para crear los grupos: `python manage.py setup_roles`
Luego, en el panel admin (/admin/), asigna usuarios al grupo correspondiente.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


GRUPO_ADMIN = 'Administradores'
GRUPO_ASESOR = 'Asesores'


def es_admin(user):
    """¿Es superusuario o pertenece al grupo Administradores?"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=GRUPO_ADMIN).exists()


def es_asesor(user):
    """¿Pertenece al grupo Asesores? (los admin NO se cuentan como asesores)"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=GRUPO_ASESOR).exists()


def puede_gestionar_matriculas(user):
    """Admin o asesor: ambos pueden registrar/editar matrículas."""
    return es_admin(user) or es_asesor(user)


def puede_editar_cursos(user):
    """Compatibilidad: cualquier permiso de Curso/Categoría habilita controles."""
    return (
        puede_agregar_cursos(user)
        or puede_cambiar_cursos(user)
        or puede_eliminar_cursos(user)
        or puede_agregar_categorias(user)
        or puede_eliminar_categorias(user)
    )


def puede_agregar_cursos(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.add_curso')
    )


def puede_cambiar_cursos(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.change_curso')
    )


def puede_eliminar_cursos(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.delete_curso')
    )


def puede_agregar_categorias(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.add_categoria')
    )


def puede_eliminar_categorias(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.delete_categoria')
    )


def puede_agregar_jornadas(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.add_jornadacurso')
    )


def puede_editar_jornadas(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.change_jornadacurso')
    )


def puede_eliminar_jornadas(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.delete_jornadacurso')
    )


def puede_ver_jornadas(user):
    return es_admin(user) or (
        user.is_authenticated and user.has_perm('academia.view_jornadacurso')
    )


def puede_gestionar_jornadas(user):
    """Permite entrar al panel de jornadas si tiene cualquier permiso de Jornada."""
    return (
        puede_ver_jornadas(user)
        or puede_agregar_jornadas(user)
        or puede_editar_jornadas(user)
        or puede_eliminar_jornadas(user)
    )


# ─────────────────────────────────────────────────────────
# Decoradores
# ─────────────────────────────────────────────────────────

def admin_requerido(view_func):
    """
    Decorador que exige rol Administrador.
    Si no lo es, redirige a 'bienvenida' con un mensaje de error.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not es_admin(request.user):
            messages.error(
                request,
                'No tienes permiso para realizar esta acción. '
                'Solo los administradores pueden modificar cursos, jornadas o categorías.'
            )
            return redirect('academia:bienvenida')
        return view_func(request, *args, **kwargs)
    return _wrapped


def matricula_requerida(view_func):
    """
    Decorador para vistas de matrícula: requiere admin O asesor.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not puede_gestionar_matriculas(request.user):
            messages.error(
                request,
                'No tienes permiso para gestionar matrículas. '
                'Pide a un administrador que te asigne al grupo "Asesores".'
            )
            return redirect('academia:bienvenida')
        return view_func(request, *args, **kwargs)
    return _wrapped


def jornadas_requeridas(view_func):
    """
    Permite abrir el panel de jornadas si el usuario tiene al menos un permiso
    real de Jornada en Django Admin.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not puede_gestionar_jornadas(request.user):
            messages.error(
                request,
                'No tienes permiso para gestionar jornadas. '
                'Pide que te asignen permisos de ver, agregar, cambiar o eliminar Jornada.'
            )
            return redirect('academia:bienvenida')
        return view_func(request, *args, **kwargs)
    return _wrapped


def permiso_jornada_requerido(permiso):
    """
    Exige un permiso específico del modelo JornadaCurso, respetando también
    superusuarios y el grupo Administradores.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not (es_admin(request.user) or request.user.has_perm(permiso)):
                messages.error(request, 'No tienes permiso para realizar esa acción en jornadas.')
                return redirect('academia:bienvenida')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def permiso_requerido(permiso, mensaje='No tienes permiso para realizar esta acción.'):
    """Exige un permiso de Django Admin, respetando también Administradores."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not (es_admin(request.user) or request.user.has_perm(permiso)):
                messages.error(request, mensaje)
                return redirect('academia:bienvenida')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
