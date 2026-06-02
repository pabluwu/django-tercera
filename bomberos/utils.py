import logging
from datetime import timedelta
from uuid import uuid4
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import localtime, now
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

def send_email_notification(subject, template_name, context, recipients, text_body=None, attachments=None):
    """
    Función genérica para enviar correos electrónicos con contenido HTML y adjuntos opcionales.
    """
    if not recipients:
        logger.warning(f"No hay destinatarios para el correo: {subject}")
        return False

    try:
        html_body = render_to_string(template_name, context)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body or subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_body, "text/html")

        if attachments:
            for attachment in attachments:
                email.attach(**attachment)

        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(f"Error enviando correo: {subject}")
        return False

def send_licencia_confirmation_email(licencia):
    """
    Envía un correo de confirmación al autor de la licencia.
    """
    user = licencia.autor
    if not user.email:
        logger.warning(f"El usuario {user.username} no tiene email registrado.")
        return False

    citacion = licencia.citacion
    context = {
        'user': user,
        'licencia': licencia,
        'citacion': citacion,
    }

    subject = f"Confirmación de Licencia - {citacion.nombre}"
    template = 'emails/licencia_created.html'
    
    fecha_local = localtime(citacion.fecha) if citacion.fecha else None
    text_body = (
        f"Hola {user.first_name}, se ha registrado tu licencia correctamente.\n\n"
        f"Motivo: {licencia.motivo}\n"
        f"Citación: {citacion.nombre}\n"
        f"Fecha Citación: {fecha_local.strftime('%d/%m/%Y %H:%M') if fecha_local else 'N/A'}\n"
    )

    return send_email_notification(subject, template, context, [user.email], text_body)

def build_citacion_ics(citacion):
    """
    Construye el contenido de un archivo ICS para una citación.
    """
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

def send_citacion_notification_email(citacion):
    """
    Envía una notificación de nueva citación a los destinatarios configurados.
    """
    recipients_raw = getattr(settings, 'CITACION_EMAIL_RECIPIENTS', '')
    recipients = [email.strip() for email in recipients_raw.replace(';', ',').split(',') if email.strip()]
    
    if not recipients:
        logger.warning("No hay destinatarios configurados para notificación de citaciones.")
        return False

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

    attachments = []
    ics_content = build_citacion_ics(citacion)
    if ics_content:
        attachments.append({
            'filename': f"citacion-{citacion.id}.ics",
            'content': ics_content,
            'mimetype': "text/calendar; charset=utf-8",
        })

    return send_email_notification(
        subject, 
        'emails/citacion_created.html', 
        context, 
        recipients, 
        text_body, 
        attachments
    )

def send_comprobante_upload_notification(comprobante):
    """
    Notifica al bombero y a todos los Tesoreros que se ha subido un nuevo comprobante.
    """
    User = get_user_model()
    bombero = comprobante.bombero
    meses = comprobante.meses_pagados.all()
    
    # Obtener correos de Tesoreros
    tesoreros_emails = list(User.objects.filter(groups__name='Tesorero', is_active=True).values_list('email', flat=True))
    
    recipients = list(set([bombero.email] + tesoreros_emails))
    recipients = [e for e in recipients if e]

    context = {
        'user': bombero,
        'comprobante': comprobante,
        'meses': meses,
    }

    subject = f"Comprobante Recibido - {bombero.first_name} {bombero.last_name}"
    return send_email_notification(subject, 'emails/comprobante_subido.html', context, recipients)

def send_comprobante_status_notification(comprobante):
    """
    Notifica al bombero si su comprobante fue aprobado o rechazado.
    """
    bombero = comprobante.bombero
    if not bombero.email:
        return False

    context = {
        'user': bombero,
        'aprobado': comprobante.aprobado,
        'observacion': comprobante.observacion,
        'meses': comprobante.meses_pagados.all(),
    }

    status_str = "Aprobado" if comprobante.aprobado else "Rechazado"
    subject = f"Resultado de Revisión: Comprobante {status_str}"
    
    return send_email_notification(subject, 'emails/comprobante_resultado.html', context, [bombero.email])

def send_cuotas_registradas_notification(comprobante):
    """
    Notifica al bombero que se le han registrado cuotas (ComprobanteTesorero).
    """
    bombero = comprobante.bombero
    if not bombero.email:
        return False

    context = {
        'user': bombero,
        'comprobante': comprobante,
        'meses': comprobante.meses_pagados.all(),
    }

    subject = "Registro de Cuotas Exitoso"
    return send_email_notification(subject, 'emails/cuotas_registradas.html', context, [bombero.email])

def send_archivo_notification_email(archivo):
    """
    Notifica a todos los usuarios activos que se ha subido un nuevo archivo.
    """
    User = get_user_model()
    # Obtener todos los correos de usuarios activos que tengan email
    recipients = list(User.objects.filter(is_active=True).exclude(email__isnull=True).exclude(email='').values_list('email', flat=True))
    
    if not recipients:
        return False

    base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000').rstrip('/')
    archivos_url = f"{base_url}/archivos"

    context = {
        'archivo': archivo,
        'archivos_url': archivos_url,
    }

    subject = f"Nuevo archivo disponible: {archivo.nombre}"
    return send_email_notification(subject, 'emails/archivo_uploaded.html', context, recipients)
