from collections import OrderedDict, defaultdict

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Citacion, Emergencia, ListaAsistencia, Licencia, UserProfile
from ..serializers.asistencia import (
    AsistenciaResumenSerializer,
    UsuarioResumenAnualSerializer,
    AsistenciaAnualGlobalSerializer,
    AsistenciaEmergenciaResumenSerializer,
)


class AsistenciaResumenViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        year_param = request.query_params.get('anio')
        year = None
        if year_param is not None:
            try:
                year = int(year_param)
            except ValueError:
                return Response(
                    {"detail": "Parámetro 'anio' inválido."},
                    status=400,
                )

        citacion = get_object_or_404(Citacion.objects.select_related('autor'), pk=pk)

        if year is not None and citacion.fecha.year != year:
            return Response(
                {"detail": "La citación no corresponde al año solicitado."},
                status=404,
            )

        content_type = ContentType.objects.get_for_model(Citacion)
        lista = (
            ListaAsistencia.objects.filter(
                content_type=content_type,
                object_id=citacion.id,
            )
            .prefetch_related('asistencias__bombero')
            .first()
        )

        if not lista:
            return Response(
                {"detail": "La citación no tiene una lista de asistencia asociada."},
                status=404,
            )

        asistencias = list(lista.asistencias.all())

        licencias_qs = (
            Licencia.objects.filter(citacion=citacion)
            .select_related('autor')
            .order_by('fecha_licencia')
        )

        all_users_qs = User.objects.all().order_by('id')
        user_map = {user.id: user for user in all_users_qs}
        total_registrados = len(user_map)

        asistentes_data = []
        asistentes_ids = set()
        inasistencias_registradas_ids = set()

        for asistencia in asistencias:
            bombero = asistencia.bombero
            asistentes_data.append(OrderedDict([
                ('id', bombero.id),
                ('email', bombero.email),
                ('first_name', bombero.first_name),
                ('last_name', bombero.last_name),
                ('asistio', asistencia.asistio),
                ('hora_llegada', asistencia.hora_llegada),
            ]))

            if asistencia.asistio:
                asistentes_ids.add(bombero.id)
            else:
                inasistencias_registradas_ids.add(bombero.id)

        licencias_data = []
        licencias_ids = set()

        for licencia in licencias_qs:
            autor = licencia.autor
            if autor.id in asistentes_ids:
                continue
            licencias_data.append(OrderedDict([
                ('id', autor.id),
                ('email', autor.email),
                ('first_name', autor.first_name),
                ('last_name', autor.last_name),
                ('motivo', licencia.motivo),
                ('fecha_licencia', licencia.fecha_licencia),
            ]))
            licencias_ids.add(autor.id)

        inasistentes_ids = set(inasistencias_registradas_ids)

        if total_registrados:
            inasistentes_ids.update(
                set(user_map.keys())
                - asistentes_ids
                - licencias_ids
                - inasistencias_registradas_ids
            )

        inasistentes_data = [
            OrderedDict([
                ('id', user.id),
                ('email', user.email),
                ('first_name', user.first_name),
                ('last_name', user.last_name),
            ])
            for user_id, user in user_map.items()
            if user_id in inasistentes_ids
        ]

        total_asistencias = len(asistentes_ids)
        total_licencias = len(licencias_ids)
        total_inasistencias = len(inasistentes_ids)

        if total_registrados > 0:
            porcentaje_asistencias = round((total_asistencias / total_registrados) * 100, 2)
            porcentaje_licencias = round((total_licencias / total_registrados) * 100, 2)
            porcentaje_inasistencias = round((total_inasistencias / total_registrados) * 100, 2)
        else:
            porcentaje_asistencias = porcentaje_licencias = porcentaje_inasistencias = 0.0

        data = {
            'citacion': {
                'id': citacion.id,
                'nombre': citacion.nombre,
                'descripcion': citacion.descripcion,
                'fecha': citacion.fecha,
                'lugar': citacion.lugar,
                'tenida': citacion.tenida,
            },
            'asistentes': asistentes_data,
            'licencias': licencias_data,
            'inasistentes': inasistentes_data,
            'totales': {
                'asistentes': total_asistencias,
                'licencias': total_licencias,
                'inasistencias': total_inasistencias,
                'registrados': total_registrados,
            },
            'porcentajes': {
                'asistentes': porcentaje_asistencias,
                'licencias': porcentaje_licencias,
                'inasistencias': porcentaje_inasistencias,
            },
        }

        serializer = AsistenciaResumenSerializer(data)
        return Response(serializer.data)


