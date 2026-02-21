# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # asegúrate de importar correctamente
from ..models import TIPO_CHOICES

class TiposPermitidosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos_permitidos = []
        for codename, label in TIPO_CHOICES:
            tipos_permitidos.append({"value": codename, "label": label})

        return Response(tipos_permitidos)
