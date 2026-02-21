from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

# 1. Rutas básicas
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Carga de variables de entorno (.env para local)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# 3. Configuración de Entorno
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-%g-!cf+4-(mc94tz$^a%py76mij$l%6vteb^$mn26-(@k6-zdx')
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = []
render_external_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname:
    ALLOWED_HOSTS.append(render_external_hostname)
else:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

# 4. Definición de Aplicaciones
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Para archivos estáticos en Render
    'django.contrib.staticfiles',
    'rest_framework',
    'bomberos',
    'django_filters',
]

# 5. Middleware (Manteniendo tu log personalizado)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Requerido por Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ApiLogMiddleware', # Tu middleware original
]

# 6. CORS y REST Framework (Tus valores originales)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

ROOT_URLCONF = 'core.urls'

# 7. TEMPLATES (Corregido para el error admin.E403)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# 8. Base de Datos (Solución para Aiven + Local)
if os.getenv('DATABASE_URL'):
    db_config = dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
    )
    # Limpieza de argumentos conflictivos
    db_config.pop('sslmode', None)
    db_config.pop('ssl-mode', None)
    
    db_config['OPTIONS'] = {
        'ssl': {'ca': None},
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }
    DATABASES = {'default': db_config}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'tercera_api',
            'USER': 'root',
            'PASSWORD': 'sup3rl1m',
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# 9. Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 10. Internacionalización
LANGUAGE_CODE = 'es-cl' # Cambiado a español si prefieres
TIME_ZONE = 'America/Santiago' # Ajustado a tu zona horaria
USE_I18N = True
USE_TZ = True

# 11. Archivos Estáticos y Media
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/documentos/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'documentos')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 12. Email y Notificaciones (Tus variables originales)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('SMTP_HOST', '')
EMAIL_PORT = int(os.getenv('SMTP_PORT', '465'))
EMAIL_HOST_USER = os.getenv('SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('SMTP_PASS', '')

smtp_secure = os.getenv('SMTP_SECURE', '').lower()
smtp_require_tls = os.getenv('SMTP_REQUIRE_TLS', '').lower()
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', str(smtp_secure == 'true')).lower() == 'true'
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', str(smtp_secure != 'true' and smtp_require_tls == 'true')).lower() == 'true'
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))
DEFAULT_FROM_EMAIL = os.getenv('SMTP_FROM', EMAIL_HOST_USER or 'no-reply@example.com')

FRONTEND_RESET_URL = os.getenv('FRONTEND_RESET_URL', 'https://example.com/reset-password')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')

CITACION_EMAIL_RECIPIENTS_MODE = os.getenv('CITACION_EMAIL_RECIPIENTS_MODE', 'list')
CITACION_EMAIL_RECIPIENTS = os.getenv('CITACION_EMAIL_RECIPIENTS', 'lopez.pablo2305@gmail.com')