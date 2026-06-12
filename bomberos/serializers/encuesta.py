from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from ..models import Formulario, FormularioCampo, FormularioRespuesta, FormularioRespuestaValor
from .user import UserSerializer

class FormularioCampoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormularioCampo
        fields = ['id', 'label', 'tipo_campo', 'obligatorio', 'opciones', 'orden']
        read_only_fields = ['id']


class FormularioSerializer(serializers.ModelSerializer):
    campos = FormularioCampoSerializer(many=True, required=False)
    creado_por_info = UserSerializer(source='creado_por', read_only=True)
    num_respuestas = serializers.SerializerMethodField()
    respondido = serializers.SerializerMethodField()

    class Meta:
        model = Formulario
        fields = [
            'id', 'titulo', 'descripcion', 'fecha_lanzamiento', 
            'fecha_inicio', 'fecha_fin', 'uuid', 'creado_por', 
            'creado_por_info', 'campos', 'num_respuestas', 'respondido', 
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'uuid', 'creado_por', 'creado_por_info', 'num_respuestas', 'respondido', 'creado_en', 'actualizado_en']

    def get_num_respuestas(self, obj):
        return obj.respuestas.count()

    def get_respondido(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.respuestas.filter(usuario=request.user).exists()
        return False

    def create(self, validated_data):
        campos_data = validated_data.pop('campos', [])
        formulario = Formulario.objects.create(**validated_data)
        for i, campo_data in enumerate(campos_data):
            campo_data['orden'] = campo_data.get('orden', i)
            FormularioCampo.objects.create(formulario=formulario, **campo_data)
        return formulario

    def update(self, instance, validated_data):
        campos_data = validated_data.pop('campos', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if campos_data is not None:
            # Si ya hay respuestas, no modificamos los campos para proteger la integridad de datos
            if not instance.respuestas.exists():
                instance.campos.all().delete()
                for i, campo_data in enumerate(campos_data):
                    campo_data['orden'] = campo_data.get('orden', i)
                    FormularioCampo.objects.create(formulario=instance, **campo_data)
        
        return instance


class FormularioRespuestaValorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormularioRespuestaValor
        fields = ['campo', 'valor']


class FormularioRespuestaSerializer(serializers.ModelSerializer):
    valores = FormularioRespuestaValorSerializer(many=True)
    usuario_info = UserSerializer(source='usuario', read_only=True)

    class Meta:
        model = FormularioRespuesta
        fields = ['id', 'formulario', 'usuario', 'usuario_info', 'valores', 'creado_en']
        read_only_fields = ['id', 'usuario', 'usuario_info', 'creado_en']

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None
        formulario = attrs.get('formulario')

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Debe estar autenticado para responder.")

        # Validar respuesta única
        if FormularioRespuesta.objects.filter(formulario=formulario, usuario=user).exists():
            raise serializers.ValidationError("Ya has respondido a este formulario.")

        # Validar fechas
        ahora = timezone.now()
        if formulario.fecha_lanzamiento > ahora or formulario.fecha_inicio > ahora:
            raise serializers.ValidationError("Este formulario aún no está disponible para recibir respuestas.")
        if formulario.fecha_fin and formulario.fecha_fin < ahora:
            raise serializers.ValidationError("El período para responder este formulario ha finalizado.")

        # Validar campos obligatorios y tipos de datos
        valores_data = attrs.get('valores', [])
        campos_enviados = {v['campo'].id: v['valor'] for v in valores_data}
        
        # Obtener campos desde la BD
        campos_form = formulario.campos.all()
        
        for campo in campos_form:
            valor = campos_enviados.get(campo.id)
            
            # Validar obligatorio
            if campo.obligatorio:
                if valor is None or valor == '' or (isinstance(valor, list) and len(valor) == 0):
                    raise serializers.ValidationError(f"El campo '{campo.label}' es obligatorio.")
            
            # Validar tipo de dato si se envió
            if valor is not None and valor != '':
                if campo.tipo_campo == 'numerico':
                    try:
                        float(valor)
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(f"El campo '{campo.label}' debe ser numérico.")
                
                elif campo.tipo_campo == 'seleccion_unica':
                    if valor not in campo.opciones:
                        raise serializers.ValidationError(f"El valor '{valor}' no es una opción válida para '{campo.label}'.")
                
                elif campo.tipo_campo == 'seleccion_multiple':
                    if not isinstance(valor, list):
                        raise serializers.ValidationError(f"El campo '{campo.label}' requiere una lista de selecciones.")
                    for item in valor:
                        if item not in campo.opciones:
                            raise serializers.ValidationError(f"El valor '{item}' no es una opción válida para '{campo.label}'.")
        
        return attrs

    def create(self, validated_data):
        valores_data = validated_data.pop('valores')
        request = self.context.get('request')
        usuario = request.user
        
        with transaction.atomic():
            respuesta = FormularioRespuesta.objects.create(usuario=usuario, **validated_data)
            for valor_data in valores_data:
                FormularioRespuestaValor.objects.create(respuesta=respuesta, **valor_data)
        
        return respuesta
