from rest_framework import serializers
from django.utils import timezone
from ..models import ExcepcionAsistencia, TipoExcepcionChoices
from .user import UserSerializer


class ExcepcionAsistenciaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo ExcepcionAsistencia."""

    autor_username = serializers.CharField(source='autor.username', read_only=True)
    bombero = UserSerializer(source='usuario', read_only=True)
    is_activa = serializers.SerializerMethodField()

    class Meta:
        model = ExcepcionAsistencia
        fields = [
            'id', 'tipo_excepcion', 'usuario', 'bombero', 'fecha_inicio', 'fecha_fin', 'motivo',
            'autor', 'autor_username', 'is_activa', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_activa(self, obj):
        """Retorna True si la fecha_fin es mayor a la fecha actual."""
        return obj.fecha_fin > timezone.now()


class ExcepcionAsistenciaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar ExcepcionAsistencia."""

    class Meta:
        model = ExcepcionAsistencia
        fields = [
            'id', 'tipo_excepcion', 'usuario', 'fecha_inicio', 'fecha_fin', 'motivo',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TipoExcepcionSerializer(serializers.Serializer):
    """Serializer para exponer las opciones de TipoExcepcion."""
    value = serializers.CharField()
    label = serializers.CharField()
