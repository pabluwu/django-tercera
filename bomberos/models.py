from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid



class Tenant(models.Model):
    nombre = models.CharField(max_length=100)
    subdominio = models.CharField(max_length=50, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.nombre


class Modulo(models.Model):
    clave = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'

    def __str__(self):
        return self.nombre


class TenantModulo(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='modulos_contratados')
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    fecha_activacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'modulo')
        verbose_name = 'Módulo contratado por Tenant'
        verbose_name_plural = 'Módulos contratados por Tenant'

    def __str__(self):
        return f"{self.tenant.nombre} - {self.modulo.nombre} ({'Activo' if self.is_active else 'Inactivo'})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='bombero', on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, related_name='usuarios', on_delete=models.PROTECT, null=True, blank=True)
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
    is_conductor = models.BooleanField(default=False)

RESPONSABLE_CHOICES = [
    ('director', 'Director'),
    ('capitan', 'Capitán'),
    ('secretario', 'Secretario'),
    ('tesorero', 'Tesorero'),
    ('teniente_1', 'Teniente 1°'),
    ('teniente_2', 'Teniente 2°'),
    ('teniente_3', 'Teniente 3°'),
    ('ayudante', 'Ayudante'),
]

class Citacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=300, null=True)
    fecha = models.DateTimeField(null=True)
    lugar = models.CharField(max_length=100)
    tenida = models.CharField(max_length=100)
    responsable = models.CharField(max_length=50, choices=RESPONSABLE_CHOICES, null=True, blank=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre
    
class Licencia(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    citacion = models.ForeignKey(Citacion, on_delete=models.CASCADE)
    motivo = models.TextField(max_length=300)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_licencia = models.DateTimeField(auto_now_add=True)
    documento = models.FileField(upload_to='licencias/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        permissions = [
            ("check_licencias", "Puede revisar todas las licencias"),
        ]

    def __str__(self):
        return f"{self.motivo} ({self.get_estado_display()})"

class Emergencia(models.Model):
    clave = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    unidades = models.TextField()
    is_declarado = models.BooleanField(default=False)
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


# ==================== INVENTARIO MODELS ====================

class Sala(models.Model):
    """Modelo para representar salas donde se almacenan activos fijos."""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

    def __str__(self):
        return self.nombre

    def delete(self, *args, **kwargs):
        """Soft delete: cambia is_active a False en lugar de eliminar."""
        self.is_active = False
        self.save()


class Item(models.Model):
    """Modelo para representar items/activos fijos."""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    ubicacion_especifica = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    sala = models.ForeignKey(
        Sala,
        on_delete=models.PROTECT,
        related_name='items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"{self.nombre} ({self.cantidad}) - {self.sala.nombre}"

    def delete(self, *args, **kwargs):
        """Soft delete: cambia is_active a False en lugar de eliminar."""
        self.is_active = False
        self.save()


class AccionLogChoices(models.TextChoices):
    CREATE = 'CREATE', 'Creación'
    UPDATE = 'UPDATE', 'Actualización'
    DELETE = 'DELETE', 'Eliminación'
    TRANSFER = 'TRANSFER', 'Transferencia'


class LogInventario(models.Model):
    """Modelo para registrar todas las acciones del inventario."""
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_inventario'
    )
    accion = models.CharField(max_length=20, choices=AccionLogChoices.choices)
    motivo = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    sala_afectada = models.ForeignKey(
        Sala,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    item_afectado = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Inventario'
        verbose_name_plural = 'Logs de Inventario'

    def __str__(self):
        usuario_label = self.usuario.username if self.usuario else "Sistema"
        return f"[{self.accion}] {usuario_label} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"


class TipoExcepcionChoices(models.TextChoices):
    SUSPENDIDO = 'Suspendido', 'Suspendido'
    LICENCIA_CORRIDA = 'Licencia Corrida', 'Licencia Corrida'
    SEPARADO = 'Separado', 'Separado'
    LICENCIA_EXTENDIDA = 'Licencia Extendida', 'Licencia Extendida'


class ExcepcionAsistencia(models.Model):
    """Modelo para establecer excepciones en el cálculo de asistencia."""
    tipo_excepcion = models.CharField(max_length=50, choices=TipoExcepcionChoices.choices)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    motivo = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='excepciones_asistencia')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = 'Excepción de Asistencia'
        verbose_name_plural = 'Excepciones de Asistencia'

    def __str__(self):
        return f"{self.tipo_excepcion} - {self.autor.username} ({self.fecha_inicio.strftime('%Y-%m-%d')} a {self.fecha_fin.strftime('%Y-%m-%d')})"


class Guardia(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='guardias')
    fecha = models.DateField()
    oficial = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='guardias_oficial')
    conductor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='guardias_conductor')
    bomberos = models.ManyToManyField(User, related_name='guardias_bombero')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='guardias_creadas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    es_borrador = models.BooleanField(default=False)

    class Meta:
        unique_together = ('tenant', 'fecha')
        ordering = ['fecha']
        verbose_name = 'Guardia'
        verbose_name_plural = 'Guardias'

    def __str__(self):
        return f"Guardia {self.fecha.strftime('%d/%m/%Y')} - Tenant: {self.tenant.nombre}"


