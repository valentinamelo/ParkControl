from django.contrib import admin

from .models import Espacio, Zona


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo_vehiculo"]


@admin.register(Espacio)
class EspacioAdmin(admin.ModelAdmin):
    list_display = ["codigo", "zona", "estado"]
    list_filter = ["zona", "estado"]
    search_fields = ["codigo"]
