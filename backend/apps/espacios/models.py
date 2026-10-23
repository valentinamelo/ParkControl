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

    def siguientes_codigos(self, cantidad):
        """Los próximos códigos libres de la zona: si existen A-01..A-05, sigue A-06, A-07..."""
        prefijo = f"{self.nombre}-"
        usados = set(Espacio.objects.filter(codigo__startswith=prefijo).values_list("codigo", flat=True))
        numeros = [int(c[len(prefijo):]) for c in usados if c[len(prefijo):].isdigit()]
        n = max(numeros, default=0)
        codigos = []
        while len(codigos) < cantidad:
            n += 1
            codigo = f"{prefijo}{n:02d}"
            if codigo not in usados:
                codigos.append(codigo)
        return codigos

    def crear_espacios(self, cantidad):
        return Espacio.objects.bulk_create(
            [Espacio(zona=self, codigo=codigo) for codigo in self.siguientes_codigos(cantidad)]
        )


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
