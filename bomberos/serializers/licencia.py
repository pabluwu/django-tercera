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
        read_only_fields = ['autor_info', 'citacion_info', 'estado']

    def validate_documento(self, value):
        if value:
            # 500kb = 500 * 1024 bytes
            if value.size > 500 * 1024:
                raise serializers.ValidationError("El documento no debe superar los 500 KB.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        is_create = not self.instance
        if is_create and request and request.user:
            citacion = attrs.get('citacion')
            # Verificar si existe alguna licencia que no esté rechazada para este usuario y citación
            exists = Licencia.objects.filter(
                citacion=citacion,
                autor=request.user,
                estado__in=['pendiente', 'aceptada']
            ).exists()
            if exists:
                raise serializers.ValidationError(
                    {"citacion": "Ya tienes una solicitud de licencia pendiente o aceptada para esta citación."}
                )
        return attrs