from django.conf import settings
from django.db import models

from apps.espacios.models import Espacio
from apps.vehiculos.models import Vehiculo


class Tiquete(models.Model):
    """Movimiento de un vehículo: se abre en la entrada y se cierra en la salida."""

    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        CERRADO = "CERRADO", "Cerrado"
        ANULADO = "ANULADO", "Anulado"

    codigo = models.CharField(max_length=20, unique=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="tiquetes")
    espacio = models.ForeignKey(Espacio, on_delete=models.PROTECT, related_name="tiquetes")
    fecha_entrada = models.DateTimeField()
    fecha_salida = models.DateTimeField(null=True, blank=True)
    minutos = models.PositiveIntegerField(null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTO)
    es_mensualidad = models.BooleanField(default=False)
    motivo_anulacion = models.CharField(max_length=200, blank=True)
    usuario_entrada = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tiquetes_entrada"
    )
    usuario_salida = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="tiquetes_salida"
    )

    class Meta:
        verbose_name = "tiquete"
        verbose_name_plural = "tiquetes"
        ordering = ["-fecha_entrada"]

    def __str__(self):
        return f"{self.codigo} - {self.vehiculo.placa} ({self.get_estado_display()})"


class Pago(models.Model):
    """Pago de un tiquete o de una mensualidad."""

    class Metodo(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"

    tiquete = models.OneToOneField(Tiquete, on_delete=models.PROTECT, null=True, blank=True, related_name="pago")
    mensualidad = models.ForeignKey(
        "mensualidades.Mensualidad", on_delete=models.PROTECT, null=True, blank=True, related_name="pagos"
    )
    valor = models.DecimalField(max_digits=10, decimal_places=0)
    metodo = models.CharField(max_length=15, choices=Metodo.choices, default=Metodo.EFECTIVO)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pagos")

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"${self.valor} - {self.get_metodo_display()}"
