from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import UserProfile, ExpedienteSalud, Accidente, MovimientoAccidente

class UserProfileBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'cia', 'cargo']


class ExpedienteSaludSerializer(serializers.ModelSerializer):
    bombero_detalle = UserProfileBriefSerializer(source='bombero', read_only=True)
    creado_por_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExpedienteSalud
        fields = [
            'id', 'bombero', 'bombero_detalle', 'categoria', 'archivo',
            'fecha_documento', 'observaciones', 'creado_por', 'creado_por_name',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['creado_por', 'creado_en', 'actualizado_en']

    def get_creado_por_name(self, obj):
        if obj.creado_por:
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return "N/A"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['creado_por'] = request.user
        return super().create(validated_data)


class MovimientoAccidenteSerializer(serializers.ModelSerializer):
    creado_por_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MovimientoAccidente
        fields = [
            'id', 'accidente', 'fecha_hito', 'tipo_accion', 'detalle', 'archivo',
            'creado_por', 'creado_por_name', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['creado_por', 'creado_en', 'actualizado_en']

    def get_creado_por_name(self, obj):
        if obj.creado_por:
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return "N/A"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['creado_por'] = request.user
        return super().create(validated_data)


class AccidenteSerializer(serializers.ModelSerializer):
    bombero_detalle = UserProfileBriefSerializer(source='bombero', read_only=True)
    creado_por_name = serializers.SerializerMethodField(read_only=True)
    movimientos = MovimientoAccidenteSerializer(many=True, read_only=True)

    class Meta:
        model = Accidente
        fields = [
            'id', 'bombero', 'bombero_detalle', 'fecha_hora', 'descripcion',
            'contexto', 'estado', 'movimientos', 'creado_por', 'creado_por_name',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['creado_por', 'creado_en', 'actualizado_en']

    def get_creado_por_name(self, obj):
        if obj.creado_por:
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return "N/A"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['creado_por'] = request.user
        return super().create(validated_data)
