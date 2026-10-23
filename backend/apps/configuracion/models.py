from django.db import models


class Parqueadero(models.Model):
    """Datos generales del parqueadero (un solo registro)."""

    nombre = models.CharField(max_length=100, default="ParkControl")
    nit = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "parqueadero"
        verbose_name_plural = "parqueadero"

    def __str__(self):
        return self.nombre


class TipoVehiculo(models.Model):
    """Carro, Moto, etc."""

    nombre = models.CharField(max_length=30, unique=True)

    class Meta:
        verbose_name = "tipo de vehículo"
        verbose_name_plural = "tipos de vehículo"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Tarifa(models.Model):
    """Tarifa de cobro para un tipo de vehículo."""

    class Modalidad(models.TextChoices):
        HORA = "HORA", "Por hora"
        FRACCION = "FRACCION", "Por fracción"

    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.PROTECT, related_name="tarifas")
    modalidad = models.CharField(max_length=10, choices=Modalidad.choices, default=Modalidad.HORA)
    valor = models.DecimalField("valor por hora o fracción", max_digits=10, decimal_places=0)
    minutos_fraccion = models.PositiveIntegerField(default=60)
    minutos_gracia = models.PositiveIntegerField(default=0)
    tope_diario = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    vigente = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "tarifa"
        verbose_name_plural = "tarifas"
        ordering = ["tipo_vehiculo__nombre", "-creada"]

    def __str__(self):
        return f"{self.tipo_vehiculo} - ${self.valor} ({self.get_modalidad_display()})"


class Horario(models.Model):
    """Horario de atención por día de la semana."""

    class Dia(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    dia_semana = models.IntegerField(choices=Dia.choices, unique=True)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    abierto = models.BooleanField(default=True)

    class Meta:
        verbose_name = "horario"
        verbose_name_plural = "horarios"
        ordering = ["dia_semana"]

    def __str__(self):
        if not self.abierto:
            return f"{self.get_dia_semana_display()}: cerrado"
        return f"{self.get_dia_semana_display()}: {self.hora_apertura:%H:%M} - {self.hora_cierre:%H:%M}"
