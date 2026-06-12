from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import Formulario, FormularioCampo, FormularioRespuesta, FormularioRespuestaValor
from ..permissions import IsOficial
from ..serializers.encuesta import FormularioSerializer, FormularioRespuestaSerializer

class FormularioViewSet(viewsets.ModelViewSet):
    serializer_class = FormularioSerializer
    queryset = Formulario.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'resultados']:
            return [IsAuthenticated(), IsOficial()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'bombero', None)
        if not profile or not profile.tenant:
            return Formulario.objects.none()
        
        is_oficial_perm = IsOficial()
        qs = Formulario.objects.filter(tenant=profile.tenant)
        
        # Si no es oficial, solo ver encuestas que ya estén lanzadas
        if not is_oficial_perm.has_permission(self.request, self):
            ahora = timezone.now()
            qs = qs.filter(fecha_lanzamiento__lte=ahora)
            
        return qs

    def perform_create(self, serializer):
        profile = self.request.user.bombero
        serializer.save(tenant=profile.tenant, creado_por=self.request.user)

    @action(detail=False, methods=['get'], url_path='uuid/(?P<uuid>[^/.]+)')
    def get_by_uuid(self, request, uuid=None):
        profile = getattr(request.user, 'bombero', None)
        if not profile or not profile.tenant:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)
            
        formulario = get_object_or_404(Formulario, uuid=uuid, tenant=profile.tenant)
        
        is_oficial_perm = IsOficial()
        # Si no es oficial y aún no se lanza, denegar acceso
        if not is_oficial_perm.has_permission(request, self):
            if formulario.fecha_lanzamiento > timezone.now():
                return Response({"detail": "Este formulario aún no está disponible."}, status=status.HTTP_403_FORBIDDEN)
                
        serializer = self.get_serializer(formulario)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='resultados')
    def resultados(self, request, pk=None):
        formulario = self.get_object()
        respuestas = formulario.respuestas.all()
        total_respuestas = respuestas.count()
        
        campos_stats = []
        for campo in formulario.campos.all():
            valores_campo = FormularioRespuestaValor.objects.filter(campo=campo).values_list('valor', flat=True)
            
            stats = {
                "id": campo.id,
                "label": campo.label,
                "tipo_campo": campo.tipo_campo,
                "obligatorio": campo.obligatorio,
                "opciones": campo.opciones,
            }
            
            if campo.tipo_campo == 'numerico':
                numeros = []
                for v in valores_campo:
                    try:
                        if v is not None and v != '':
                            numeros.append(float(v))
                    except (ValueError, TypeError):
                        pass
                
                stats["stats"] = {
                    "promedio": sum(numeros) / len(numeros) if numeros else 0,
                    "min": min(numeros) if numeros else 0,
                    "max": max(numeros) if numeros else 0,
                    "total_respuestas_validas": len(numeros)
                }
            
            elif campo.tipo_campo in ('seleccion_unica', 'seleccion_multiple'):
                frecuencias = {opcion: 0 for opcion in campo.opciones}
                total_selecciones = 0
                
                for v in valores_campo:
                    if isinstance(v, list):
                        for opt in v:
                            if opt in frecuencias:
                                frecuencias[opt] += 1
                                total_selecciones += 1
                    else:
                        if v in frecuencias:
                            frecuencias[v] += 1
                            total_selecciones += 1
                             
                stats["stats"] = {
                    "frecuencias": frecuencias,
                    "total_selecciones": total_selecciones
                }
                
            elif campo.tipo_campo == 'texto':
                respuestas_texto = [v for v in valores_campo if v is not None and v != '']
                stats["stats"] = {
                    "respuestas": respuestas_texto[:100]
                }
                
            campos_stats.append(stats)
            
        respuestas_list = []
        for resp in respuestas:
            valores_dict = {val.campo_id: val.valor for val in resp.valores.all()}
            respuestas_list.append({
                "id": resp.id,
                "usuario_id": resp.usuario.id,
                "usuario_nombre": resp.usuario.get_full_name() or resp.usuario.username,
                "usuario_rut": getattr(resp.usuario.bombero, 'rut', ''),
                "fecha": resp.creado_en,
                "respuestas": valores_dict
            })
            
        return Response({
            "formulario_id": formulario.id,
            "formulario_titulo": formulario.titulo,
            "total_respuestas": total_respuestas,
            "estadisticas": campos_stats,
            "respuestas_individuales": respuestas_list
        })


class FormularioRespuestaViewSet(mixins.CreateModelMixin,
                                 mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin,
                                 viewsets.GenericViewSet):
    serializer_class = FormularioRespuestaSerializer
    queryset = FormularioRespuesta.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), IsOficial()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'bombero', None)
        if not profile or not profile.tenant:
            return FormularioRespuesta.objects.none()
        
        return FormularioRespuesta.objects.filter(formulario__tenant=profile.tenant)
