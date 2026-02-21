from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..serializers.user import UserProfileSerializer, UserProfileUpdateSerializer


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    profile = getattr(user, 'bombero', None)

    if request.method == 'PATCH':
        if profile is None:
            return Response(
                {"detail": "No se encontró un perfil asociado al usuario."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user.refresh_from_db()
        profile.refresh_from_db()

    permisos = user.get_all_permissions()  # set de strings como 'app_label.codename'

    profile_data = None
    profile = getattr(user, 'bombero', None)
    if profile:
        profile_data = UserProfileSerializer(profile, context={'request': request}).data

    groups_data = [
        {
            "id": group.id,
            "name": group.name,
        }
        for group in user.groups.all()
    ]

    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "permissions": list(permisos),  # convertir set en lista
        "profile": profile_data,
        "groups": groups_data,
    })
