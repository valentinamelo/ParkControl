from django.contrib import admin

from .models import Pago, Tiquete


@admin.register(Tiquete)
class TiqueteAdmin(admin.ModelAdmin):
    list_display = ["codigo", "vehiculo", "espacio", "fecha_entrada", "fecha_salida", "valor", "estado"]
    list_filter = ["estado", "es_mensualidad"]
    search_fields = ["codigo", "vehiculo__placa"]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ["fecha", "valor", "metodo", "tiquete", "mensualidad", "usuario"]
    list_filter = ["metodo"]
