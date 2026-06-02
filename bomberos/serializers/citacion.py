from rest_framework import serializers
from ..models import Citacion
from .user import UserSerializer

class CitacionSerializer(serializers.ModelSerializer):
    autor_info = UserSerializer(source='autor', read_only=True)

    class Meta:
        model = Citacion
        fields = ['id', 'nombre', 'descripcion', 'fecha', 'lugar', 'tenida', 'responsable', 'autor', 'autor_info']
        read_only_fields = ['autor_info']

class CitacionConLicenciasSerializer(serializers.ModelSerializer):
    autor_info = UserSerializer(source='autor', read_only=True)
    num_licencias = serializers.IntegerField(read_only=True)

    class Meta:
        model = Citacion
        fields = ['id', 'nombre', 'descripcion', 'fecha', 'lugar', 'tenida', 'responsable', 'autor', 'autor_info', 'num_licencias']
        read_only_fields = ['autor_info', 'num_licencias']
