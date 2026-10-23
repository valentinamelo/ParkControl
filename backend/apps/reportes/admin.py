from django.contrib import admin

from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ["fecha", "usuario", "accion", "detalle"]
    list_filter = ["accion"]
