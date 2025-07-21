from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType
from bomberos.models import Citacion, ListaAsistencia
from ..serializers.citacion import CitacionSerializer
from rest_framework import viewsets, permissions
from django.utils.dateparse import parse_datetime

class CitacionViewSet(viewsets.ModelViewSet):
    queryset = Citacion.objects.all()
    serializer_class = CitacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')

        if fecha_desde:
            queryset = queryset.filter(fecha__gte=parse_datetime(fecha_desde))
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=parse_datetime(fecha_hasta))

        return queryset

    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        """Citaciones pasadas sin lista de asistencia asociada"""
        citacion_type = ContentType.objects.get_for_model(Citacion)
        citaciones_con_lista = ListaAsistencia.objects.filter(
            content_type=citacion_type
        ).values_list('object_id', flat=True)

        citaciones_disponibles = Citacion.objects.filter(
            fecha__lt=now()
        ).exclude(id__in=citaciones_con_lista)

        serializer = self.get_serializer(citaciones_disponibles, many=True)
        return Response(serializer.data)
