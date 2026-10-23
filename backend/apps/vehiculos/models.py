from django.db import models

from apps.configuracion.models import TipoVehiculo


class Cliente(models.Model):
    """Propietario de un vehículo (necesario para mensualidades)."""

    nombre = models.CharField(max_length=120)
    documento = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    correo = models.EmailField(blank=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.documento})"


class Vehiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.PROTECT, related_name="vehiculos")
    marca = models.CharField(max_length=40, blank=True)
    modelo = models.CharField(max_length=40, blank=True)
    color = models.CharField(max_length=30, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehiculos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "vehículo"
        verbose_name_plural = "vehículos"
        ordering = ["placa"]

    def save(self, *args, **kwargs):
        self.placa = self.placa.upper().replace(" ", "").replace("-", "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.placa} ({self.tipo_vehiculo})"
