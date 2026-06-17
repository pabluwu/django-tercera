import smtplib
import threading
import queue
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SMTPService:
    """
    Servicio Singleton para el manejo y optimización de envíos SMTP.
    Mantiene una sesión activa persistente en un hilo secundario dedicado (worker),
    evitando la latencia del handshake SSL/TLS en cada solicitud HTTP de los usuarios.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SMTPService, cls).__new__(cls, *args, **kwargs)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.queue = queue.Queue()
        self.connection = None

        # Iniciar el hilo Worker secundario (daemon para no bloquear el apagado del servidor)
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.name = "SMTPBackgroundWorker"
        self.worker_thread.start()

        self._initialized = True
        logger.info("[SMTPService] Singleton inicializado. Worker en segundo plano iniciado.")

    def _get_connection(self):
        """
        Obtiene la conexión SMTP activa. 
        Si no existe o si ha expirado (validado con NOOP), establece una nueva conexión.
        """
        host = getattr(settings, 'EMAIL_HOST', '')
        port = int(getattr(settings, 'EMAIL_PORT', 465))
        user = getattr(settings, 'EMAIL_HOST_USER', '')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', True)
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        timeout = getattr(settings, 'EMAIL_TIMEOUT', 15)

        # 1. Asegurar codificación UTF-8 en credenciales con caracteres especiales (ñ, tildes)
        if isinstance(user, str):
            user = user.encode('utf-8').decode('utf-8')
        if isinstance(password, str):
            password = password.encode('utf-8').decode('utf-8')

        # 2. Si ya existe una conexión, verificar su estado antes de reusar
        if self.connection is not None:
            try:
                # El comando NOOP verifica si el socket sigue abierto y el servidor responde
                status, msg = self.connection.noop()
                if status == 250:
                    return self.connection
                logger.warning(f"[SMTPService] NOOP no retornó status 250 (retornó {status}: {msg}). Reconectando...")
            except Exception as e:
                logger.info(f"[SMTPService] Conexión SMTP existente inactiva o cerrada ({e}). Reconectando...")
            
            self.close_connection()

        # 3. Crear una nueva conexión y realizar handshake
        logger.info(f"[SMTPService] Estableciendo nueva sesión SMTP con {host}:{port}...")
        start_time = time.time()
        try:
            if use_ssl:
                # SSL Directo (Puerto 465 por defecto)
                conn = smtplib.SMTP_SSL(host, port, timeout=timeout)
            else:
                # SMTP estándar (Puerto 587 o 25)
                conn = smtplib.SMTP(host, port, timeout=timeout)
                if use_tls:
                    conn.starttls()
            
            # Identificarse con el servidor SMTP
            conn.ehlo()
            
            # Autenticación. Python 3 codifica automáticamente a UTF-8 si el servidor soporta SMTPUTF8.
            # En caso de servidores antiguos, smtplib intenta codificar en utf-8 o ascii.
            conn.login(user, password)
            
            self.connection = conn
            logger.info(f"[SMTPService] Conexión SMTP establecida exitosamente en {time.time() - start_time:.2f} segundos.")
            return self.connection
        except Exception as e:
            logger.error(f"[SMTPService] Error crítico al conectar/autenticar en SMTP: {e}", exc_info=True)
            self.connection = None
            return None

    def close_connection(self):
        """
        Cierra de forma limpia y segura la sesión SMTP actual.
        """
        if self.connection:
            try:
                self.connection.quit()
            except Exception:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.connection = None
            logger.info("[SMTPService] Sesión SMTP cerrada.")

    def send_email_async(self, email_message):
        """
        Coloca un objeto EmailMessage de Django en la cola de procesamiento en segundo plano.
        Esta llamada es instantánea y no bloquea el hilo de la solicitud HTTP.
        """
        self.queue.put(email_message)

    def _worker_loop(self):
        """
        Loop continuo del hilo secundario que consume los correos de la cola
        y los envía en serie reutilizando la conexión SMTP activa.
        """
        logger.info("[SMTPService] Loop de Worker en segundo plano iniciado.")
        while True:
            try:
                # Bloquea hasta que haya un correo disponible en la cola
                email_message = self.queue.get()
                
                success = False
                # Reintentos automáticos si falla la transmisión (ej. pérdida temporal de red)
                for attempt in range(1, 4):
                    try:
                        conn = self._get_connection()
                        if conn is None:
                            raise ConnectionError("No se pudo establecer conexión con el servidor SMTP.")

                        # Obtener destinatarios y remitente
                        from_email = email_message.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
                        recipients = email_message.to
                        
                        if not recipients:
                            logger.warning("[SMTPService] Mensaje ignorado debido a que la lista de destinatarios está vacía.")
                            break
                        
                        # Django construye el cuerpo MIME completo incluyendo adjuntos e imágenes embebidas en bytes (UTF-8)
                        msg_bytes = email_message.message().as_bytes()
                        
                        # Enviar el correo electrónico
                        logger.info(f"[SMTPService] Transmitiendo correo a {recipients} (Intento {attempt})...")
                        conn.sendmail(from_email, recipients, msg_bytes)
                        logger.info(f"[SMTPService] ¡Correo transmitido con éxito a {recipients}!")
                        
                        success = True
                        break
                    except Exception as e:
                        logger.error(f"[SMTPService] Error en intento {attempt} enviando correo: {e}")
                        # Forzar cierre de conexión para reconectar limpiamente en el próximo intento
                        self.close_connection()
                        if attempt < 3:
                            time.sleep(2 ** attempt)  # Backoff exponencial (2s, 4s)

                if not success:
                    logger.error(f"[SMTPService] Fallo final tras 3 intentos. El correo a {email_message.to} no pudo ser enviado.")

                # Marcar la tarea como resuelta
                self.queue.task_done()

            except Exception as e:
                logger.error(f"[SMTPService] Excepción inesperada en worker loop: {e}", exc_info=True)
                time.sleep(5)  # Evita ciclos infinitos ultrarrápidos ante fallos graves
