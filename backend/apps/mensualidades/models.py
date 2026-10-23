from django.db import models

from apps.configuracion.models import TipoVehiculo
from apps.espacios.models import Espacio
from apps.vehiculos.models import Cliente, Vehiculo


class PlanMensual(models.Model):
    nombre = models.CharField(max_length=60)
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.PROTECT, related_name="planes")
    valor = models.DecimalField(max_digits=10, decimal_places=0)
    dias = models.PositiveIntegerField(default=30)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "plan mensual"
        verbose_name_plural = "planes mensuales"
        ordering = ["tipo_vehiculo__nombre", "nombre"]

    def __str__(self):
        return f"{self.nombre} - ${self.valor}"


class Mensualidad(models.Model):
    class Estado(models.TextChoices):
        VIGENTE = "VIGENTE", "Vigente"
        VENCIDA = "VENCIDA", "Vencida"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="mensualidades")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="mensualidades")
    plan = models.ForeignKey(PlanMensual, on_delete=models.PROTECT, related_name="mensualidades")
    espacio_fijo = models.ForeignKey(
        Espacio, on_delete=models.SET_NULL, null=True, blank=True, related_name="mensualidades"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.VIGENTE)

    class Meta:
        verbose_name = "mensualidad"
        verbose_name_plural = "mensualidades"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.vehiculo.placa} {self.fecha_inicio} a {self.fecha_fin}"
