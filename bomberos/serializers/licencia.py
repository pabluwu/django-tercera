from rest_framework import serializers
from ..models import Citacion, Licencia
from .user import UserSerializer
from .citacion import CitacionSerializer

class LicenciaSerializer(serializers.ModelSerializer):
    autor_info = UserSerializer(source='autor', read_only=True)
    citacion = serializers.PrimaryKeyRelatedField(queryset=Citacion.objects.all())
    citacion_info = CitacionSerializer(source='citacion', read_only=True)

    class Meta:
        model = Licencia
        fields = '__all__'
        read_only_fields = ['autor_info', 'citacion_info']