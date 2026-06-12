from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Guardia, SolicitudReemplazo, UserProfile


class UserMinimalSerializer(serializers.ModelSerializer):
    nombres = serializers.CharField(source='bombero.nombres', read_only=True)
    apellido_paterno = serializers.CharField(source='bombero.apellido_paterno', read_only=True)
    apellido_materno = serializers.CharField(source='bombero.apellido_materno', read_only=True)
    cargo = serializers.CharField(source='bombero.cargo', read_only=True)
    is_conductor = serializers.BooleanField(source='bombero.is_conductor', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'nombres', 'apellido_paterno', 'apellido_materno', 'cargo', 'is_conductor']


class GuardiaSerializer(serializers.ModelSerializer):
    oficial = UserMinimalSerializer(read_only=True)
    conductor = UserMinimalSerializer(read_only=True)
    bomberos = UserMinimalSerializer(many=True, read_only=True)

    oficial_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='oficial', write_only=True, required=False, allow_null=True
    )
    conductor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='conductor', write_only=True, required=False, allow_null=True
    )
    bomberos_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='bomberos', write_only=True, many=True, required=False
    )

    class Meta:
        model = Guardia
        fields = [
            'id', 'fecha', 'oficial', 'oficial_id', 'conductor', 'conductor_id',
            'bomberos', 'bomberos_ids', 'creado_en', 'actualizado_en', 'es_borrador'
        ]

    def create(self, validated_data):
        bomberos_data = validated_data.pop('bomberos', [])
        guardia = Guardia.objects.create(**validated_data)
        if bomberos_data:
            guardia.bomberos.set(bomberos_data)
        return guardia

    def update(self, instance, validated_data):
        bomberos_data = validated_data.pop('bomberos', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if bomberos_data is not None:
            instance.bomberos.set(bomberos_data)
        return instance


class GuardiaDayInputSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    oficial_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    conductor_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    bomberos_ids = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    es_borrador = serializers.BooleanField(default=False, required=False)


class GuardiaBulkSaveSerializer(serializers.Serializer):
    anio = serializers.IntegerField()
    mes = serializers.IntegerField()
    days = GuardiaDayInputSerializer(many=True)
    es_borrador = serializers.BooleanField(default=False, required=False)


class SolicitudReemplazoSerializer(serializers.ModelSerializer):
    guardia = GuardiaSerializer(read_only=True)
    guardia_id = serializers.PrimaryKeyRelatedField(queryset=Guardia.objects.all(), source='guardia', write_only=True)
    solicitante = UserMinimalSerializer(read_only=True)
    reemplazo = UserMinimalSerializer(read_only=True)
    reemplazo_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='reemplazo', write_only=True)

    class Meta:
        model = SolicitudReemplazo
        fields = [
            'id', 'guardia', 'guardia_id', 'solicitante', 'reemplazo', 'reemplazo_id',
            'estado', 'fecha_creacion', 'fecha_respuesta'
        ]
        read_only_fields = ['estado', 'fecha_creacion', 'fecha_respuesta']
