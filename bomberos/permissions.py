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