class UsuarioAsistenciaResumenView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        year_param = request.query_params.get('anio')
        if year_param is None:
            return Response(
                {"detail": "Debe proporcionar el parámetro 'anio'."},
                status=400,
            )
        try:
            year = int(year_param)
        except ValueError:
            return Response(
                {"detail": "Parámetro 'anio' inválido."},
                status=400,
            )

        ct_citacion = ContentType.objects.get_for_model(Citacion)
        ct_emergencia = ContentType.objects.get_for_model(Emergencia)

        citaciones_ids = list(
            Citacion.objects.filter(fecha__year=year).values_list('id', flat=True)
        )
        emergencias_ids = list(
            Emergencia.objects.filter(fecha__year=year).values_list('id', flat=True)
        )

        listas_citacion = list(
            ListaAsistencia.objects.filter(
                content_type=ct_citacion,
                object_id__in=citaciones_ids,
            ).prefetch_related('asistencias__bombero')
        )

        listas_emergencia = list(
            ListaAsistencia.objects.filter(
                content_type=ct_emergencia,
                object_id__in=emergencias_ids,
            ).prefetch_related('asistencias__bombero')
        )

        citaciones_con_lista_ids = {lista.object_id for lista in listas_citacion}
        emergencias_con_lista_ids = {lista.object_id for lista in listas_emergencia}

        total_citaciones_con_lista = len(citaciones_con_lista_ids)
        total_emergencias_con_lista = len(emergencias_con_lista_ids)
        total_listas = total_citaciones_con_lista + total_emergencias_con_lista

        if total_listas == 0:
            data = {
                'usuario': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'anio': year,
                'total_citaciones': 0,
                'total_emergencias': 0,
                'total_listas': 0,
                'asistencias': 0,
                'licencias': 0,
                'inasistencias': 0,
            }
            serializer = UsuarioResumenAnualSerializer(data)
            return Response(serializer.data)

        asistencias_citaciones = 0
        licencias_count = 0
        inasistencias_citaciones = 0

        licencias_ids = set(
            Licencia.objects.filter(
                citacion_id__in=citaciones_con_lista_ids,
                citacion__fecha__year=year,
                autor=user,
            ).values_list('citacion_id', flat=True)
        )

        for lista in listas_citacion:
            citacion_id = lista.object_id
            registros = [
                asistencia
                for asistencia in lista.asistencias.all()
                if asistencia.bombero_id == user.id
            ]

            if any(reg.asistio for reg in registros):
                asistencias_citaciones += 1
                continue

            if citacion_id in licencias_ids:
                licencias_count += 1
                continue

            inasistencias_citaciones += 1

        asistencias_emergencias = 0
        inasistencias_emergencias = 0

        for lista in listas_emergencia:
            registros = [
                asistencia
                for asistencia in lista.asistencias.all()
                if asistencia.bombero_id == user.id
            ]

            if any(reg.asistio for reg in registros):
                asistencias_emergencias += 1
            else:
                inasistencias_emergencias += 1

        data = {
            'usuario': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'anio': year,
            'total_citaciones': total_citaciones_con_lista,
            'total_emergencias': total_emergencias_con_lista,
            'total_listas': total_listas,
            'asistencias': asistencias_citaciones + asistencias_emergencias,
            'licencias': licencias_count,
            'inasistencias': inasistencias_citaciones + inasistencias_emergencias,
        }

        serializer = UsuarioResumenAnualSerializer(data)
        return Response(serializer.data)


