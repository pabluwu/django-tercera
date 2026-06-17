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

def test_async_dispatch():
    print("=" * 60)
    print("Prueba de Despacho de Correo Asíncrono")
    print("=" * 60)
    
    start_time = time.time()
    
    # Enviar correo usando el backend estándar de Django (que ahora es el nuestro)
    send_mail(
        subject='Prueba de Despacho Asíncrono - Antigravity',
        message=f'Esta es una prueba de velocidad.\nHora de gatillado: {time.strftime("%H:%M:%S")}',
        from_email=None, # Django usará DEFAULT_FROM_EMAIL
        recipient_list=['lopez.pablo2305@gmail.com'],
        fail_silently=False,
    )
    
    elapsed = time.time() - start_time
    print(f"\n[CLIENTE] La llamada a send_mail() retornó en: {elapsed:.4f} segundos.")
    print("Si tardó menos de 0.1s, significa que la asincronía está funcionando perfectamente y el request no fue bloqueado.")
    print("\n[INFO] Manteniendo el script abierto por 10 segundos para permitir que el hilo worker transmita el correo...")
    
    # Esperamos para que el hilo daemon complete el envío
    time.sleep(10)
    
    # Cerrar conexión del Singleton de manera segura al terminar
    SMTPService().close_connection()
    print("Prueba finalizada.")

if __name__ == '__main__':
    test_async_dispatch()
