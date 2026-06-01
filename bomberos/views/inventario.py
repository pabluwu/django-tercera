from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone

from ..models import Sala, Item, LogInventario, AccionLogChoices
from ..serializers.inventario import (
    SalaSerializer,
    SalaCreateUpdateSerializer,
    ItemSerializer,
    ItemCreateUpdateSerializer,
    TransferenciaSerializer,
    LogInventarioSerializer,
)


def get_motivo_from_request(request):
    """Extrae el campo 'motivo' del body del request."""
    if request and hasattr(request, 'data'):
        return request.data.get('motivo', '')
    return ''


def crear_log(usuario, accion, motivo, sala_afectada=None, item_afectado=None):
    """Función helper para crear registros de LogInventario."""
    return LogInventario.objects.create(
        usuario=usuario,
        accion=accion,
        motivo=motivo,
        sala_afectada=sala_afectada,
        item_afectado=item_afectado,
    )


class SalaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Sala.
    
    Proporciona endpoints CRUD con logging de todas las operaciones.
    Implementa soft delete (cambia is_active a False en lugar de eliminar).
    """
    permission_classes = [IsAuthenticated]
    queryset = Sala.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SalaCreateUpdateSerializer
        return SalaSerializer

    def perform_create(self, serializer):
        """Crea una Sala y registra la acción en LogInventario."""
        motivo = get_motivo_from_request(self.request)
        sala = serializer.save()
        crear_log(
            usuario=self.request.user,
            accion=AccionLogChoices.CREATE,
            motivo=motivo,
            sala_afectada=sala,
        )

    def perform_update(self, serializer):
        """Actualiza una Sala y registra la acción en LogInventario."""
        motivo = get_motivo_from_request(self.request)
        sala = serializer.save()
        crear_log(
            usuario=self.request.user,
            accion=AccionLogChoices.UPDATE,
            motivo=motivo,
            sala_afectada=sala,
        )

    def perform_destroy(self, instance):
        """Soft delete: cambia is_active a False y registra la acción."""
        motivo = get_motivo_from_request(self.request)
        # Guardamos el nombre antes de hacer el soft delete
        sala_nombre = instance.nombre
        # Ejecutamos el soft delete (el método delete del modelo cambia is_active a False)
        instance.delete()
        # Buscamos la sala para loguear (podría haber sido marcada como inactiva)
        sala = Sala.objects.filter(nombre=sala_nombre, is_active=False).first()
        crear_log(
            usuario=self.request.user,
            accion=AccionLogChoices.DELETE,
            motivo=motivo,
            sala_afectada=sala,
        )

    @action(detail=True, methods=['get'], url_path='items')
    def list_items(self, request, pk=None):
        """
        Lista todos los items de una sala específica.
        
        GET /api/inventario/salas/{id}/items/
        """
        sala = self.get_object()
        items = sala.items.filter(is_active=True)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Item.
    
    Proporciona endpoints CRUD con logging de todas las operaciones.
    Implementa soft delete y la acción especial 'transferir'.
    """
    permission_classes = [IsAuthenticated]
    queryset = Item.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ItemCreateUpdateSerializer
        return ItemSerializer

    def get_queryset(self):
        """Permite filtrar items por sala usando el parámetro 'sala'."""
        queryset = super().get_queryset()
        sala_id = self.request.query_params.get('sala')
        if sala_id:
            queryset = queryset.filter(sala_id=sala_id)
        return queryset

    def perform_create(self, serializer):
        """Crea un Item y registra la acción en LogInventario."""
        motivo = get_motivo_from_request(self.request)
        item = serializer.save()
        crear_log(
            usuario=self.request.user,
            accion=AccionLogChoices.CREATE,
            motivo=motivo,
            sala_afectada=item.sala,
            item_afectado=item,
        )

    def perform_update(self, serializer):
        """Actualiza un Item y registra la acción en LogInventario."""
        motivo = get_motivo_from_request(self.request)
        item = serializer.save()
        crear_log(
            usuario=self.request.user,
            accion=AccionLogChoices.UPDATE,
            motivo=motivo,
            sala_afectada=item.sala,
            item_afectado=item,
        )

    def perform_destroy(self, instance):
        """Soft delete: cambia is_active a False y registra la acción."""
        motivo = get_motivo_from_request(self.request)
        sala = instance.sala
        # Ejecutamos el soft delete
        instance.delete()
        # Buscamos el item para loguear
        item = Item.objects.filter(
            nombre=instance.nombre,
            sala=sala,
            is_active=False
        ).first()
        crear_log(
            usuario=self.request.user,
            accion=AccionLogChoices.DELETE,
            motivo=motivo,
            sala_afectada=sala,
            item_afectado=item,
        )

    @action(detail=True, methods=['post'], url_path='transferir')
    def transferir(self, request, pk=None):
        """
        Acción especial para transferir un item a otra sala.
        
        Payload esperado:
        {
            "nueva_sala_id": 2,
            "motivo": "Reorganización de equipos"
        }
        """
        item = self.get_object()
        
        serializer = TransferenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        nueva_sala_id = serializer.validated_data['nueva_sala_id']
        motivo = serializer.validated_data['motivo']
        
        # Obtenemos la nueva sala
        nueva_sala = Sala.objects.get(pk=nueva_sala_id)
        sala_anterior = item.sala
        
        # Actualizamos la sala del item
        item.sala = nueva_sala
        item.save()
        
        # Creamos el log de transferencia
        crear_log(
            usuario=request.user,
            accion=AccionLogChoices.TRANSFER,
            motivo=f"Transferido desde '{sala_anterior.nombre}' a '{nueva_sala.nombre}'. Motivo: {motivo}",
            sala_afectada=nueva_sala,
            item_afectado=item,
        )
        
        # Retornamos el item actualizado
        item_serializer = ItemSerializer(item)
        return Response(item_serializer.data, status=status.HTTP_200_OK)


class LogInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para LogInventario.
    
    Permite visualizar el historial de todas las operaciones del inventario.
    """
    permission_classes = [IsAuthenticated]
    queryset = LogInventario.objects.all()
    serializer_class = LogInventarioSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por parámetros query opcionales
        usuario_id = self.request.query_params.get('usuario')
        accion = self.request.query_params.get('accion')
        sala_id = self.request.query_params.get('sala')
        item_id = self.request.query_params.get('item')
        
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        if accion:
            queryset = queryset.filter(accion=accion)
        if sala_id:
            queryset = queryset.filter(sala_afectada_id=sala_id)
        if item_id:
            queryset = queryset.filter(item_afectado_id=item_id)
            
        return queryset
