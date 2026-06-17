import os
import django
import time
import logging

# Configurar logging para ver la salida del hilo worker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s'
)

# Inicializar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import send_mail
from bomberos.email_service import SMTPService

def test_reuse():
    print("=" * 60)
    print("Prueba de Reutilización de Conexión SMTP (Singleton)")
    print("=" * 60)
    
    # Enviar primer correo
    print("\n[CLIENTE] Gatillando primer correo...")
    send_mail(
        subject='Prueba Reutilización - Correo 1',
        message='Este es el primer correo de la prueba.',
        from_email=None,
        recipient_list=['lopez.pablo2305@gmail.com'],
    )
    
    # Esperar 4 segundos para asegurar que el primer correo se transmita por completo
    time.sleep(4)
    
    # Enviar segundo correo
    print("\n[CLIENTE] Gatillando segundo correo...")
    send_mail(
        subject='Prueba Reutilización - Correo 2',
        message='Este es el segundo correo y debería reutilizar la conexión existente.',
        from_email=None,
        recipient_list=['lopez.pablo2305@gmail.com'],
    )
    
    # Esperar 4 segundos para la transmisión del segundo correo
    time.sleep(4)
    
    # Cerrar conexión de forma manual al terminar el script
    SMTPService().close_connection()
    print("\nPrueba de reutilización finalizada.")

if __name__ == '__main__':
    test_reuse()
