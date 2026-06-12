from typing import Iterable

from rest_framework.permissions import BasePermission


class GroupRequired(BasePermission):
    """
    Permiso que restringe el acceso a usuarios autenticados que pertenezcan
    a al menos uno de los grupos indicados en ``required_groups``.

    Uso:
        class MiVista(viewsets.ViewSet):
            permission_classes = [IsAuthenticated, groups_required('tesoreros')]
    """

    required_groups: Iterable[str] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if not self.required_groups:
            return True

        user_groups = set(user.groups.values_list('name', flat=True))
        return bool(user_groups.intersection(self.required_groups))


def groups_required(*group_names: str) -> BasePermission:
    """
    Devuelve una clase de permiso que acepta la solicitud únicamente si
    el usuario pertenece a alguno de los grupos indicados.

    Ejemplo:

        class TesoreriaViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, groups_required('tesoreros')]

    Se pueden indicar varios grupos, en cuyo caso basta que el usuario
    pertenezca a uno de ellos para conceder acceso.
    """

    class _GroupPermission(GroupRequired):
        required_groups = group_names

    return _GroupPermission


class ModuleRequired(BasePermission):
    """
    Permiso que restringe el acceso a usuarios cuyo Tenant no tiene activo
    el módulo solicitado (modulo_clave).
    """

    def __init__(self, modulo_clave: str):
        self.modulo_clave = modulo_clave

    def has_permission(self, request, view) -> bool:
        from rest_framework.exceptions import PermissionDenied
        from .models import TenantModulo

        user = request.user
        if not user or not user.is_authenticated:
            return False

        profile = getattr(user, 'bombero', None)
        if not profile:
            raise PermissionDenied("El usuario no tiene un perfil asociado.")

        tenant = profile.tenant
        if not tenant:
            raise PermissionDenied("El usuario no pertenece a ninguna organización.")

        # Verificar si el módulo está contratado y activo
        modulo_activo = TenantModulo.objects.filter(
            tenant=tenant,
            modulo__clave=self.modulo_clave,
            is_active=True
        ).exists()

        if not modulo_activo:
            raise PermissionDenied(f"El módulo '{self.modulo_clave}' no está habilitado para esta organización.")

        return True


def module_required(modulo_clave: str) -> BasePermission:
    """
    Devuelve una clase de permiso que restringe el acceso según el módulo.
    """
    class _ModulePermission(ModuleRequired):
        def __init__(self):
            super().__init__(modulo_clave)

    return _ModulePermission


class IsOficial(BasePermission):
    """
    Permiso que restringe el acceso únicamente a oficiales de la compañía
    (Director, Capitán, Tenientes, Secretario, Tesorero, Ayudante, Intendente).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Grupos de oficiales conocidos (normalizados en minúsculas)
        oficiales_groups = {
            'director', 'capitán', 'capitan', 'secretario', 'tesorero',
            'teniente 1°', 'teniente 2°', 'teniente 3°', 'teniente primero',
            'teniente segundo', 'teniente tercero', 'ayudante', 'intendente'
        }
        user_groups = {g.lower() for g in user.groups.values_list('name', flat=True)}

        # Comprobar intersección de grupos
        if oficiales_groups.intersection(user_groups):
            return True

        # También verificar según el cargo registrado en el perfil
        profile = getattr(user, 'bombero', None)
        if profile and profile.cargo:
            cargo = profile.cargo.lower()
            if any(o in cargo for o in ['director', 'capitán', 'capitan', 'secretario', 'tesorero', 'teniente', 'ayudante', 'intendente']):
                return True

        return False


