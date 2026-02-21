from rest_framework import serializers


class UsuarioBasicoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)


class AsistenciaDetalleSerializer(UsuarioBasicoSerializer):
    asistio = serializers.BooleanField()
    hora_llegada = serializers.DateTimeField(allow_null=True)


class LicenciaDetalleSerializer(UsuarioBasicoSerializer):
    motivo = serializers.CharField()
    fecha_licencia = serializers.DateTimeField()


class TotalesSerializer(serializers.Serializer):
    asistentes = serializers.IntegerField()
    licencias = serializers.IntegerField()
    inasistencias = serializers.IntegerField()
    registrados = serializers.IntegerField()


class PorcentajesSerializer(serializers.Serializer):
    asistentes = serializers.FloatField()
    licencias = serializers.FloatField()
    inasistencias = serializers.FloatField()


class CitacionResumenSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField(allow_null=True, allow_blank=True)
    fecha = serializers.DateTimeField()
    lugar = serializers.CharField()
    tenida = serializers.CharField()


class AsistenciaResumenSerializer(serializers.Serializer):
    citacion = CitacionResumenSerializer()
    asistentes = AsistenciaDetalleSerializer(many=True)
    licencias = LicenciaDetalleSerializer(many=True)
    inasistentes = UsuarioBasicoSerializer(many=True)
    totales = TotalesSerializer()
    porcentajes = PorcentajesSerializer()


class UsuarioResumenAnualSerializer(serializers.Serializer):
    usuario = UsuarioBasicoSerializer()
    anio = serializers.IntegerField()
    total_citaciones = serializers.IntegerField()
    total_emergencias = serializers.IntegerField()
    total_listas = serializers.IntegerField()
    asistencias = serializers.IntegerField()
    licencias = serializers.IntegerField()
    inasistencias = serializers.IntegerField()


class AsistenciaAnualGlobalSerializer(serializers.Serializer):
    anio = serializers.IntegerField()
    total_citaciones = serializers.IntegerField()
    total_emergencias = serializers.IntegerField()
    total_listas = serializers.IntegerField()
    total_bomberos = serializers.IntegerField()
    total_posibles = serializers.IntegerField()
    totales = TotalesSerializer()
    porcentajes = PorcentajesSerializer()


class EmergenciaResumenSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    clave = serializers.CharField()
    fecha = serializers.DateTimeField()
    unidades = serializers.CharField()


class AsistenciaEmergenciaResumenSerializer(serializers.Serializer):
    emergencia = EmergenciaResumenSerializer()
    asistentes = AsistenciaDetalleSerializer(many=True)
    inasistentes = UsuarioBasicoSerializer(many=True)
    totales = TotalesSerializer()
    porcentajes = PorcentajesSerializer()
