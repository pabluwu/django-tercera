from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='bombero', on_delete=models.CASCADE)
    rut = models.CharField(max_length=15)
    fecha_ingreso = models.DateField(null = True)
    telefono = models.IntegerField(null = True)
    contacto = models.IntegerField(null = True)
    imagen = models.ImageField(upload_to ='fotos_perfil/', default='fotos_perfil/user.jpg')

class Citacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=300, null=True)
    fecha = models.DateTimeField(null=True)
    lugar = models.CharField(max_length=100)
    tenida = models.CharField(max_length=100)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre
    
class Licencia(models.Model):
    citacion = models.ForeignKey(Citacion, on_delete=models.CASCADE)
    motivo = models.TextField(max_length=300)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_licencia = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("check_licencias", "Puede revisar todas las licencias"),
        ]

    def __str__(self):
        return self.motivo

class Emergencia(models.Model):
    clave = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    unidades = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Emergencia {self.clave} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
    

class ListaAsistencia(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    evento = GenericForeignKey('content_type', 'object_id')

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Asistencia a {self.content_type.model} #{self.object_id}"

class Asistencia(models.Model):
    lista = models.ForeignKey(ListaAsistencia, on_delete=models.CASCADE, related_name='asistencias')
    bombero = models.ForeignKey(User, on_delete=models.CASCADE)
    asistio = models.BooleanField(default=True)
    hora_llegada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.bombero.email} - {'Presente' if self.asistio else 'Ausente'}"
