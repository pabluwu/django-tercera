from rest_framework import serializers
from ..models import Emergencia

class EmergenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emergencia
        fields = '__all__'
        read_only_fields = ['autor']