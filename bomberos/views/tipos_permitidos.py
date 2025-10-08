# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # asegúrate de importar correctamente
from ..models import TIPO_CHOICES

class TiposPermitidosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print('hola')
        user = request.user
        tipos_permitidos = []

        for codename, label in TIPO_CHOICES:
            perm = f"bomberos.can_upload_{codename}"  # reemplaza `app_label` por el nombre real de tu app
            if user.has_perm(perm):
                tipos_permitidos.append({ "value": codename, "label": label })

        return Response(tipos_permitidos)
