import logging
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from bomberos.serializers.auth import (
    RutTokenObtainPairSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

logger = logging.getLogger(__name__)


class RutTokenObtainPairView(TokenObtainPairView):
    serializer_class = RutTokenObtainPairSerializer


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        profile = getattr(user, 'bombero', None)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_RESET_URL}?uid={uid}&token={token}"

        context = {
            'name': user.get_full_name() or user.username,
            'rut': getattr(profile, 'rut', ''),
            'email': user.email,
            'reset_link': reset_link,
        }
        try:
            subject = "Restablecer contraseña - Intranet Tercera Compañía"
            text_body = (
                f"Hola {context['name']},\n\n"
                f"Solicitaste restablecer tu contraseña de la Intranet de la Tercera Compañía.\n"
                f"RUT: {context['rut']}\n"
                f"Email: {context['email']}\n\n"
                f"Para continuar, abre este enlace: {reset_link}\n\n"
                "Si no solicitaste este cambio, puedes ignorar este mensaje."
            )
            html_body = render_to_string('emails/password_reset.html', context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_body, "text/html")
            email.send(fail_silently=False)
        except Exception as e:
            logger.exception("Error enviando correo de restablecimiento")
            return Response(
                {"detail": "No se pudo enviar el correo de restablecimiento.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Si el email existe, se envió un link para restablecer la contraseña."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        new_password = serializer.validated_password
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Contraseña actualizada correctamente."})
