from rest_framework import serializers

from .models import Cliente, Vehiculo


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
