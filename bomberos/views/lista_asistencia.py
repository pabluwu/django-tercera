from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from ..models import ListaAsistencia
from ..serializers.lista_asistencia import ListaAsistenciaCreateSerializer

class ListaAsistenciaViewSet(viewsets.ModelViewSet):
    queryset = ListaAsistencia.objects.all()
    serializer_class = ListaAsistenciaCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        content_type_param = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')

        if content_type_param:
            normalized = content_type_param.lower()
            app_label = self.request.query_params.get('app_label', 'bomberos')

            if '.' in normalized:
                app_label, normalized = normalized.split('.', 1)

            try:
                content_type = ContentType.objects.get(app_label=app_label, model=normalized)
            except ContentType.DoesNotExist:
                raise ValidationError({"content_type": "Tipo de contenido inválido."})
            queryset = queryset.filter(content_type=content_type)

        if object_id:
            try:
                object_id = int(object_id)
            except (TypeError, ValueError):
                raise ValidationError({"object_id": "Debe ser un número entero válido."})
            queryset = queryset.filter(object_id=object_id)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lista = serializer.save()
        return Response(serializer.to_representation(lista), status=status.HTTP_201_CREATED)
