import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime, now
from uuid import uuid4
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bomberos.models import Citacion, ListaAsistencia
from ..serializers.citacion import CitacionSerializer

logger = logging.getLogger(__name__)

class CitacionViewSet(viewsets.ModelViewSet):
    queryset = Citacion.objects.all()
    serializer_class = CitacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        citacion = serializer.save(autor=self.request.user)
        self._send_citacion_email(citacion)

    def get_queryset(self):
        queryset = super().get_queryset()
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')

        if fecha_desde:
            queryset = queryset.filter(fecha__gte=parse_datetime(fecha_desde))
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=parse_datetime(fecha_hasta))

        return queryset

    def _get_citacion_recipients(self):
        mode = getattr(settings, 'CITACION_EMAIL_RECIPIENTS_MODE', 'list').lower()
        if mode == 'all_users':
            User = get_user_model()
            return list(
                User.objects.filter(is_active=True)
                .exclude(email__isnull=True)
                .exclude(email__exact='')
                .values_list('email', flat=True)
            )

        raw = getattr(settings, 'CITACION_EMAIL_RECIPIENTS', '')
        return [email.strip() for email in raw.replace(';', ',').split(',') if email.strip()]

    def _send_citacion_email(self, citacion):
        recipients = self._get_citacion_recipients()
        if not recipients:
            logger.warning("No hay destinatarios configurados para notificación de citaciones.")
            return

        base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000').rstrip('/')
        citacion_url = f"{base_url}/citaciones/{citacion.id}"

        fecha_local = localtime(citacion.fecha) if citacion.fecha else None
        context = {
            'citacion': citacion,
            'fecha': fecha_local,
            'citacion_url': citacion_url,
        }

        subject = f"Nueva citación: {citacion.nombre}"
        text_body = (
            "Se ha creado una nueva citación.\n\n"
            f"Nombre: {citacion.nombre}\n"
            f"Descripción: {citacion.descripcion or '-'}\n"
            f"Fecha: {fecha_local.strftime('%d/%m/%Y %H:%M') if fecha_local else '-'}\n"
            f"Lugar: {citacion.lugar}\n"
            f"Tenida: {citacion.tenida}\n\n"
            f"Ver detalle: {citacion_url}\n"
        )
        try:
            html_body = render_to_string('emails/citacion_created.html', context)
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_body, "text/html")

            ics_content = self._build_citacion_ics(citacion)
            if ics_content:
                email.attach(
                    filename=f"citacion-{citacion.id}.ics",
                    content=ics_content,
                    mimetype="text/calendar; charset=utf-8",
                )
            email.send(fail_silently=False)
        except Exception:
            logger.exception("Error enviando correo de citación")

    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        """Citaciones pasadas sin lista de asistencia asociada"""
        citacion_type = ContentType.objects.get_for_model(Citacion)
        citaciones_con_lista = ListaAsistencia.objects.filter(
            content_type=citacion_type
        ).values_list('object_id', flat=True)

        citaciones_disponibles = Citacion.objects.filter(
            fecha__lt=now()
        ).exclude(id__in=citaciones_con_lista)

        serializer = self.get_serializer(citaciones_disponibles, many=True)
        return Response(serializer.data)

    def _build_citacion_ics(self, citacion):
        if not citacion.fecha:
            return None

        dtstart = localtime(citacion.fecha)
        dtend = dtstart + timedelta(hours=1)
        dtstamp = localtime(now())
        uid = f"citacion-{citacion.id}-{uuid4()}@tercera-api"

        def format_dt(value):
            return value.strftime("%Y%m%dT%H%M%S")

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Tercera API//Citaciones//ES",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{format_dt(dtstamp)}",
            f"DTSTART:{format_dt(dtstart)}",
            f"DTEND:{format_dt(dtend)}",
            f"SUMMARY:{citacion.nombre}",
            f"DESCRIPTION:{citacion.descripcion or ''}",
            f"LOCATION:{citacion.lugar}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "\r\n".join(lines)
