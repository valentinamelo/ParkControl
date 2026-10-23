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
        extra_kwargs = {"nombre": {"validators": []}}  # se valida en validate_nombre

    def validate_nombre(self, valor):
        valor = valor.strip().capitalize()
        if TipoVehiculo.objects.filter(nombre__iexact=valor).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Ya existe un tipo de vehículo con este nombre.")
        return valor


class TarifaSerializer(serializers.ModelSerializer):
    tipo_vehiculo_nombre = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)

    class Meta:
        model = Tarifa
        fields = [
            "id", "tipo_vehiculo", "tipo_vehiculo_nombre", "modalidad", "modalidad_display",
            "valor", "minutos_fraccion", "minutos_gracia", "tope_diario", "vigente", "creada",
        ]
        read_only_fields = ["vigente", "creada"]

    def validate(self, attrs):
        # En una edición parcial, lo que no llega se toma de la tarifa actual
        def valor_de(campo, defecto=None):
            return attrs.get(campo, getattr(self.instance, campo, defecto))

        if valor_de("valor", 0) <= 0:
            raise serializers.ValidationError({"valor": "El valor debe ser mayor que cero."})
        if valor_de("modalidad") == Tarifa.Modalidad.HORA:
            attrs["minutos_fraccion"] = 60
        elif valor_de("minutos_fraccion", 0) < 1:
            raise serializers.ValidationError({"minutos_fraccion": "La fracción debe ser de al menos 1 minuto."})
        tope = valor_de("tope_diario")
        if tope is not None and tope < valor_de("valor"):
            raise serializers.ValidationError({"tope_diario": "El tope diario no puede ser menor que el valor de una hora o fracción."})
        return attrs


class HorarioSerializer(serializers.ModelSerializer):
    dia = serializers.CharField(source="get_dia_semana_display", read_only=True)

    class Meta:
        model = Horario
        fields = ["id", "dia_semana", "dia", "hora_apertura", "hora_cierre", "abierto"]

    def validate(self, attrs):
        abierto = attrs.get("abierto", getattr(self.instance, "abierto", True))
        apertura = attrs.get("hora_apertura", getattr(self.instance, "hora_apertura", None))
        cierre = attrs.get("hora_cierre", getattr(self.instance, "hora_cierre", None))
        if abierto and apertura and cierre and apertura >= cierre:
            raise serializers.ValidationError({"hora_cierre": "La hora de cierre debe ser posterior a la de apertura."})
        return attrs
