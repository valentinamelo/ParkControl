import re

from django.utils import timezone
from rest_framework import serializers

from apps.configuracion.models import TipoVehiculo
from apps.espacios.models import Espacio
from apps.vehiculos.serializers import normalizar_placa

from .models import Pago, Tiquete
from .reglas import minutos_entre


class TiqueteSerializer(serializers.ModelSerializer):
    placa = serializers.CharField(source="vehiculo.placa", read_only=True)
    tipo_vehiculo = serializers.CharField(source="vehiculo.tipo_vehiculo.nombre", read_only=True)
    vehiculo_descripcion = serializers.SerializerMethodField()
    espacio = serializers.CharField(source="espacio.codigo", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    usuario_entrada = serializers.CharField(source="usuario_entrada.get_full_name", read_only=True)
    usuario_salida = serializers.CharField(source="usuario_salida.get_full_name", read_only=True, default=None)
    metodo_pago = serializers.SerializerMethodField()
    minutos_transcurridos = serializers.SerializerMethodField()

    class Meta:
        model = Tiquete
        fields = [
            "id", "codigo", "placa", "tipo_vehiculo", "vehiculo_descripcion", "espacio",
            "fecha_entrada", "fecha_salida", "minutos", "minutos_transcurridos", "valor", "multa",
            "estado", "estado_display", "es_mensualidad", "usuario_entrada", "usuario_salida", "metodo_pago",
            "motivo_anulacion",
        ]

    def get_vehiculo_descripcion(self, tiquete):
        v = tiquete.vehiculo
        return " ".join(p for p in (v.marca, v.modelo, v.color) if p)

    def get_metodo_pago(self, tiquete):
        pago = getattr(tiquete, "pago", None)  # el tiquete puede no tener pago (mensualidad o $0)
        return pago.get_metodo_display() if pago else None

    def get_minutos_transcurridos(self, tiquete):
        """Para tiquetes abiertos, el tiempo que lleva dentro; para cerrados, el que se cobró."""
        if tiquete.estado != Tiquete.Estado.ABIERTO:
            return tiquete.minutos
        return minutos_entre(tiquete.fecha_entrada, timezone.now())


class EntradaSerializer(serializers.Serializer):
    """
    POST /api/tiquetes/entrada/
    {placa, tipo_vehiculo?, espacio?, marca?, modelo?, color?, forzar?}

    Si la placa no existe, se registra el vehículo con los datos enviados (tipo obligatorio).
    Si no se indica el espacio, se asigna el espacio fijo de la mensualidad o el primero disponible.
    """

    placa = serializers.CharField(max_length=10)
    tipo_vehiculo = serializers.PrimaryKeyRelatedField(queryset=TipoVehiculo.objects.all(), required=False)
    espacio = serializers.PrimaryKeyRelatedField(queryset=Espacio.objects.select_related("zona"), required=False)
    marca = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    modelo = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    color = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    forzar = serializers.BooleanField(required=False, default=False)

    def validate_placa(self, valor):
        valor = normalizar_placa(valor)
        if not re.fullmatch(r"[A-Z0-9]{4,8}", valor):
            raise serializers.ValidationError("La placa debe tener entre 4 y 8 letras o números (p. ej. ABC123).")
        return valor


class SalidaSerializer(serializers.Serializer):
    """POST /api/tiquetes/{codigo}/salida/ {metodo?, tiquete_perdido?}"""

    metodo = serializers.ChoiceField(choices=Pago.Metodo.choices, required=False)
    tiquete_perdido = serializers.BooleanField(required=False, default=False)


class AnulacionSerializer(serializers.Serializer):
    """POST /api/tiquetes/{codigo}/anular/ {motivo}"""

    motivo = serializers.CharField(max_length=200)

    def validate_motivo(self, valor):
        valor = valor.strip()
        if len(valor) < 5:
            raise serializers.ValidationError("Explica el motivo de la anulación (mínimo 5 caracteres).")
        return valor
