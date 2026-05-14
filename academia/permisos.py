"""
Helpers de permisos basados en grupos de Django.

Roles:
- Administrador: acceso total (CRUD de cursos, jornadas, categorías, matrículas).
- Asesor: solo lectura de cursos/jornadas. CRUD completo sobre matrículas.

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
    """Solo admin puede crear/editar/eliminar cursos, jornadas, categorías."""
    return es_admin(user)


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
