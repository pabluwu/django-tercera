from rest_framework import viewsets, permissions
from bomberos.models import Licencia
from ..serializers.licencia import LicenciaSerializer

class LicenciaViewSet(viewsets.ModelViewSet):
    queryset = Licencia.objects.all()
    serializer_class = LicenciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        autor_id = self.request.query_params.get('autor')
        citacion_id = self.request.query_params.get('citacion')

        if autor_id:
            queryset = queryset.filter(autor_id=autor_id)
        if citacion_id:
            queryset = queryset.filter(citacion_id=citacion_id)

        return queryset