from django.conf import settings
from django.db import models


class Bitacora(models.Model):
    """Registro de acciones importantes (entradas, salidas, anulaciones, cambios)."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="acciones")
    accion = models.CharField(max_length=50)
    detalle = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "registro de bitácora"
        verbose_name_plural = "bitácora"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} {self.usuario} - {self.accion}"