class AsistenciaAnualGlobalView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        year_param = request.query_params.get('anio')
        if year_param is None:
            return Response(
                {"detail": "Debe proporcionar el parámetro 'anio'."},
                status=400,
            )
        try:
            year = int(year_param)
        except ValueError:
            return Response(
                {"detail": "Parámetro 'anio' inválido."},
                status=400,
            )

        perfiles = UserProfile.objects.select_related('user').all()
        bombero_ids = [perfil.user_id for perfil in perfiles]
        total_bomberos = len(bombero_ids)

        ct_citacion = ContentType.objects.get_for_model(Citacion)
        ct_emergencia = ContentType.objects.get_for_model(Emergencia)

        citaciones = Citacion.objects.filter(fecha__year=year).order_by('fecha')
        emergencias = Emergencia.objects.filter(fecha__year=year).order_by('fecha')

        citacion_ids = list(citaciones.values_list('id', flat=True))
        emergencia_ids = list(emergencias.values_list('id', flat=True))

        listas_citacion = list(
            ListaAsistencia.objects.filter(
                content_type=ct_citacion,
                object_id__in=citacion_ids,
            ).prefetch_related('asistencias__bombero')
        )
        listas_emergencia = list(
            ListaAsistencia.objects.filter(
                content_type=ct_emergencia,
                object_id__in=emergencia_ids,
            ).prefetch_related('asistencias__bombero')
        )

        listas = listas_citacion + listas_emergencia

        citaciones_con_lista_ids = {lista.object_id for lista in listas_citacion}
        emergencias_con_lista_ids = {lista.object_id for lista in listas_emergencia}

        total_citaciones = len(citaciones_con_lista_ids)
        total_emergencias = len(emergencias_con_lista_ids)
        total_listas = len(listas)

        if total_listas == 0 or total_bomberos == 0:
            data = {
                'anio': year,
                'total_citaciones': total_citaciones,
                'total_emergencias': total_emergencias,
                'total_listas': total_listas,
                'total_bomberos': total_bomberos,
                'total_posibles': total_listas * total_bomberos,
                'totales': {
                    'asistentes': 0,
                    'licencias': 0,
                    'inasistencias': 0,
                    'registrados': total_bomberos,
                },
                'porcentajes': {
                    'asistentes': 0.0,
                    'licencias': 0.0,
                    'inasistencias': 0.0,
                },
            }
            serializer = AsistenciaAnualGlobalSerializer(data)
            return Response(serializer.data)

        asistencia_status = {}

        for lista in listas:
            for asistencia in lista.asistencias.all():
                key = (lista.id, asistencia.bombero_id)
                if asistencia.asistio:
                    asistencia_status[key] = 'asistencia'
                else:
                    asistencia_status.setdefault(key, 'inasistencia')

        listas_por_citacion = {}
        for lista in listas_citacion:
            listas_por_citacion.setdefault(lista.object_id, []).append(lista)

        licencias = Licencia.objects.filter(
            citacion_id__in=citaciones_con_lista_ids,
            citacion__fecha__year=year,
            autor_id__in=bombero_ids,
        ).values_list('citacion_id', 'autor_id')

        licencias_set = set()
        for citacion_id, autor_id in licencias:
            for lista in listas_por_citacion.get(citacion_id, []):
                key = (lista.id, autor_id)
                if asistencia_status.get(key) == 'asistencia':
                    continue
                licencias_set.add(key)

        total_posibles = total_listas * total_bomberos
        contadores = {
            'asistencia': 0,
            'licencia': 0,
            'inasistencia': 0,
        }

        bombero_set = set(bombero_ids)

        for lista in listas:
            for bombero_id in bombero_set:
                key = (lista.id, bombero_id)
                status = asistencia_status.get(key)
                if status == 'asistencia':
                    contadores['asistencia'] += 1
                elif key in licencias_set:
                    contadores['licencia'] += 1
                elif status == 'inasistencia':
                    contadores['inasistencia'] += 1
                else:
                    contadores['inasistencia'] += 1

        porcentajes = {
            'asistentes': round((contadores['asistencia'] / total_posibles) * 100, 2)
            if total_posibles
            else 0.0,
            'licencias': round((contadores['licencia'] / total_posibles) * 100, 2)
            if total_posibles
            else 0.0,
            'inasistencias': round((contadores['inasistencia'] / total_posibles) * 100, 2)
            if total_posibles
            else 0.0,
        }

        data = {
            'anio': year,
            'total_citaciones': total_citaciones,
            'total_emergencias': total_emergencias,
            'total_listas': total_listas,
            'total_bomberos': total_bomberos,
            'total_posibles': total_posibles,
            'totales': {
                'asistentes': contadores['asistencia'],
                'licencias': contadores['licencia'],
                'inasistencias': contadores['inasistencia'],
                'registrados': total_bomberos,
            },
            'porcentajes': porcentajes,
        }

        serializer = AsistenciaAnualGlobalSerializer(data)
        return Response(serializer.data)


class AsistenciaEmergenciaResumenViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        year_param = request.query_params.get('anio')
        year = None
        if year_param is not None:
            try:
                year = int(year_param)
            except ValueError:
                return Response(
                    {"detail": "Parámetro 'anio' inválido."},
                    status=400,
                )

        emergencia = get_object_or_404(Emergencia.objects.select_related('autor'), pk=pk)

        if year is not None and emergencia.fecha.year != year:
            return Response(
                {"detail": "La emergencia no corresponde al año solicitado."},
                status=404,
            )

        content_type = ContentType.objects.get_for_model(Emergencia)
        lista = (
            ListaAsistencia.objects.filter(
                content_type=content_type,
                object_id=emergencia.id,
            )
            .prefetch_related('asistencias__bombero')
            .first()
        )

        if not lista:
            return Response(
                {"detail": "La emergencia no tiene una lista de asistencia asociada."},
                status=404,
            )

        asistencias = list(lista.asistencias.all())

        all_users_qs = User.objects.all().order_by('id')
        user_map = {user.id: user for user in all_users_qs}
        total_registrados = len(user_map)

        asistentes_data = []
        asistentes_ids = set()
        inasistencias_registradas_ids = set()

        for asistencia in asistencias:
            bombero = asistencia.bombero
            asistentes_data.append(OrderedDict([
                ('id', bombero.id),
                ('email', bombero.email),
                ('first_name', bombero.first_name),
                ('last_name', bombero.last_name),
                ('asistio', asistencia.asistio),
                ('hora_llegada', asistencia.hora_llegada),
            ]))

            if asistencia.asistio:
                asistentes_ids.add(bombero.id)
            else:
                inasistencias_registradas_ids.add(bombero.id)

        inasistentes_ids = set(inasistencias_registradas_ids)

        if total_registrados:
            inasistentes_ids.update(
                set(user_map.keys())
                - asistentes_ids
                - inasistencias_registradas_ids
            )

        inasistentes_data = [
            OrderedDict([
                ('id', user.id),
                ('email', user.email),
                ('first_name', user.first_name),
                ('last_name', user.last_name),
            ])
            for user_id, user in user_map.items()
            if user_id in inasistentes_ids
        ]

        total_asistencias = len(asistentes_ids)
        total_inasistencias = len(inasistentes_ids)

        if total_registrados > 0:
            porcentaje_asistencias = round((total_asistencias / total_registrados) * 100, 2)
            porcentaje_inasistencias = round((total_inasistencias / total_registrados) * 100, 2)
        else:
            porcentaje_asistencias = porcentaje_inasistencias = 0.0

        data = {
            'emergencia': {
                'id': emergencia.id,
                'clave': emergencia.clave,
                'fecha': emergencia.fecha,
                'unidades': emergencia.unidades,
            },
            'asistentes': asistentes_data,
            'inasistentes': inasistentes_data,
            'totales': {
                'asistentes': total_asistencias,
                'licencias': 0,
                'inasistencias': total_inasistencias,
                'registrados': total_registrados,
            },
            'porcentajes': {
                'asistentes': porcentaje_asistencias,
                'licencias': 0.0,
                'inasistencias': porcentaje_inasistencias,
            },
        }

        serializer = AsistenciaEmergenciaResumenSerializer(data)
        return Response(serializer.data)
