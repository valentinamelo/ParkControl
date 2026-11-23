"""
Tarea diaria (por ejemplo con cron a las 00:05):

    python manage.py marcar_mensualidades_vencidas

Las consultas de mensualidades también lo hacen al vuelo, así que la tarea es un respaldo.
"""
from django.core.management.base import BaseCommand

from apps.mensualidades.reglas import marcar_vencidas


class Command(BaseCommand):
    help = "Marca como VENCIDA cada mensualidad cuya fecha final ya pasó."

    def handle(self, *args, **options):
        cantidad = marcar_vencidas()
        self.stdout.write(self.style.SUCCESS(f"{cantidad} mensualidades marcadas como vencidas."))
