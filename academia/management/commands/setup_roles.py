"""
Comando: python manage.py setup_roles

Crea (o actualiza) los grupos "Administradores" y "Asesores" con los
permisos apropiados sobre los modelos del sistema.

- Administradores: todos los permisos sobre todos los modelos.
- Asesores: solo VIEW en Curso/Categoría/Jornada/Estudiante;
            ADD/CHANGE/VIEW/DELETE sobre Matricula.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from academia.models import (
    Categoria, Curso, JornadaCurso, Estudiante, Matricula,
)
from academia.permisos import GRUPO_ADMIN, GRUPO_ASESOR


def _perms_for(model, codenames):
    """Retorna los Permission de un modelo según codenames como ['add', 'view']."""
    ct = ContentType.objects.get_for_model(model)
    full = [f'{cn}_{model._meta.model_name}' for cn in codenames]
    return list(Permission.objects.filter(content_type=ct, codename__in=full))


class Command(BaseCommand):
    help = 'Crea los grupos Administradores y Asesores con sus permisos.'

    def handle(self, *args, **options):
        # ─── Grupo Administradores ──────────────────────────────
        admin_group, created_admin = Group.objects.get_or_create(name=GRUPO_ADMIN)
        admin_perms = []
        for model in [Categoria, Curso, JornadaCurso, Estudiante, Matricula]:
            admin_perms += _perms_for(model, ['add', 'change', 'view', 'delete'])
        admin_group.permissions.set(admin_perms)
        self.stdout.write(self.style.SUCCESS(
            f'{"✓ Creado" if created_admin else "✓ Actualizado"} grupo "{GRUPO_ADMIN}" '
            f'con {len(admin_perms)} permisos.'
        ))

        # ─── Grupo Asesores ─────────────────────────────────────
        asesor_group, created_asesor = Group.objects.get_or_create(name=GRUPO_ASESOR)
        asesor_perms = []
        # Solo lectura sobre cursos/categorías/jornadas
        for model in [Categoria, Curso, JornadaCurso]:
            asesor_perms += _perms_for(model, ['view'])
        # Lectura + creación + edición de estudiantes (necesario para registrar matrícula)
        asesor_perms += _perms_for(Estudiante, ['add', 'change', 'view'])
        # Full CRUD sobre matrículas
        asesor_perms += _perms_for(Matricula, ['add', 'change', 'view', 'delete'])
        asesor_group.permissions.set(asesor_perms)
        self.stdout.write(self.style.SUCCESS(
            f'{"✓ Creado" if created_asesor else "✓ Actualizado"} grupo "{GRUPO_ASESOR}" '
            f'con {len(asesor_perms)} permisos.'
        ))

        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            '➜ Para asignar usuarios a un grupo, entra a /admin/auth/user/, '
            'edita el usuario y agrégalo al grupo correspondiente.'
        ))
