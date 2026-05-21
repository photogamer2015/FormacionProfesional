"""
Context processor que expone los roles del usuario en TODOS los templates.

Uso en plantillas:
    {% if es_admin %}...{% endif %}
    {% if es_asesor %}...{% endif %}
    {% if puede_editar_cursos %}...{% endif %}
"""
from .permisos import (
    es_admin as _es_admin,
    es_asesor as _es_asesor,
    puede_editar_cursos as _puede_editar_cursos,
    puede_gestionar_matriculas as _puede_gestionar_matriculas,
)


def roles(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {
            'es_admin': False,
            'es_asesor': False,
            'puede_editar_cursos': False,
            'puede_gestionar_matriculas': False,
            'rol_actual': '',
        }

    es_a = _es_admin(user)
    es_s = _es_asesor(user)
    if es_a:
        rol_actual = 'Administrador'
    elif es_s:
        rol_actual = 'Asesor'
    else:
        rol_actual = 'Usuario'

    return {
        'es_admin': es_a,
        'es_asesor': es_s,
        'puede_editar_cursos': _puede_editar_cursos(user),
        'puede_gestionar_matriculas': _puede_gestionar_matriculas(user),
        'rol_actual': rol_actual,
    }


def feature_flags(request):
    """Expone flags de funcionalidad a todos los templates."""
    from .views import MATRICULA_ONLINE_HABILITADA
    return {
        'matricula_online_habilitada': MATRICULA_ONLINE_HABILITADA,
    }
