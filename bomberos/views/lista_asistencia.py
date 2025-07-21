from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import ListaAsistencia
from ..serializers.lista_asistencia import ListaAsistenciaCreateSerializer

class ListaAsistenciaViewSet(viewsets.ModelViewSet):
    queryset = ListaAsistencia.objects.all()
    serializer_class = ListaAsistenciaCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lista = serializer.save()
        return Response(serializer.to_representation(lista), status=status.HTTP_201_CREATED)
