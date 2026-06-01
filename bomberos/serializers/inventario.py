from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Sala, Item, LogInventario


class MotivoRequiredMixin:
    """Mixin que valida que el campo 'motivo' esté presente en POST, PUT, PATCH."""

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            motivo = attrs.get('motivo')
            if not motivo:
                # El motivo debe venir en los datos iniciales
                if hasattr(self, 'initial_data') and 'motivo' in self.initial_data:
                    attrs['motivo'] = self.initial_data['motivo']
                else:
                    raise serializers.ValidationError({
                        'motivo': 'El campo "motivo" es obligatorio para esta operación.'
                    })
        return attrs


class SalaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Sala."""

    class Meta:
        model = Sala
        fields = ['id', 'nombre', 'descripcion', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SalaCreateUpdateSerializer(MotivoRequiredMixin, serializers.ModelSerializer):
    """Serializer para crear/actualizar Salas con validación de motivo."""
    motivo = serializers.CharField(required=True, min_length=1, write_only=True)

    class Meta:
        model = Sala
        fields = ['id', 'nombre', 'descripcion', 'is_active', 'motivo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Remover 'motivo' antes de pasar al modelo
        validated_data.pop('motivo', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Remover 'motivo' antes de pasar al modelo
        validated_data.pop('motivo', None)
        return super().update(instance, validated_data)


class ItemSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Item."""

    sala_nombre = serializers.CharField(source='sala.nombre', read_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'nombre', 'descripcion', 'cantidad', 'ubicacion_especifica',
            'is_active', 'sala', 'sala_nombre', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItemCreateUpdateSerializer(MotivoRequiredMixin, serializers.ModelSerializer):
    """Serializer para crear/actualizar Items con validación de motivo."""
    motivo = serializers.CharField(required=True, min_length=1, write_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'nombre', 'descripcion', 'cantidad', 'ubicacion_especifica',
            'is_active', 'sala', 'motivo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Remover 'motivo' antes de pasar al modelo
        validated_data.pop('motivo', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Remover 'motivo' antes de pasar al modelo
        validated_data.pop('motivo', None)
        return super().update(instance, validated_data)


class TransferenciaSerializer(serializers.Serializer):
    """Serializer para la acción de transferir items entre salas."""
    nueva_sala_id = serializers.IntegerField()
    motivo = serializers.CharField(required=True, min_length=1)

    def validate_nueva_sala_id(self, value):
        try:
            Sala.objects.get(pk=value, is_active=True)
        except Sala.DoesNotExist:
            raise serializers.ValidationError("La sala seleccionada no existe o está inactiva.")
        return value


class LogInventarioSerializer(serializers.ModelSerializer):
    """Serializer para el modelo LogInventario."""

    usuario_username = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)
    sala_nombre = serializers.CharField(source='sala_afectada.nombre', read_only=True, allow_null=True)
    item_nombre = serializers.CharField(source='item_afectado.nombre', read_only=True, allow_null=True)

    class Meta:
        model = LogInventario
        fields = [
            'id', 'usuario', 'usuario_username', 'accion', 'motivo', 'fecha',
            'sala_afectada', 'sala_nombre', 'item_afectado', 'item_nombre'
        ]
        read_only_fields = ['id', 'usuario', 'fecha']
