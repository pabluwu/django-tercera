# views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
from ..models import ComprobanteTransferencia, ComprobanteTesorero, MesAnio
from ..serializers.tesoreria import (
    ComprobanteTransferenciaSerializer,
    ComprobanteTesoreroSerializer,
    MesAnioSerializer
)

class ComprobanteTransferenciaViewSet(viewsets.ModelViewSet):
    queryset = ComprobanteTransferencia.objects.all()
    serializer_class = ComprobanteTransferenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser] 

    def perform_create(self, serializer):
        print(self.request.data)
        serializer.save(bombero=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            print("Errores de validación:", e.detail)
            raise

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pendientes(self, request):
        if not request.user.is_staff:
            return Response({"detail": "No autorizado"}, status=403)
        pendientes = self.queryset.filter(aprobado__isnull=True)
        return Response(self.get_serializer(pendientes, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def aprobar(self, request, pk=None):
        instance = self.get_object()
        numero = request.data.get("numero_comprobante")
        monto = request.data.get("monto_total")

        if not numero or not monto:
            return Response({"detail": "Faltan datos"}, status=400)

        comprobante = ComprobanteTesorero.objects.create(
            numero_comprobante=numero,
            tesorero=request.user,
            bombero=instance.bombero,
            monto_total=monto,
            metodo_pago='transferencia'
        )
        comprobante.meses_pagados.set(instance.meses_pagados.all())
        comprobante.save()

        instance.aprobado = True
        instance.revisado_por = request.user
        instance.fecha_revision = now()
        instance.save()

        return Response({"detail": "Comprobante aprobado y registrado correctamente"})

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def rechazar(self, request, pk=None):
        instance = self.get_object()
        observacion = request.data.get("observacion", "")
        instance.aprobado = False
        instance.revisado_por = request.user
        instance.fecha_revision = now()
        instance.observacion = observacion
        instance.save()
        return Response({"detail": "Comprobante rechazado"})

class ComprobanteTesoreroViewSet(viewsets.ModelViewSet):
    queryset = ComprobanteTesorero.objects.all()
    serializer_class = ComprobanteTesoreroSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(tesorero=self.request.user) 
    
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            print("Errores de validación:", e.detail)
            raise

class MesAnioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MesAnio.objects.all()
    serializer_class = MesAnioSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mis_meses_pagados(self, request):
        bombero = request.user

        ids_tesorero = ComprobanteTesorero.objects.filter(
            bombero=bombero
        ).values_list('meses_pagados', flat=True)

        ids_transferencia = ComprobanteTransferencia.objects.filter(
            bombero=bombero,
            aprobado=True
        ).values_list('meses_pagados', flat=True)

        ids = set(ids_tesorero).union(set(ids_transferencia))
        meses = MesAnio.objects.filter(id__in=ids).order_by('anio', 'mes')

        return Response(self.get_serializer(meses, many=True).data)

    @action(detail=False, methods=['get'], url_path='meses_pagados_por_bombero/(?P<bombero_id>[^/.]+)')
    def meses_pagados_por_bombero(self, request, bombero_id=None):
        ids_tesorero = ComprobanteTesorero.objects.filter(
            bombero_id=bombero_id
        ).values_list('meses_pagados', flat=True)

        ids_transferencia = ComprobanteTransferencia.objects.filter(
            bombero_id=bombero_id,
            aprobado=True
        ).values_list('meses_pagados', flat=True)

        ids = set(ids_tesorero).union(set(ids_transferencia))
        meses = MesAnio.objects.filter(id__in=ids).order_by('anio', 'mes')

        return Response(MesAnioSerializer(meses, many=True).data)

