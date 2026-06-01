from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from ..models import ListaAsistencia, Asistencia, ExcepcionAsistencia

class ListaAsistenciaCreateSerializer(serializers.Serializer):
    content_type = serializers.CharField()
    object_id = serializers.IntegerField()
    bomberos = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    def create(self, validated_data):
        content_type_str = validated_data['content_type']
        object_id = validated_data['object_id']
        bomberos_ids = validated_data['bomberos']

        try:
            content_type = ContentType.objects.get(model=content_type_str)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Tipo de contenido inválido.")

        lista = ListaAsistencia.objects.create(
            content_type=content_type,
            object_id=object_id
        )

        for bombero_id in bomberos_ids:
            user = User.objects.get(id=bombero_id)
            Asistencia.objects.create(lista=lista, bombero=user, asistio=True)

        return lista

    def to_representation(self, instance):
        tipo_lista = instance.content_type.model
        evento = getattr(instance, 'evento', None)
        evento_info = {}
        licencias = []
        total_licencias = 0
        excepciones = []
        total_excepciones = 0

        # Citación
        if tipo_lista == 'citacion' and evento is not None and hasattr(evento, 'licencia_set'):
            citacion = evento
            evento_info = {
                'id': citacion.id,
                'nombre': citacion.nombre,
                'descripcion': citacion.descripcion,
                'fecha': citacion.fecha,
                'lugar': citacion.lugar,
                'tenida': citacion.tenida,
                'autor': {
                    'email': citacion.autor.email,
                    'first_name': citacion.autor.first_name,
                    'last_name': citacion.autor.last_name,
                }
            }
            licencias_queryset = citacion.licencia_set.select_related('autor')
            total_licencias = licencias_queryset.count()
            licencias = [
                {
                    'email': l.autor.email,
                    'first_name': l.autor.first_name,
                    'last_name': l.autor.last_name,
                    'motivo': l.motivo,
                    'fecha_licencia': l.fecha_licencia,
                }
                for l in licencias_queryset
            ]

        # Emergencia
        elif tipo_lista == 'emergencia' and evento is not None:
            emergencia = evento
            evento_info = {
                'id': emergencia.id,
                'clave': emergencia.clave,
                'fecha': emergencia.fecha,
                'unidades': emergencia.unidades,
                'autor': {
                    'email': emergencia.autor.email,
                    'first_name': emergencia.autor.first_name,
                    'last_name': emergencia.autor.last_name,
                }
            }

        # Obtener bomberos con excepciones activas para la fecha del evento
        if evento is not None and hasattr(evento, 'fecha'):
            evento_fecha = evento.fecha
            excepciones_queryset = ExcepcionAsistencia.objects.filter(
                is_active=True,
                fecha_inicio__lte=evento_fecha,
                fecha_fin__gte=evento_fecha
            ).select_related('usuario')
            
            total_excepciones = excepciones_queryset.count()
            
            # Agrupar excepciones por tipo
            excepciones_por_tipo = {}
            for exc in excepciones_queryset:
                tipo = exc.tipo_excepcion
                if tipo not in excepciones_por_tipo:
                    excepciones_por_tipo[tipo] = []
                excepciones_por_tipo[tipo].append({
                    'bombero_id': exc.usuario.id,
                    'email': exc.usuario.email,
                    'first_name': exc.usuario.first_name,
                    'last_name': exc.usuario.last_name,
                    'fecha_inicio': exc.fecha_inicio,
                    'fecha_fin': exc.fecha_fin,
                    'motivo': exc.motivo,
                })
            
            excepciones = excepciones_por_tipo

        return {
            'id': instance.id,
            'tipo': tipo_lista,
            'evento': evento_info,  # ahora contiene los datos completos
            'fecha_creacion': instance.fecha_creacion,
            'total_licencias': total_licencias,
            'licencias': licencias,
            'total_excepciones': total_excepciones,
            'excepciones': excepciones,
            'asistencias': [
                {
                    'bombero_id': a.bombero.id,
                    'email': a.bombero.email,
                    'first_name': a.bombero.first_name,
                    'last_name': a.bombero.last_name,
                    'hora_llegada': a.hora_llegada,
                }
                for a in instance.asistencias.all()
            ]
        }


