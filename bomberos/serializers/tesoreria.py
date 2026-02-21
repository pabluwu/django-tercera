# serializers.py

from collections import OrderedDict
from rest_framework import serializers
from datetime import date
from ..models import ComprobanteTransferencia, ComprobanteTesorero, MesAnio
from .user import UserSerializer

class MesAnioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MesAnio
        fields = '__all__'

class ComprobanteTransferenciaSerializer(serializers.ModelSerializer):
    meses_pagados = serializers.PrimaryKeyRelatedField(
        queryset=MesAnio.objects.all(),
        many=True,
        write_only=True
    )
    meses_pagados_detalle = MesAnioSerializer(
        source='meses_pagados',
        many=True,
        read_only=True
    )
    bombero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ComprobanteTransferencia
        fields = [
            'id', 'archivo', 'fecha_envio',
            'meses_pagados', 'meses_pagados_detalle',
            'bombero', 'aprobado', 'observacion',
            'fecha_revision', 'revisado_por'
        ]
        read_only_fields = ['aprobado', 'revisado_por', 'fecha_revision', 'bombero']

    def get_bombero(self, obj):
        return {
            "id": obj.bombero.id,
            "nombre": obj.bombero.get_full_name() or obj.bombero.username,
            "email": obj.bombero.email,
        }

    def validate(self, data):
        if not data.get('archivo'):
            raise serializers.ValidationError({"archivo": "Este campo es obligatorio."})
        if not data.get('meses_pagados'):
            raise serializers.ValidationError({"meses_pagados": "Debes seleccionar al menos un mes."})
        return data
    

class CuotasAnualesSerializer(serializers.Serializer):
    anio = serializers.IntegerField()
    pagadas = serializers.IntegerField()
    pendientes = serializers.IntegerField()

    def to_representation(self, instance):
        """
        Ensure deterministic ordering of keys per item.
        """
        rep = super().to_representation(instance)
        return OrderedDict([
            ('anio', rep['anio']),
            ('pagadas', rep['pagadas']),
            ('pendientes', rep['pendientes']),
        ])


class BomberoCuotasSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = UserSerializer()
    rut = serializers.CharField(allow_blank=True, allow_null=True)
    fecha_ingreso = serializers.DateField(allow_null=True)
    telefono = serializers.IntegerField(allow_null=True)
    contacto = serializers.IntegerField(allow_null=True)
    imagen = serializers.CharField(allow_blank=True, allow_null=True)
    cuotas_por_anio = CuotasAnualesSerializer(many=True)
    total_pagadas = serializers.IntegerField()
    total_pendientes = serializers.IntegerField()
    isMoroso = serializers.IntegerField()

    class Meta:
        fields = (
            'id',
            'user',
            'rut',
            'fecha_ingreso',
            'telefono',
            'contacto',
            'imagen',
            'cuotas_por_anio',
            'total_pagadas',
            'total_pendientes',
            'isMoroso',
        )
    
class ComprobanteTesoreroSerializer(serializers.ModelSerializer):
    meses_pagados = serializers.PrimaryKeyRelatedField(queryset=MesAnio.objects.all(), many=True)

    class Meta:
        model = ComprobanteTesorero
        fields = '__all__'
        read_only_fields = ['tesorero']
    
    def validate(self, data):
        numero = data.get('numero_comprobante')
        fecha = data.get('fecha_emision') or date.today()

        if numero and fecha:
            anio = fecha.year
            if ComprobanteTesorero.objects.filter(
                numero_comprobante=numero,
                fecha_emision__year=anio
            ).exists():
                raise serializers.ValidationError({
                    'numero_comprobante': f'Ya existe un comprobante con ese número en el año {anio}.'
                })
        return data
