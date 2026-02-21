# views.py

from collections import defaultdict
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
from ..models import ComprobanteTransferencia, ComprobanteTesorero, MesAnio, UserProfile
from ..permissions import groups_required
from ..serializers.tesoreria import (
    ComprobanteTransferenciaSerializer,
    ComprobanteTesoreroSerializer,
    MesAnioSerializer,
    BomberoCuotasSerializer
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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated, groups_required('Tesorero')],
    )
    def pendientes(self, request):
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
    permission_classes = [permissions.IsAuthenticated, groups_required('Tesorero')]
    
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


class ResumenCuotasViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        perfiles = UserProfile.objects.select_related('user').all()
        current_date = now().date()
        current_year = current_date.year
        current_month = current_date.month

        mes_entries = list(MesAnio.objects.all().values('id', 'anio', 'mes'))
        mes_info = {entry['id']: entry for entry in mes_entries}
        meses_por_anio = defaultdict(set)

        for entry in mes_entries:
            meses_por_anio[entry['anio']].add(entry['id'])

        pagos_por_usuario = defaultdict(lambda: defaultdict(set))

        tesorero_links = ComprobanteTesorero.objects.filter(
            meses_pagados__isnull=False
        ).values_list('bombero_id', 'meses_pagados__id')
        for bombero_id, mes_id in tesorero_links:
            info = mes_info.get(mes_id)
            if not info:
                continue
            pagos_por_usuario[bombero_id][info['anio']].add(mes_id)

        transferencia_links = ComprobanteTransferencia.objects.filter(
            aprobado=True,
            meses_pagados__isnull=False
        ).values_list('bombero_id', 'meses_pagados__id')
        for bombero_id, mes_id in transferencia_links:
            info = mes_info.get(mes_id)
            if not info:
                continue
            pagos_por_usuario[bombero_id][info['anio']].add(mes_id)

        ordered_years = sorted(meses_por_anio.keys())
        resultados = []

        meses_vigentes_ids = set()
        if current_year in meses_por_anio:
            meses_vigentes_ids = {
                mes_id
                for mes_id in meses_por_anio[current_year]
                if int(mes_info[mes_id]['mes']) <= current_month
            }

        for perfil in perfiles:
            cuotas_por_anio = []
            total_pagadas = 0
            total_pendientes = 0

            for anio in ordered_years:
                total_meses = len(meses_por_anio[anio])
                pagadas = len(pagos_por_usuario[perfil.user_id].get(anio, set()))
                pendientes = max(total_meses - pagadas, 0)

                cuotas_por_anio.append({
                    'anio': anio,
                    'pagadas': pagadas,
                    'pendientes': pendientes,
                })

                total_pagadas += pagadas
                total_pendientes += pendientes

            imagen_value = None
            if perfil.imagen:
                try:
                    imagen_value = perfil.imagen.url
                except ValueError:
                    imagen_value = perfil.imagen.name

            pagos_actual_year = pagos_por_usuario[perfil.user_id].get(current_year, set())
            pagos_hasta_mes_actual = pagos_actual_year.intersection(meses_vigentes_ids)
            pendientes_hasta_mes_actual = max(len(meses_vigentes_ids) - len(pagos_hasta_mes_actual), 0)
            is_moroso = 1 if pendientes_hasta_mes_actual > 4 else 0

            resultados.append({
                'id': perfil.id,
                'user': {
                    'id': perfil.user.id,
                    'username': perfil.user.username,
                    'email': perfil.user.email,
                    'first_name': perfil.user.first_name,
                    'last_name': perfil.user.last_name,
                },
                'rut': perfil.rut,
                'fecha_ingreso': perfil.fecha_ingreso,
                'telefono': perfil.telefono,
                'contacto': perfil.contacto,
                'imagen': imagen_value,
                'cuotas_por_anio': cuotas_por_anio,
                'total_pagadas': total_pagadas,
                'total_pendientes': total_pendientes,
                'isMoroso': is_moroso,
            })

        serializer = BomberoCuotasSerializer(resultados, many=True)
        return Response(serializer.data)
