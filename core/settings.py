from pathlib import Path
from datetime import timedelta
import os
import dj_database_url # <--- Asegúrate de tenerlo en requirements.txt

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga de .env (se mantiene igual para local)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# --- CONFIGURACIÓN DE SEGURIDAD ---
# En Render, usaremos la variable de entorno. En local, la que ya tenías.
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-%g-!cf+4-(mc94tz$^a%py76mij$l%6vteb^$mn26-(@k6-zdx')

# DEBUG será False si estamos en Render (porque RENDER_EXTERNAL_HOSTNAME existirá)
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = []
render_external_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname:
    ALLOWED_HOSTS.append(render_external_hostname)
else:
    ALLOWED_HOSTS.append('localhost')
    ALLOWED_HOSTS.append('127.0.0.1')

# --- APPS Y MIDDLEWARE ---
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # <--- Nuevo: Para estáticos
    'django.contrib.staticfiles',
    'rest_framework',
    'bomberos',
    'django_filters',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- Nuevo: Debe ir aquí
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ApiLogMiddleware',
]

# --- BASE DE DATOS (EL CAMBIO CLAVE) ---
if os.getenv('DATABASE_URL'):
    # Si existe DATABASE_URL (en Render), la usamos
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True # Aiven requiere SSL
        )
    }
else:
    # Si no (en tu local), usamos tu MySQL de siempre
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

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Esta línea permite que WhiteNoise comprima los archivos para que pesen menos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- EL RESTO DE TU CONFIGURACIÓN SE MANTIENE IGUAL ---
# (CORS, REST_FRAMEWORK, SIMPLE_JWT, EMAIL, etc.)
# ...