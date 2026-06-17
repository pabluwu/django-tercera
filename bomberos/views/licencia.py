from datetime import timedelta

from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from bomberos.models import Licencia, Citacion
from ..serializers.licencia import LicenciaSerializer
from ..serializers.citacion import CitacionConLicenciasSerializer
from ..utils import send_licencia_confirmation_email, send_licencia_status_email
from ..permissions import IsOficial

class LicenciaViewSet(viewsets.ModelViewSet):
    queryset = Licencia.objects.all()
    serializer_class = LicenciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsOficial])
    def aceptar(self, request, pk=None):
        licencia = self.get_object()
        licencia.estado = 'aceptada'
        licencia.save()
        send_licencia_status_email(licencia)
        return Response({"detail": "Licencia aceptada correctamente.", "estado": licencia.estado})

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsOficial])
    def rechazar(self, request, pk=None):
        licencia = self.get_object()
        licencia.estado = 'rechazada'
        licencia.save()
        send_licencia_status_email(licencia)
        return Response({"detail": "Licencia rechazada correctamente.", "estado": licencia.estado})

    def _auto_accept_past_licencias(self):
        # Encontrar todas las licencias que estén pendientes y cuya citación ya haya pasado su fecha y hora
        past_pending = Licencia.objects.filter(
            estado='pendiente',
            citacion__fecha__lt=timezone.now()
        )
        for licencia in past_pending:
            licencia.estado = 'aceptada'
            licencia.save()
            send_licencia_status_email(licencia)

    @action(detail=False, methods=['get'])
    def citaciones_con_licencias(self, request):
        """
        Devuelve todas las citaciones con la cantidad de licencias asociadas.
        """
        self._auto_accept_past_licencias()
        citaciones = Citacion.objects.annotate(num_licencias=Count('licencia')).order_by('-fecha')
        serializer = CitacionConLicenciasSerializer(citaciones, many=True)
        return Response(serializer.data)

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

        licencia = serializer.save(autor=self.request.user)
        send_licencia_confirmation_email(licencia)

    def get_queryset(self):
        self._auto_accept_past_licencias()
        queryset = super().get_queryset()
        autor_id = self.request.query_params.get('autor')
        citacion_id = self.request.query_params.get('citacion')

        if autor_id:
            queryset = queryset.filter(autor_id=autor_id)
        if citacion_id:
            queryset = queryset.filter(citacion_id=citacion_id)

        return queryset
