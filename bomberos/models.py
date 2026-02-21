from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='bombero', on_delete=models.CASCADE)
    rut = models.CharField(max_length=15)
    nombres = models.CharField(max_length=150, blank=True)
    apellido_paterno = models.CharField(max_length=150, blank=True)
    apellido_materno = models.CharField(max_length=150, blank=True)
    cia = models.CharField(max_length=50, blank=True)
    registro = models.CharField(max_length=50, blank=True)
    registro_cia = models.CharField(max_length=50, blank=True)
    codigo_llamado = models.CharField(max_length=50, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    fecha_ingreso = models.DateField(null = True)
    telefono = models.IntegerField(null = True)
    sexo = models.CharField(max_length=30, blank=True)
    nacionalidad = models.CharField(max_length=100, blank=True)
    sangre_grupo = models.CharField(max_length=10, blank=True)
    estado_civil = models.CharField(max_length=50, blank=True)
    profesion = models.CharField(max_length=150, blank=True)
    direccion_calle = models.CharField(max_length=255, blank=True)
    direccion_numero = models.CharField(max_length=20, blank=True)
    direccion_complemento = models.CharField(max_length=255, blank=True)
    direccion_comuna = models.CharField(max_length=100, blank=True)
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

TIPO_CHOICES = [
    ('oficios_direccion', 'Oficios de Dirección'),
    ('oficios_capitania', 'Oficios de Capitanía'),
    ('citaciones_comandancia', 'Citaciones de Comandancia'),
    ('resoluciones_consejo_disciplina', 'Resoluciones Consejo de Disciplina'),
    ('resoluciones_consejo_superior', 'Resoluciones Consejo Superior de Disciplina'),
    ('circulares_escuela', 'Circulares Escuela de Bomberos de Quillota'),
    ('correspondencia_recibida', 'Correspondencia Recibida'),
    ('ordenes_dia_compania', 'Órdenes del Día de Compañía'),
    ('ordenes_dia_comandancia', 'Órdenes del Día de Comandancia'),
    ('informativos_direccion', 'Informativos Dirección'),
    ('guardias_nocturnas', 'Guardias Nocturnas'),
    ('reglamentos', 'Reglamentos'),
]
class Archivo(models.Model):

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='archivos/')
    descripcion = models.TextField(blank=True)

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            (f"can_upload_{tipo[0]}", f"Puede subir {tipo[1]}")
            for tipo in TIPO_CHOICES
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
class MesPago(models.TextChoices):
    ENERO = '01', 'Enero'
    FEBRERO = '02', 'Febrero'
    MARZO = '03', 'Marzo'
    ABRIL = '04', 'Abril'
    MAYO = '05', 'Mayo'
    JUNIO = '06', 'Junio'
    JULIO = '07', 'Julio'
    AGOSTO = '08', 'Agosto'
    SEPTIEMBRE = '09', 'Septiembre'
    OCTUBRE = '10', 'Octubre'
    NOVIEMBRE = '11', 'Noviembre'
    DICIEMBRE = '12', 'Diciembre'
    
class MesAnio(models.Model):
    anio = models.PositiveIntegerField()
    mes = models.CharField(max_length=2, choices=MesPago.choices)

    class Meta:
        unique_together = ('anio', 'mes')
        ordering = ['anio', 'mes']

    def __str__(self):
        return f"{self.get_mes_display()} {self.anio}"
    
class ComprobanteTransferencia(models.Model):
    bombero = models.ForeignKey(User, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='comprobantes_transferencia/')
    fecha_envio = models.DateField(auto_now_add=True)
    meses_pagados = models.ManyToManyField(MesAnio)
    aprobado = models.BooleanField(null=True, default=None)  # None: pendiente
    observacion = models.TextField(blank=True, null=True)
    revisado_por = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='revisiones_transferencias'
    )
    fecha_revision = models.DateTimeField(null=True, blank=True)

class ComprobanteTesorero(models.Model):
    numero_comprobante = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateField(auto_now_add=True)
    tesorero = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comprobantes_emitidos')
    bombero = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos_recibidos')
    meses_pagados = models.ManyToManyField(MesAnio)
    monto_total = models.PositiveIntegerField()
    metodo_pago = models.CharField(max_length=15, choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia')])


class ApiLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=300)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='apilog_created_at_idx'),
            models.Index(fields=['path'], name='apilog_path_idx'),
            models.Index(fields=['status_code'], name='apilog_status_code_idx'),
        ]

    def __str__(self):
        user_label = self.user.username if self.user else "anon"
        return f"[{self.method}] {self.path} ({self.status_code}) - {user_label}"
