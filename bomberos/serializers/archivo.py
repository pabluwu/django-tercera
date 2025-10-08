# serializers.py
from rest_framework import serializers
from ..models import Archivo


class ArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = '__all__'
        read_only_fields = ['creado_por', 'creado_en']

    def validate(self, attrs):
        tipo = attrs.get("tipo")
        user = self.context['request'].user
        perm_codename = f"bomberos.can_upload_{tipo}"  # cambia "app_label" por el nombre de tu app

        if not user.has_perm(perm_codename):
            raise serializers.ValidationError(f"No tiene permiso para subir documentos de tipo '{tipo}'.")

        return attrs

    def create(self, validated_data):
        validated_data['creado_por'] = self.context['request'].user
        return super().create(validated_data)
