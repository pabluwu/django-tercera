# views.py
from rest_framework import viewsets, permissions, parsers, filters
from ..models import Archivo
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers.archivo import ArchivoSerializer

class ArchivoViewSet(viewsets.ModelViewSet):
    queryset = Archivo.objects.all().order_by('-creado_en')
    serializer_class = ArchivoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    filter_backends = [
        DjangoFilterBackend,  # ✅ para filtros por campos específicos
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['tipo']  # ✅ permite usar ?tipo=xxxx
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['creado_en']