import os
import mimetypes
from django.http import FileResponse, Http404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ExpedienteSalud, Accidente, MovimientoAccidente
from ..serializers.salud import (
    ExpedienteSaludSerializer,
    AccidenteSerializer,
    MovimientoAccidenteSerializer,
)
from ..permissions import IsEncargadoSalud


class ExpedienteSaludViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los Expedientes de Salud por Bombero.
    Acceso restringido a Encargados de Salud.
    """
    queryset = ExpedienteSalud.objects.all()
    serializer_class = ExpedienteSaludSerializer
    permission_classes = [IsAuthenticated, IsEncargadoSalud]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['bombero', 'categoria']
    search_fields = ['bombero__nombres', 'bombero__apellido_paterno', 'observaciones']
    ordering_fields = ['fecha_documento', 'creado_en']
    ordering = ['-fecha_documento']

    @action(detail=True, methods=['get'], url_path='descargar')
    def descargar(self, request, pk=None):
        """
        Descarga segura del archivo adjunto al expediente de salud.
        """
        instance = self.get_object()
        if not instance.archivo:
            raise Http404("No hay archivo asociado a este expediente.")

        file_path = instance.archivo.path
        if not os.path.exists(file_path):
            raise Http404("El archivo físico no se encuentra en el servidor.")

        # Determinar tipo de contenido para la respuesta
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        response = FileResponse(open(file_path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response


class AccidenteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el Historial de Accidentes.
    Acceso restringido a Encargados de Salud.
    """
    queryset = Accidente.objects.all()
    serializer_class = AccidenteSerializer
    permission_classes = [IsAuthenticated, IsEncargadoSalud]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['bombero', 'estado', 'contexto']
    search_fields = ['bombero__nombres', 'bombero__apellido_paterno', 'descripcion']
    ordering_fields = ['fecha_hora', 'creado_en']
    ordering = ['-fecha_hora']


class MovimientoAccidenteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los Movimientos/Bitácora de cada Accidente.
    Acceso restringido a Encargados de Salud.
    """
    queryset = MovimientoAccidente.objects.all()
    serializer_class = MovimientoAccidenteSerializer
    permission_classes = [IsAuthenticated, IsEncargadoSalud]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['accidente']
    ordering_fields = ['fecha_hito', 'creado_en']
    ordering = ['-fecha_hito']

    @action(detail=True, methods=['get'], url_path='descargar')
    def descargar(self, request, pk=None):
        """
        Descarga segura del archivo adjunto al movimiento del accidente.
        """
        instance = self.get_object()
        if not instance.archivo:
            raise Http404("No hay archivo asociado a este movimiento.")

        file_path = instance.archivo.path
        if not os.path.exists(file_path):
            raise Http404("El archivo físico no se encuentra en el servidor.")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        response = FileResponse(open(file_path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
