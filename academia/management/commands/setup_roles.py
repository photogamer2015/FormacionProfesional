"""
Comando: python manage.py setup_roles

Crea (o actualiza) los grupos "Administradores" y "Asesores" con los
permisos apropiados sobre los modelos del sistema.

- Administradores: todos los permisos sobre todos los modelos.
- Asesores: pueden REGISTRAR matrículas, abonos, comprobantes y
            adicionales, pero NO eliminar nada. Solo lectura sobre
            cursos/categorías/jornadas. No tienen acceso a egresos,
            categorías de egreso ni al panel administrativo.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from academia.models import (
    Categoria, Curso, JornadaCurso, Estudiante, Matricula,
    Abono, Comprobante, RecuperacionPendiente, Adicional, PersonaExterna,
    CategoriaEgreso, Egreso, AlertaPagoRevisada,
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
        TODOS_MODELOS = [
            Categoria, Curso, JornadaCurso, Estudiante, Matricula,
            Abono, Comprobante, RecuperacionPendiente, Adicional,
            PersonaExterna, CategoriaEgreso, Egreso, AlertaPagoRevisada,
        ]

        # ─── Grupo Administradores ──────────────────────────────
        # Acceso TOTAL a todos los modelos (add, change, view, delete).
        admin_group, created_admin = Group.objects.get_or_create(name=GRUPO_ADMIN)
        admin_perms = []
        for model in TODOS_MODELOS:
            admin_perms += _perms_for(model, ['add', 'change', 'view', 'delete'])
        admin_group.permissions.set(admin_perms)
        self.stdout.write(self.style.SUCCESS(
            f'{"✓ Creado" if created_admin else "✓ Actualizado"} grupo "{GRUPO_ADMIN}" '
            f'con {len(admin_perms)} permisos (acceso total).'
        ))

        # ─── Grupo Asesores ─────────────────────────────────────
        # Pueden registrar matrículas, abonos, comprobantes, adicionales.
        # NO pueden eliminar nada. NO pueden tocar egresos ni categorías
        # de egreso. NO pueden modificar cursos/categorías/jornadas
        # (solo verlas, porque las necesitan para registrar matrículas).
        asesor_group, created_asesor = Group.objects.get_or_create(name=GRUPO_ASESOR)
        asesor_perms = []

        # Solo lectura sobre el catálogo del negocio
        for model in [Categoria, Curso, JornadaCurso]:
            asesor_perms += _perms_for(model, ['view'])

        # Pueden registrar/editar estudiantes (necesario para matricular)
        # pero NO eliminarlos
        asesor_perms += _perms_for(Estudiante, ['add', 'change', 'view'])

        # Operación principal: matrículas, abonos, comprobantes, adicionales
        # pueden CREAR y EDITAR, pero NO eliminar
        for model in [Matricula, Abono, Comprobante, Adicional, PersonaExterna]:
            asesor_perms += _perms_for(model, ['add', 'change', 'view'])

        # Clases en recuperación: pueden marcar y cobrar (add/change/view)
        asesor_perms += _perms_for(RecuperacionPendiente, ['add', 'change', 'view'])

        # NOTA: NO se da NINGÚN permiso sobre Egreso, CategoriaEgreso ni
        # AlertaPagoRevisada — son del panel administrativo (solo admin).

        asesor_group.permissions.set(asesor_perms)
        self.stdout.write(self.style.SUCCESS(
            f'{"✓ Creado" if created_asesor else "✓ Actualizado"} grupo "{GRUPO_ASESOR}" '
            f'con {len(asesor_perms)} permisos (sin eliminar, sin egresos, sin panel admin).'
        ))

        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            '➜ Para asignar usuarios a un grupo, entra a /admin/auth/user/, '
            'edita el usuario y agrégalo al grupo correspondiente.'
        ))
        self.stdout.write(self.style.WARNING(
            '➜ Recuerda marcar "Es staff" (is_staff=True) en los usuarios '
            'que necesiten entrar al panel /admin/. Sin eso, no podrán '
            'ingresar aunque tengan permisos asignados.'
        ))