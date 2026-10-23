from django.contrib import admin

from .models import Mensualidad, PlanMensual


@admin.register(PlanMensual)
class PlanMensualAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo_vehiculo", "valor", "dias", "activo"]


@admin.register(Mensualidad)
class MensualidadAdmin(admin.ModelAdmin):
    list_display = ["vehiculo", "cliente", "plan", "fecha_inicio", "fecha_fin", "estado"]
    list_filter = ["estado"]
