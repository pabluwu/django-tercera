from django.core.management.base import BaseCommand

from bomberos.models import MesAnio, MesPago


class Command(BaseCommand):
    help = "Puebla la tabla MesAnio con meses (01-12) para los años indicados (por defecto hasta 2030)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-year",
            type=int,
            default=2020,
            help="Año inicial (incluido). Por defecto 2020.",
        )
        parser.add_argument(
            "--end-year",
            type=int,
            default=2030,
            help="Año final (incluido). Por defecto 2030.",
        )

    def handle(self, *args, **options):
        start_year = options["start_year"]
        end_year = options["end_year"]

        if start_year > end_year:
            self.stderr.write(self.style.ERROR("El año inicial no puede ser mayor que el final."))
            return

        created = 0
        for year in range(start_year, end_year + 1):
            for mes, _ in MesPago.choices:
                _, was_created = MesAnio.objects.get_or_create(anio=year, mes=mes)
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"MesAnio listo. Registros creados: {created}"))
