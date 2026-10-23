from django.db import models

from apps.configuracion.models import TipoVehiculo


class Zona(models.Model):
    """Agrupación de espacios (A, B, C...) para un tipo de vehículo."""

    nombre = models.CharField(max_length=10, unique=True)
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.PROTECT, related_name="zonas")

    class Meta:
        verbose_name = "zona"
        verbose_name_plural = "zonas"
        ordering = ["nombre"]

    def __str__(self):
        return f"Zona {self.nombre} ({self.tipo_vehiculo})"


class Espacio(models.Model):
    """Un puesto de parqueo."""

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        OCUPADO = "OCUPADO", "Ocupado"
        INACTIVO = "INACTIVO", "Inactivo"

    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, related_name="espacios")
    codigo = models.CharField(max_length=10, unique=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)

    class Meta:
        verbose_name = "espacio"
        verbose_name_plural = "espacios"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.get_estado_display()}"
