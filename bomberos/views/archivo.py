# views.py
from rest_framework import viewsets, permissions, parsers, filters
from ..models import Archivo
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers.archivo import ArchivoSerializer
from ..utils import send_archivo_notification_email
from ..permissions import module_required

class ArchivoViewSet(viewsets.ModelViewSet):
    queryset = Archivo.objects.all().order_by('-creado_en')
    serializer_class = ArchivoSerializer
    permission_classes = [permissions.IsAuthenticated, module_required('archivos')]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['tipo']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['creado_en']

    def perform_create(self, serializer):
        archivo = serializer.save(creado_por=self.request.user)
        send_archivo_notification_email(archivo)
