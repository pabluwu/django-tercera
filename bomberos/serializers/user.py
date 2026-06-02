from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import UserProfile, Citacion, Licencia
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = '__all__'


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = [
            'nombres',
            'apellido_paterno',
            'apellido_materno',
            'cia',
            'registro',
            'registro_cia',
            'codigo_llamado',
            'cargo',
            'rut',
            'fecha_ingreso',
            'telefono',
            'sexo',
            'nacionalidad',
            'sangre_grupo',
            'estado_civil',
            'profesion',
            'direccion_calle',
            'direccion_numero',
            'direccion_complemento',
            'direccion_comuna',
            'contacto',
            'imagen',
            'email',
            'first_name',
            'last_name',
        ]
        extra_kwargs = {
            'rut': {'required': False},
            'fecha_ingreso': {'required': False, 'allow_null': True},
            'telefono': {'required': False, 'allow_null': True},
            'nombres': {'required': False, 'allow_blank': True},
            'apellido_paterno': {'required': False, 'allow_blank': True},
            'apellido_materno': {'required': False, 'allow_blank': True},
            'cia': {'required': False, 'allow_blank': True},
            'registro': {'required': False, 'allow_blank': True},
            'registro_cia': {'required': False, 'allow_blank': True},
            'codigo_llamado': {'required': False, 'allow_blank': True},
            'cargo': {'required': False, 'allow_blank': True},
            'sexo': {'required': False, 'allow_blank': True},
            'nacionalidad': {'required': False, 'allow_blank': True},
            'sangre_grupo': {'required': False, 'allow_blank': True},
            'estado_civil': {'required': False, 'allow_blank': True},
            'profesion': {'required': False, 'allow_blank': True},
            'direccion_calle': {'required': False, 'allow_blank': True},
            'direccion_numero': {'required': False, 'allow_blank': True},
            'direccion_complemento': {'required': False, 'allow_blank': True},
            'direccion_comuna': {'required': False, 'allow_blank': True},
            'contacto': {'required': False, 'allow_null': True},
            'imagen': {'required': False, 'allow_null': True},
        }

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)

        # Compresión de imagen si se está subiendo una nueva
        imagen = validated_data.get('imagen')
        if imagen and hasattr(imagen, 'file'):
            try:
                img = Image.open(imagen)
                
                # Convertir a RGB si es necesario (para evitar problemas con JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Redimensionar si es muy grande (ej. max 1024px de ancho o alto)
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Guardar en un buffer
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=70, optimize=True)
                buffer.seek(0)
                
                # Crear un nuevo archivo de contenido para Django
                filename = os.path.splitext(imagen.name)[0] + '.jpg'
                validated_data['imagen'] = ContentFile(buffer.read(), name=filename)
            except Exception as e:
                # Si falla el procesamiento, dejamos la imagen original o manejamos el error
                print(f"Error al comprimir la imagen: {e}")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user.save()
        instance.save()
        return instance