class SolicitudReemplazo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    guardia = models.ForeignKey(Guardia, on_delete=models.CASCADE, related_name='solicitudes_reemplazo')
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_reemplazo_pedidas')
    reemplazo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_reemplazo_recibidas')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Solicitud de Reemplazo'
        verbose_name_plural = 'Solicitudes de Reemplazo'

    def __str__(self):
        return f"Reemplazo {self.guardia.fecha.strftime('%d/%m/%Y')}: {self.solicitante.username} -> {self.reemplazo.username} ({self.estado})"


# ==================== ENCUESTAS Y FORMULARIOS ====================

class Formulario(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='formularios')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_lanzamiento = models.DateTimeField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='formularios_creados')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_lanzamiento', '-creado_en']
        verbose_name = 'Formulario'
        verbose_name_plural = 'Formularios'

    def __str__(self):
        return self.titulo


class FormularioCampo(models.Model):
    TIPO_CAMPO_CHOICES = [
        ('numerico', 'Numérico'),
        ('texto', 'Texto'),
        ('seleccion_multiple', 'Selección Múltiple'),
        ('seleccion_unica', 'Selección Única'),
    ]

    formulario = models.ForeignKey(Formulario, on_delete=models.CASCADE, related_name='campos')
    label = models.CharField(max_length=255)
    tipo_campo = models.CharField(max_length=50, choices=TIPO_CAMPO_CHOICES)
    obligatorio = models.BooleanField(default=True)
    opciones = models.JSONField(default=list, blank=True, help_text="Lista de opciones (array de strings) para selección")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Campo de Formulario'
        verbose_name_plural = 'Campos de Formulario'

    def __str__(self):
        return f"{self.label} ({self.get_tipo_campo_display()})"


class FormularioRespuesta(models.Model):
    formulario = models.ForeignKey(Formulario, on_delete=models.CASCADE, related_name='respuestas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='respuestas_formularios')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('formulario', 'usuario')
        ordering = ['-creado_en']
        verbose_name = 'Respuesta de Formulario'
        verbose_name_plural = 'Respuestas de Formulario'

    def __str__(self):
        return f"Respuesta de {self.usuario.username} a {self.formulario.titulo}"


class FormularioRespuestaValor(models.Model):
    respuesta = models.ForeignKey(FormularioRespuesta, on_delete=models.CASCADE, related_name='valores')
    campo = models.ForeignKey(FormularioCampo, on_delete=models.CASCADE, related_name='respuestas_valores')
    valor = models.JSONField(help_text="Valor ingresado por el usuario (número, texto o array de opciones)")

    class Meta:
        unique_together = ('respuesta', 'campo')
        verbose_name = 'Valor de Respuesta'
        verbose_name_plural = 'Valores de Respuesta'

    def __str__(self):
        return f"Valor para {self.campo.label}: {self.valor}"


class CategoriaSalud(models.TextChoices):
    EXAMENES = 'examenes', 'Exámenes'
    FICHAS_MEDICAS = 'fichas_medicas', 'Fichas Médicas'
    CERTIFICADOS_APTITUD = 'certificados_aptitud', 'Certificados de Aptitud'
    OTROS = 'otros', 'Otros'


class ExpedienteSalud(models.Model):
    bombero = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='expedientes_salud')
    categoria = models.CharField(max_length=50, choices=CategoriaSalud.choices)
    archivo = models.FileField(upload_to='salud/expedientes/')
    fecha_documento = models.DateField()
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expedientes_salud_creados')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_documento', '-creado_en']
        verbose_name = 'Expediente de Salud'
        verbose_name_plural = 'Expedientes de Salud'

    def __str__(self):
        return f"{self.bombero.nombres} - {self.get_categoria_display()} - {self.fecha_documento}"


class ContextoAccidente(models.TextChoices):
    INCENDIO = 'incendio', 'Incendio'
    RESCATE = 'rescate', 'Rescate'
    EJERCICIO = 'ejercicio', 'Ejercicio'
    OTRO = 'otro', 'Otro'


class EstadoAccidente(models.TextChoices):
    ABIERTO = 'abierto', 'Abierto'
    CERRADO = 'cerrado', 'Cerrado'


class Accidente(models.Model):
    bombero = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='accidentes')
    fecha_hora = models.DateTimeField()
    descripcion = models.TextField()
    contexto = models.CharField(max_length=50, choices=ContextoAccidente.choices)
    estado = models.CharField(max_length=20, choices=EstadoAccidente.choices, default=EstadoAccidente.ABIERTO)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='accidentes_creados')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Accidente'
        verbose_name_plural = 'Accidentes'

    def __str__(self):
        return f"Accidente de {self.bombero.nombres} ({self.fecha_hora.date()})"


class MovimientoAccidente(models.Model):
    accidente = models.ForeignKey(Accidente, on_delete=models.CASCADE, related_name='movimientos')
    fecha_hito = models.DateField()
    tipo_accion = models.CharField(max_length=100)
    detalle = models.TextField(blank=True)
    archivo = models.FileField(upload_to='salud/accidentes/', null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='movimientos_creados')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_hito', '-creado_en']
        verbose_name = 'Movimiento de Accidente'
        verbose_name_plural = 'Movimientos de Accidente'

    def __str__(self):
        return f"{self.tipo_accion} - {self.fecha_hito}"


