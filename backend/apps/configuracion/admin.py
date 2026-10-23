from django.contrib import admin

from .models import Horario, Parqueadero, Tarifa, TipoVehiculo

admin.site.register(Parqueadero)
admin.site.register(TipoVehiculo)


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ["tipo_vehiculo", "modalidad", "valor", "minutos_fraccion", "minutos_gracia", "tope_diario", "vigente"]
    list_filter = ["tipo_vehiculo", "vigente"]


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ["dia_semana", "hora_apertura", "hora_cierre", "abierto"]
