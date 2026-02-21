from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from bomberos.models import Licencia
from ..serializers.licencia import LicenciaSerializer

class LicenciaViewSet(viewsets.ModelViewSet):
    queryset = Licencia.objects.all()
    serializer_class = LicenciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        citacion = serializer.validated_data.get('citacion')
        if citacion and citacion.fecha:
            citacion_fecha = citacion.fecha
            if timezone.is_naive(citacion_fecha):
                citacion_fecha = timezone.make_aware(
                    citacion_fecha, timezone.get_current_timezone()
                )

            if citacion_fecha <= timezone.now() + timedelta(hours=24):
                raise ValidationError(
                    {"citacion": "No se puede crear la licencia si la citación es menor a 24 horas."}
                )

        serializer.save(autor=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        autor_id = self.request.query_params.get('autor')
        citacion_id = self.request.query_params.get('citacion')

        if autor_id:
            queryset = queryset.filter(autor_id=autor_id)
        if citacion_id:
            queryset = queryset.filter(citacion_id=citacion_id)

        return queryset
