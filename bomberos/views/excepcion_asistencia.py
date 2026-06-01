from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import ExcepcionAsistencia, TipoExcepcionChoices
from ..serializers.excepcion_asistencia import (
    ExcepcionAsistenciaSerializer,
    ExcepcionAsistenciaCreateUpdateSerializer,
    TipoExcepcionSerializer,
)


class ExcepcionAsistenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo ExcepcionAsistencia.
    
    Proporciona endpoints CRUD para gestionar excepciones de asistencia.
    """
    permission_classes = [IsAuthenticated]
    queryset = ExcepcionAsistencia.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ExcepcionAsistenciaCreateUpdateSerializer
        return ExcepcionAsistenciaSerializer

    def perform_create(self, serializer):
        """Asigna el usuario actual como autor."""
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        """Mantiene el autor original."""
        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete: cambia is_active a False."""
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get'], url_path='tipos')
    def tipos(self, request):
        """
        Endpoint para obtener las opciones de TipoExcepcion.
        
        GET /api/excepciones-asistencia/tipos/
        
        Retorna las opciones disponibles para rellenar dropdowns en el frontend.
        """
        tipos = [
            {'value': choice[0], 'label': choice[1]}
            for choice in TipoExcepcionChoices.choices
        ]
        serializer = TipoExcepcionSerializer(tipos, many=True)
        return Response(serializer.data)
