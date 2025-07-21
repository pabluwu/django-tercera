from rest_framework import serializers
from ..models import Citacion
from .user import UserSerializer

class CitacionSerializer(serializers.ModelSerializer):
    autor_info = UserSerializer(source='autor', read_only=True)

    class Meta:
        model = Citacion
        fields = '__all__'  # incluye 'autor'
        read_only_fields = ['autor_info']
