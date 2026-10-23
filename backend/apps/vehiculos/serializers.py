import re

from rest_framework import serializers

from apps.operaciones.models import Tiquete

from .models import Cliente, Vehiculo


def normalizar_placa(placa):
    return placa.upper().replace(" ", "").replace("-", "")


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nombre", "documento", "telefono", "correo"]


class VehiculoSerializer(serializers.ModelSerializer):
    tipo_vehiculo_nombre = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default=None)

    class Meta:
        model = Vehiculo
        fields = [
            "id", "placa", "tipo_vehiculo", "tipo_vehiculo_nombre",
            "marca", "modelo", "color", "cliente", "cliente_nombre",
        ]
        # La unicidad se valida en validate_placa, ya con la placa normalizada
        extra_kwargs = {"placa": {"validators": []}}

    def validate_placa(self, valor):
        valor = normalizar_placa(valor)
        if not re.fullmatch(r"[A-Z0-9]{4,8}", valor):
            raise serializers.ValidationError("La placa debe tener entre 4 y 8 letras o números (p. ej. ABC123).")
        if Vehiculo.objects.filter(placa=valor).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError(f"Ya existe un vehículo con la placa {valor}.")
        return valor

    def validate_tipo_vehiculo(self, tipo):
        if (
            self.instance
            and self.instance.tipo_vehiculo_id != tipo.pk
            and self.instance.tiquetes.filter(estado=Tiquete.Estado.ABIERTO).exists()
        ):
            raise serializers.ValidationError("No se puede cambiar el tipo mientras el vehículo está dentro del parqueadero.")
        return tipo
