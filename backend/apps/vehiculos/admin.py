from django.contrib import admin

from .models import Cliente, Vehiculo


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ["placa", "tipo_vehiculo", "marca", "modelo", "color", "cliente"]
    list_filter = ["tipo_vehiculo"]
    search_fields = ["placa"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "documento", "telefono", "correo"]
    search_fields = ["nombre", "documento"]
