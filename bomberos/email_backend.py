from django.core.mail.backends.base import BaseEmailBackend
from .email_service import SMTPService

class AsyncSingletonEmailBackend(BaseEmailBackend):
    """
    Backend de correo personalizado para Django.
    Intercepta los correos enviados nativamente por Django (o DRF)
    y los encola asíncronamente en el servicio SMTPService.
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        # Inicializa o recupera la instancia única del Singleton
        self.smtp_service = SMTPService()

    def send_messages(self, email_messages):
        """
        Encola de forma instantánea todos los mensajes y retorna la cantidad.
        El envío real se realiza secuencialmente en el hilo de fondo de SMTPService.
        """
        if not email_messages:
            return 0
        
        for message in email_messages:
            self.smtp_service.send_email_async(message)
            
        return len(email_messages)
