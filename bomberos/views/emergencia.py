# views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Emergencia
from ..serializers.emergencia import EmergenciaSerializer

class EmergenciaViewSet(viewsets.ModelViewSet):
    queryset = Emergencia.objects.all()
    serializer_class = EmergenciaSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)
