from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from ..models import Guardia, SolicitudReemplazo, Tenant
from ..permissions import module_required, groups_required
from ..serializers.guardia import (
    GuardiaSerializer,
    GuardiaBulkSaveSerializer,
    SolicitudReemplazoSerializer,
    UserMinimalSerializer
)
from ..utils import send_email_notification


class GuardiaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, module_required('guardias')]
    serializer_class = GuardiaSerializer
    queryset = Guardia.objects.all()

    def get_queryset(self):
        # Filtrar por el tenant del usuario logueado
        user = self.request.user
        profile = getattr(user, 'bombero', None)
        if not profile or not profile.tenant:
            return Guardia.objects.none()
        return Guardia.objects.filter(tenant=profile.tenant)

    def perform_create(self, serializer):
        profile = self.request.user.bombero
        serializer.save(tenant=profile.tenant, creado_por=self.request.user)

    @action(
        detail=False,
        methods=['post'],
        url_path='bulk-save',
        permission_classes=[IsAuthenticated, groups_required('Ayudante', 'Secretario'), module_required('guardias')]
    )
    def bulk_save(self, request):
        profile = request.user.bombero
        tenant = profile.tenant

        serializer = GuardiaBulkSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        anio = serializer.validated_data['anio']
        mes = serializer.validated_data['mes']
        days_data = serializer.validated_data['days']
        es_borrador_bulk = serializer.validated_data.get('es_borrador', False)

        dates_in_payload = [d['fecha'] for d in days_data]

        with transaction.atomic():
            # Guardar/Actualizar
            for day in days_data:
                fecha = day['fecha']
                oficial = day.get('oficial_id')
                conductor = day.get('conductor_id')
                bomberos_list = day.get('bomberos_ids', [])
                es_borrador_day = day.get('es_borrador', False) or es_borrador_bulk

                guardia, created = Guardia.objects.get_or_create(
                    tenant=tenant,
                    fecha=fecha,
                    defaults={'creado_por': request.user}
                )
                guardia.oficial = oficial
                guardia.conductor = conductor
                guardia.es_borrador = es_borrador_day
                guardia.bomberos.set(bomberos_list)
                guardia.save()

            # Borrar las guardias de este mes/año que ya no fueron seleccionadas
            Guardia.objects.filter(
                tenant=tenant,
                fecha__year=anio,
                fecha__month=mes
            ).exclude(fecha__in=dates_in_payload).delete()

        return Response({"detail": "Guardias planificadas y guardadas correctamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='conductores-disponibles')
    def conductores_disponibles(self, request):
        profile = request.user.bombero
        users = User.objects.filter(
            bombero__tenant=profile.tenant,
            bombero__is_conductor=True,
            is_active=True
        ).order_by('first_name', 'last_name')
        return Response(UserMinimalSerializer(users, many=True).data)

    @action(detail=False, methods=['get'], url_path='oficiales-disponibles')
    def oficiales_disponibles(self, request):
        profile = request.user.bombero
        # Oficiales: Ayudante, Teniente o Capitán
        users = User.objects.filter(
            Q(bombero__tenant=profile.tenant, is_active=True) & (
                Q(bombero__cargo__icontains='teniente') |
                Q(bombero__cargo__icontains='capitán') |
                Q(bombero__cargo__icontains='capitan') |
                Q(bombero__cargo__iexact='ayudante')
            )
        ).distinct().order_by('first_name', 'last_name')
        return Response(UserMinimalSerializer(users, many=True).data)

    @action(detail=False, methods=['get'], url_path='bomberos-disponibles')
    def bomberos_disponibles(self, request):
        profile = request.user.bombero
        users = User.objects.filter(
            bombero__tenant=profile.tenant,
            is_active=True
        ).order_by('first_name', 'last_name')
        return Response(UserMinimalSerializer(users, many=True).data)

    @action(detail=False, methods=['get'], url_path='mis-guardias')
    def mis_guardias(self, request):
        profile = request.user.bombero
        user = request.user
        anio = request.query_params.get('anio')
        mes = request.query_params.get('mes')

        if not anio or not mes:
            return Response({"detail": "Faltan parámetros 'anio' y 'mes'."}, status=status.HTTP_400_BAD_REQUEST)

        qs = Guardia.objects.filter(
            Q(tenant=profile.tenant) &
            Q(fecha__year=anio) &
            Q(fecha__month=mes) &
            Q(es_borrador=False) &
            (Q(oficial=user) | Q(conductor=user) | Q(bomberos=user))
        ).distinct().order_by('fecha')

        return Response(GuardiaSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='rango')
    def rango(self, request):
        profile = request.user.bombero
        fecha_inicio_raw = request.query_params.get('fecha-inicio')
        fecha_fin_raw = request.query_params.get('fecha-fin')

        if not fecha_inicio_raw or not fecha_fin_raw:
            return Response({"detail": "Faltan parámetros 'fecha-inicio' y 'fecha-fin' (formato YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
        except ValueError:
            return Response({"detail": "Formato de fecha inválido. Utilice YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        qs = Guardia.objects.filter(
            tenant=profile.tenant,
            fecha__range=(fecha_inicio, fecha_fin)
        )

        excluir_borradores = request.query_params.get('excluir-borradores') == 'true'
        if excluir_borradores:
            qs = qs.filter(es_borrador=False)

        qs = qs.prefetch_related('bomberos', 'oficial__bombero', 'conductor__bombero').order_by('fecha')

        return Response(GuardiaSerializer(qs, many=True).data)


class SolicitudReemplazoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, module_required('guardias')]
    serializer_class = SolicitudReemplazoSerializer
    queryset = SolicitudReemplazo.objects.all()

    def get_queryset(self):
        user = self.request.user
        # Retorna solicitudes donde el usuario es solicitante o el reemplazo propuesto
        return SolicitudReemplazo.objects.filter(
            Q(solicitante=user) | Q(reemplazo=user)
        ).order_by('-fecha_creacion')

    def perform_create(self, serializer):
        user = self.request.user
        reemplazo = serializer.validated_data['reemplazo']
        guardia = serializer.validated_data['guardia']

        # Validaciones
        if user == reemplazo:
            raise ValidationError("No puedes solicitar un reemplazo contigo mismo.")

        # Verificar que el solicitante pertenece a la guardia como bombero
        if not guardia.bomberos.filter(id=user.id).exists():
            raise ValidationError("No puedes solicitar reemplazo para una guardia en la que no estás asignado como bombero.")

        if guardia.es_borrador:
            raise ValidationError("No puedes solicitar reemplazo para una guardia en estado de borrador.")

        # Crear solicitud
        solicitud = serializer.save(solicitante=user)

        # Enviar correo de notificación
        self.enviar_email_solicitud(solicitud)

    def enviar_email_solicitud(self, solicitud):
        from django.conf import settings
        reemplazo_user = solicitud.reemplazo
        if not reemplazo_user.email:
            return

        frontend_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000').rstrip('/')
        solicitudes_url = f"{frontend_url}/guardias/solicitudes"

        context = {
            'solicitante': solicitud.solicitante,
            'reemplazo': reemplazo_user,
            'guardia': solicitud.guardia,
            'solicitudes_url': solicitudes_url
        }

        subject = f"Solicitud de Reemplazo de Guardia: {solicitud.guardia.fecha.strftime('%d/%m/%Y')}"
        text_body = (
            f"Hola {reemplazo_user.first_name},\n\n"
            f"El bombero {solicitud.solicitante.get_full_name()} te ha solicitado cubrir su guardia el día "
            f"{solicitud.guardia.fecha.strftime('%d/%m/%Y')}.\n\n"
            f"Por favor ingresa a la Intranet para Aceptar o Rechazar la solicitud:\n"
            f"{solicitudes_url}\n\n"
            "Este correo es automático."
        )

        send_email_notification(
            subject=subject,
            template_name='emails/reemplazo_guardia.html',
            context=context,
            recipients=[reemplazo_user.email],
            text_body=text_body
        )

    @action(detail=True, methods=['post'], url_path='responder')
    def responder(self, request, pk=None):
        solicitud = self.get_object()
        user = request.user

        # Validar que el usuario logueado es el reemplazo asignado
        if solicitud.reemplazo != user:
            return Response({"detail": "No tienes autorización para responder a esta solicitud."}, status=status.HTTP_403_FORBIDDEN)

        if solicitud.estado != 'pendiente':
            return Response({"detail": "Esta solicitud ya ha sido respondida."}, status=status.HTTP_400_BAD_REQUEST)

        accion = request.data.get('accion')
        if accion not in ['aceptar', 'rechazar']:
            return Response({"detail": "Acción inválida. Use 'aceptar' o 'rechazar'."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            solicitud.fecha_respuesta = timezone.now()
            if accion == 'aceptar':
                solicitud.estado = 'aceptada'
                
                # Actualizar la guardia reemplazando al bombero
                guardia = solicitud.guardia
                guardia.bomberos.remove(solicitud.solicitante)
                guardia.bomberos.add(solicitud.reemplazo)
                guardia.save()
            else:
                solicitud.estado = 'rechazada'
            
            solicitud.save()

        return Response({
            "detail": f"Solicitud de reemplazo {solicitud.estado} con éxito.",
            "estado": solicitud.estado
        }, status=status.HTTP_200_OK)
