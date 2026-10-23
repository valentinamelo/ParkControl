from rest_framework import serializers

from .models import Horario, Parqueadero, Tarifa, TipoVehiculo


class ParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parqueadero
        fields = ["id", "nombre", "nit", "direccion", "telefono"]


class TipoVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoVehiculo
        fields = ["id", "nombre"]


class TarifaSerializer(serializers.ModelSerializer):
    tipo_vehiculo_nombre = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)

    class Meta:
        model = Tarifa
        fields = [
            "id", "tipo_vehiculo", "tipo_vehiculo_nombre", "modalidad", "modalidad_display",
            "valor", "minutos_fraccion", "minutos_gracia", "tope_diario", "vigente",
        ]


class HorarioSerializer(serializers.ModelSerializer):
    dia = serializers.CharField(source="get_dia_semana_display", read_only=True)

    class Meta:
        model = Horario
        fields = ["id", "dia_semana", "dia", "hora_apertura", "hora_cierre", "abierto"]
