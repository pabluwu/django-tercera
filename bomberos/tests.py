from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta
import uuid

from bomberos.models import (
    Tenant, UserProfile, Formulario, FormularioCampo, 
    FormularioRespuesta, FormularioRespuestaValor
)

class EncuestasAPITests(APITestCase):

    def setUp(self):
        # 1. Crear Tenant
        self.tenant = Tenant.objects.create(nombre="Tercera Compañía", subdominio="tercera")

        # 2. Crear Grupos
        self.oficial_group = Group.objects.create(name="Ayudante")
        self.bombero_group = Group.objects.create(name="Bombero")

        # 3. Crear Usuarios
        self.oficial_user = User.objects.create_user(
            username="oficial", email="oficial@bomberos.cl", password="password123"
        )
        self.oficial_profile = UserProfile.objects.create(
            user=self.oficial_user, tenant=self.tenant, rut="11.111.111-1"
        )
        self.oficial_user.groups.add(self.oficial_group)

        self.bombero_user = User.objects.create_user(
            username="bombero", email="bombero@bomberos.cl", password="password123"
        )
        self.bombero_profile = UserProfile.objects.create(
            user=self.bombero_user, tenant=self.tenant, rut="22.222.222-2"
        )
        self.bombero_user.groups.add(self.bombero_group)

        # 4. Crear Formulario de prueba (activo)
        self.ahora = timezone.now()
        self.formulario_activo = Formulario.objects.create(
            tenant=self.tenant,
            titulo="Encuesta Activa",
            descripcion="Descripción de prueba",
            fecha_lanzamiento=self.ahora - timedelta(hours=1),
            fecha_inicio=self.ahora - timedelta(hours=1),
            fecha_fin=self.ahora + timedelta(days=2),
            creado_por=self.oficial_user
        )
        
        # Campos de prueba
        self.campo_texto = FormularioCampo.objects.create(
            formulario=self.formulario_activo,
            label="¿Tu nombre?",
            tipo_campo="texto",
            obligatorio=True,
            orden=0
        )
        self.campo_num = FormularioCampo.objects.create(
            formulario=self.formulario_activo,
            label="¿Tu edad?",
            tipo_campo="numerico",
            obligatorio=False,
            orden=1
        )
        self.campo_unica = FormularioCampo.objects.create(
            formulario=self.formulario_activo,
            label="¿Talla de uniforme?",
            tipo_campo="seleccion_unica",
            obligatorio=True,
            opciones=["S", "M", "L"],
            orden=2
        )

        # 5. Crear Formulario no lanzado (programado para el futuro)
        self.formulario_programado = Formulario.objects.create(
            tenant=self.tenant,
            titulo="Encuesta Futura",
            fecha_lanzamiento=self.ahora + timedelta(days=1),
            fecha_inicio=self.ahora + timedelta(days=1),
            creado_por=self.oficial_user
        )

    def test_creacion_formulario_por_oficial(self):
        """Un oficial de la compañía debería poder crear una encuesta con sus campos."""
        self.client.force_authenticate(user=self.oficial_user)
        
        url = reverse('formulario-list')
        payload = {
            "titulo": "Nueva Encuesta Oficial",
            "descripcion": "Descripción",
            "fecha_lanzamiento": (self.ahora + timedelta(hours=1)).isoformat(),
            "fecha_inicio": (self.ahora + timedelta(hours=1)).isoformat(),
            "campos": [
                {
                    "label": "Pregunta de Texto",
                    "tipo_campo": "texto",
                    "obligatorio": True
                },
                {
                    "label": "Pregunta Selección Única",
                    "tipo_campo": "seleccion_unica",
                    "obligatorio": False,
                    "opciones": ["Opción 1", "Opción 2"]
                }
            ]
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Formulario.objects.filter(titulo="Nueva Encuesta Oficial").count(), 1)
        
        formulario_creado = Formulario.objects.get(titulo="Nueva Encuesta Oficial")
        self.assertEqual(formulario_creado.campos.count(), 2)

    def test_creacion_formulario_denegado_para_bombero(self):
        """Un bombero común (no oficial) no debería poder crear formularios."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-list')
        payload = {
            "titulo": "Encuesta de Bombero",
            "fecha_lanzamiento": self.ahora.isoformat(),
            "fecha_inicio": self.ahora.isoformat(),
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_obtener_formulario_por_uuid_anonimo_denegado(self):
        """Un usuario no autenticado no puede obtener el formulario por su UUID."""
        url = reverse('formulario-get-by-uuid', kwargs={'uuid': self.formulario_activo.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtener_formulario_por_uuid_autenticado(self):
        """Cualquier usuario autenticado puede obtener la estructura de la encuesta por su UUID."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-get-by-uuid', kwargs={'uuid': self.formulario_activo.uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], self.formulario_activo.titulo)
        self.assertEqual(len(response.data['campos']), 3)

    def test_obtener_formulario_programado_denegado_para_bombero(self):
        """Un bombero común no puede ver la estructura de una encuesta no lanzada aún."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-get-by-uuid', kwargs={'uuid': self.formulario_programado.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_responder_encuesta_exito(self):
        """Un usuario registrado puede responder a una encuesta activa."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-respuesta-list')
        payload = {
            "formulario": self.formulario_activo.id,
            "valores": [
                {"campo": self.campo_texto.id, "valor": "Mi Respuesta de Texto"},
                {"campo": self.campo_num.id, "valor": 30},
                {"campo": self.campo_unica.id, "valor": "M"}
            ]
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FormularioRespuesta.objects.filter(formulario=self.formulario_activo, usuario=self.bombero_user).count(), 1)
        
        # Validar valores grabados
        resp = FormularioRespuesta.objects.get(formulario=self.formulario_activo, usuario=self.bombero_user)
        self.assertEqual(resp.valores.count(), 3)
        self.assertEqual(resp.valores.get(campo=self.campo_texto).valor, "Mi Respuesta de Texto")

    def test_responder_dos_veces_denegado(self):
        """Un usuario no puede responder la misma encuesta dos veces."""
        self.client.force_authenticate(user=self.bombero_user)
        
        # Primera respuesta
        FormularioRespuesta.objects.create(formulario=self.formulario_activo, usuario=self.bombero_user)
        
        url = reverse('formulario-respuesta-list')
        payload = {
            "formulario": self.formulario_activo.id,
            "valores": [
                {"campo": self.campo_texto.id, "valor": "Nueva Respuesta"},
                {"campo": self.campo_unica.id, "valor": "S"}
            ]
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ya has respondido a este formulario", str(response.data))

    def test_responder_campo_obligatorio_vacio_denegado(self):
        """No se puede enviar si falta un campo obligatorio."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-respuesta-list')
        # campo_unica es obligatorio, lo omitimos en el payload
        payload = {
            "formulario": self.formulario_activo.id,
            "valores": [
                {"campo": self.campo_texto.id, "valor": "Juan"}
            ]
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("es obligatorio", str(response.data))

    def test_responder_tipo_numerico_invalido_denegado(self):
        """No se puede enviar un texto en un campo de tipo numérico."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-respuesta-list')
        payload = {
            "formulario": self.formulario_activo.id,
            "valores": [
                {"campo": self.campo_texto.id, "valor": "Juan"},
                {"campo": self.campo_num.id, "valor": "no-es-numero"},
                {"campo": self.campo_unica.id, "valor": "S"}
            ]
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("debe ser numérico", str(response.data))

    def test_responder_opcion_invalida_denegado(self):
        """No se puede enviar una opción que no esté configurada en las opciones del campo."""
        self.client.force_authenticate(user=self.bombero_user)
        
        url = reverse('formulario-respuesta-list')
        payload = {
            "formulario": self.formulario_activo.id,
            "valores": [
                {"campo": self.campo_texto.id, "valor": "Juan"},
                {"campo": self.campo_unica.id, "valor": "XL"} # XL no está en ["S", "M", "L"]
            ]
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no es una opción válida", str(response.data))
