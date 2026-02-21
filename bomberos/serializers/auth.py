from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import PasswordField
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from bomberos.models import UserProfile


class RutTokenObtainPairSerializer(serializers.Serializer):
    rut = serializers.CharField()
    password = PasswordField()

    def validate(self, attrs):
        rut = attrs.get('rut')
        password = attrs.get('password')

        try:
            profile = UserProfile.objects.select_related('user').get(rut=rut)
        except UserProfile.DoesNotExist:
            raise AuthenticationFailed('RUT o contraseña incorrectos.', code='authorization')

        user = profile.user
        if not user.check_password(password):
            raise AuthenticationFailed('RUT o contraseña incorrectos.', code='authorization')
        if not user.is_active:
            raise AuthenticationFailed('Usuario inactivo.', code='authorization')

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    rut = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs):
        rut = attrs.get('rut', '').strip()
        if not rut:
            raise serializers.ValidationError("Debes enviar el rut.")

        try:
            profile = UserProfile.objects.select_related('user').get(rut=rut)
            user = profile.user
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("No se encontró un usuario con ese rut.")

        if not user.email:
            raise serializers.ValidationError("El usuario no tiene email registrado.")

        self.user = user
        self.profile = profile
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        uid = attrs.get('uid')
        token = attrs.get('token')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError("Las contraseñas no coinciden.")

        User = get_user_model()
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            raise serializers.ValidationError("Enlace inválido.")

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            raise serializers.ValidationError("Enlace inválido o expirado.")

        self.user = user
        self.validated_password = new_password
        return attrs
