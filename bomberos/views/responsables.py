from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import RESPONSABLE_CHOICES

class ResponsablesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        responsables = [{"value": codename, "label": label} for codename, label in RESPONSABLE_CHOICES]
        return Response(responsables)
