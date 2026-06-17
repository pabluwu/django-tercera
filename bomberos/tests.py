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


from bomberos.models import ExpedienteSalud, Accidente, MovimientoAccidente

class SaludYAccidentesAPITests(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(nombre="Cuerpo de Bomberos", subdominio="cb")
        
        # Crear grupos
        self.salud_group = Group.objects.create(name="Encargado de Salud")
        self.bombero_group = Group.objects.create(name="Bombero")

        # Encargado de Salud
        self.encargado_user = User.objects.create_user(
            username="encargado", email="salud@bomberos.cl", password="password123"
        )
        self.encargado_profile = UserProfile.objects.create(
            user=self.encargado_user, tenant=self.tenant, rut="11.111.111-1", cargo="Encargado de Salud"
        )
        self.encargado_user.groups.add(self.salud_group)

        # Bombero
        self.bombero_user = User.objects.create_user(
            username="bombero", email="bombero@bomberos.cl", password="password123"
        )
        self.bombero_profile = UserProfile.objects.create(
            user=self.bombero_user, tenant=self.tenant, rut="22.222.222-2"
        )
        self.bombero_user.groups.add(self.bombero_group)

    def test_acceso_restringido_para_bombero_normal(self):
        """Un bombero normal no debe poder listar expedientes ni accidentes (403)."""
        self.client.force_authenticate(user=self.bombero_user)
        
        response = self.client.get('/api/salud/expedientes/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.get('/api/salud/accidentes/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_acceso_concedido_para_encargado_salud(self):
        """El Encargado de Salud debe poder listar expedientes y accidentes (200)."""
        self.client.force_authenticate(user=self.encargado_user)
        
        response = self.client.get('/api/salud/expedientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/salud/accidentes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_creacion_expediente_salud_con_archivo(self):
        """El Encargado de Salud puede subir expedientes médicos."""
        self.client.force_authenticate(user=self.encargado_user)
        
        # Creamos un archivo dummy en memoria
        from django.core.files.uploadedfile import SimpleUploadedFile
        archivo_test = SimpleUploadedFile("examen.pdf", b"pdf content", content_type="application/pdf")
        
        payload = {
            "bombero": self.bombero_profile.id,
            "categoria": "examenes",
            "archivo": archivo_test,
            "fecha_documento": "2026-06-13",
            "observaciones": "Examen de sangre preventivo"
        }
        
        response = self.client.post('/api/salud/expedientes/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExpedienteSalud.objects.count(), 1)
        
        expediente = ExpedienteSalud.objects.first()
        self.assertEqual(expediente.creado_por, self.encargado_user)
        self.assertEqual(expediente.categoria, "examenes")

    def test_creacion_accidente_y_movimiento(self):
        """El Encargado de Salud puede registrar accidentes e hitos médicos."""
        self.client.force_authenticate(user=self.encargado_user)
        
        payload_accidente = {
            "bombero": self.bombero_profile.id,
            "fecha_hora": "2026-06-13T10:00:00Z",
            "descripcion": "Esguince de tobillo en acto de servicio",
            "contexto": "incendio"
        }
        
        response = self.client.post('/api/salud/accidentes/', payload_accidente, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Accidente.objects.count(), 1)
        
        accidente = Accidente.objects.first()
        self.assertEqual(accidente.estado, "abierto")
        
        # Registrar un movimiento (sin archivo, hito opcional)
        payload_movimiento = {
            "accidente": accidente.id,
            "fecha_hito": "2026-06-13",
            "tipo_accion": "Derivación a centro médico",
            "detalle": "Traslado en ambulancia institucional"
        }
        
        response = self.client.post('/api/salud/movimientos/', payload_movimiento, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MovimientoAccidente.objects.count(), 1)
        
        movimiento = MovimientoAccidente.objects.first()
        self.assertFalse(bool(movimiento.archivo))  # sin archivo


from django.core.files.uploadedfile import SimpleUploadedFile
from bomberos.models import Citacion, Licencia

class LicenciasAPITests(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(nombre="Cuerpo de Bomberos", subdominio="cb")
        
        # Crear grupos
        self.oficial_group = Group.objects.create(name="Ayudante")
        self.bombero_group = Group.objects.create(name="Bombero")

        # Usuarios
        self.oficial_user = User.objects.create_user(
            username="oficial_lic", email="oficial_lic@bomberos.cl", password="password123"
        )
        self.oficial_profile = UserProfile.objects.create(
            user=self.oficial_user, tenant=self.tenant, rut="11.111.111-1"
        )
        self.oficial_user.groups.add(self.oficial_group)

        self.bombero_user = User.objects.create_user(
            username="bombero_lic", email="bombero_lic@bomberos.cl", password="password123"
        )
        self.bombero_profile = UserProfile.objects.create(
            user=self.bombero_user, tenant=self.tenant, rut="22.222.222-2"
        )
        self.bombero_user.groups.add(self.bombero_group)

        # Crear Citacion (en el futuro > 24 horas para que sea válida la creación de licencias)
        self.citacion = Citacion.objects.create(
            nombre="Citación de Prueba",
            lugar="Cuartel",
            tenida="Uniforme",
            fecha=timezone.now() + timedelta(days=2),
            autor=self.oficial_user
        )

    def test_crear_licencia_con_documento_valido(self):
        """Crear una licencia con un documento válido de menos de 500 KB."""
        self.client.force_authenticate(user=self.bombero_user)
        archivo_valido = SimpleUploadedFile("certificado.pdf", b"a" * 1024, content_type="application/pdf")
        
        payload = {
            "citacion": self.citacion.id,
            "motivo": "Ausencia médica",
            "autor": self.bombero_user.id,
            "documento": archivo_valido
        }
        
        response = self.client.post('/api/licencias/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Licencia.objects.count(), 1)
        
        licencia = Licencia.objects.first()
        self.assertEqual(licencia.estado, 'pendiente')
        self.assertTrue(bool(licencia.documento))

    def test_crear_licencia_con_documento_excede_limite(self):
        """Crear una licencia con un documento que pesa más de 500 KB debe fallar."""
        self.client.force_authenticate(user=self.bombero_user)
        # 501 KB
        archivo_grande = SimpleUploadedFile("certificado_grande.pdf", b"a" * (501 * 1024), content_type="application/pdf")
        
        payload = {
            "citacion": self.citacion.id,
            "motivo": "Ausencia médica",
            "autor": self.bombero_user.id,
            "documento": archivo_grande
        }
        
        response = self.client.post('/api/licencias/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("El documento no debe superar los 500 KB", str(response.data))

    def test_no_dos_licencias_activas_para_misma_citacion(self):
        """Un usuario no puede tener dos solicitudes de licencia activas (pendientes/aceptadas) para la misma citación."""
        self.client.force_authenticate(user=self.bombero_user)
        
        # Primera licencia (pendiente)
        Licencia.objects.create(
            citacion=self.citacion,
            motivo="Primera",
            autor=self.bombero_user,
            estado='pendiente'
        )
        
        # Intento de crear otra
        payload = {
            "citacion": self.citacion.id,
            "autor": self.bombero_user.id,
            "motivo": "Segunda"
        }
        response = self.client.post('/api/licencias/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ya tienes una solicitud de licencia pendiente o aceptada", str(response.data))

    def test_si_rechazada_puede_enviar_otra(self):
        """Si la licencia previa es rechazada, se permite solicitar una nueva para la misma citación."""
        self.client.force_authenticate(user=self.bombero_user)
        
        # Crear una rechazada
        Licencia.objects.create(
            citacion=self.citacion,
            motivo="Rechazada previamente",
            autor=self.bombero_user,
            estado='rechazada'
        )
        
        # Crear una nueva
        payload = {
            "citacion": self.citacion.id,
            "autor": self.bombero_user.id,
            "motivo": "Nueva solicitud"
        }
        response = self.client.post('/api/licencias/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Licencia.objects.filter(citacion=self.citacion, autor=self.bombero_user).count(), 2)

    def test_oficial_puede_aceptar_o_rechazar_licencia(self):
        """Un oficial de la compañía puede aceptar y rechazar una licencia."""
        licencia = Licencia.objects.create(
            citacion=self.citacion,
            motivo="Ausencia",
            autor=self.bombero_user,
            estado='pendiente'
        )
        
        # Aceptar por oficial
        self.client.force_authenticate(user=self.oficial_user)
        response = self.client.patch(f'/api/licencias/{licencia.id}/aceptar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        licencia.refresh_from_db()
        self.assertEqual(licencia.estado, 'aceptada')
        
        # Rechazar por oficial
        response = self.client.patch(f'/api/licencias/{licencia.id}/rechazar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        licencia.refresh_from_db()
        self.assertEqual(licencia.estado, 'rechazada')

    def test_auto_aceptar_licencias_pasadas(self):
        """Verificar que las licencias pendientes de citaciones en el pasado se auto-acepten al consultar."""
        citacion_pasada = Citacion.objects.create(
            nombre="Citación Pasada",
            lugar="Cuartel",
            tenida="Uniforme",
            fecha=timezone.now() - timedelta(days=1),
            autor=self.oficial_user
        )
        
        licencia_pasada = Licencia.objects.create(
            citacion=citacion_pasada,
            motivo="Falta antigua",
            autor=self.bombero_user,
            estado='pendiente'
        )
        
        self.client.force_authenticate(user=self.bombero_user)
        # Consultar las licencias (esto debe disparar la auto-aceptación)
        response = self.client.get('/api/licencias/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        licencia_pasada.refresh_from_db()
        self.assertEqual(licencia_pasada.estado, 'aceptada')
