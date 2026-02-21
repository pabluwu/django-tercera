from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, CitacionViewSet, LicenciaViewSet, ListaAsistenciaViewSet, EmergenciaViewSet, ArchivoViewSet
from .views.user import me_view
from .views.tipos_permitidos import TiposPermitidosView
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth import RutTokenObtainPairView, PasswordResetRequestView, PasswordResetConfirmView

from .views import (
    ComprobanteTransferenciaViewSet,
    ComprobanteTesoreroViewSet,
    MesAnioViewSet,
    ResumenCuotasViewSet,
    AsistenciaResumenViewSet,
    UsuarioAsistenciaResumenView,
    AsistenciaAnualGlobalView,
    AsistenciaEmergenciaResumenViewSet,
)

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
router.register(r'tesoreria/resumen-cuotas', ResumenCuotasViewSet, basename='tesoreria-resumen-cuotas')
router.register(r'asistencia/resumen', AsistenciaResumenViewSet, basename='asistencia-resumen')
router.register(r'asistencia/usuario', UsuarioAsistenciaResumenView, basename='asistencia-usuario-resumen')
router.register(r'asistencia/anual', AsistenciaAnualGlobalView, basename='asistencia-anual-resumen')
router.register(r'asistencia/emergencia', AsistenciaEmergenciaResumenViewSet, basename='asistencia-emergencia-resumen')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', RutTokenObtainPairView.as_view(), name='token_obtain_pair'),  # login por RUT
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # renovar
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('me/', me_view, name='me'),
    path('archivo/tipos-permitidos/', TiposPermitidosView.as_view(), name='tipos_permitidos'), 
]
