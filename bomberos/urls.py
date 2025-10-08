from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, CitacionViewSet, LicenciaViewSet, ListaAsistenciaViewSet, EmergenciaViewSet, ArchivoViewSet
from .views.user import me_view
from .views.tipos_permitidos import TiposPermitidosView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import ComprobanteTransferenciaViewSet, ComprobanteTesoreroViewSet, MesAnioViewSet

router = DefaultRouter()
router.register(r'perfiles', UserProfileViewSet)
router.register(r'citaciones', CitacionViewSet)
router.register(r'licencias', LicenciaViewSet)
router.register(r'emergencias', EmergenciaViewSet)
router.register(r'listas-asistencia', ListaAsistenciaViewSet)
router.register(r'archivos', ArchivoViewSet)
router.register(r'meses-anio', MesAnioViewSet)
router.register(r'comprobantes/transferencia', ComprobanteTransferenciaViewSet, basename='comprobante-transferencia')
router.register(r'comprobantes/tesorero', ComprobanteTesoreroViewSet, basename='comprobante-tesorero')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # renovar
    path('me/', me_view, name='me'),
    path('archivo/tipos-permitidos/', TiposPermitidosView.as_view(), name='tipos_permitidos'), 
]
