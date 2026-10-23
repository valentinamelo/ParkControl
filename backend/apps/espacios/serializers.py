from django.utils import timezone
from rest_framework import serializers

from apps.configuracion.models import TipoVehiculo
from apps.operaciones.models import Tiquete

from .models import Espacio, Zona


class ZonaSerializer(serializers.ModelSerializer):
    tipo_vehiculo_nombre = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    total_espacios = serializers.IntegerField(source="espacios.count", read_only=True)

    class Meta:
        model = Zona
        fields = ["id", "nombre", "tipo_vehiculo", "tipo_vehiculo_nombre", "total_espacios"]
        extra_kwargs = {"nombre": {"validators": []}}  # se valida en validate_nombre

    def validate_nombre(self, valor):
        valor = valor.strip().upper()
        if Zona.objects.filter(nombre=valor).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError(f"Ya existe la zona {valor}.")
        if self.instance and self.instance.nombre != valor and self.instance.espacios.exists():
            raise serializers.ValidationError("No se puede renombrar una zona que ya tiene espacios.")
        return valor

    def validate_tipo_vehiculo(self, tipo):
        # Cambiar el tipo de la zona cambia el tipo de todos sus espacios (RF-06)
        if (
            self.instance
            and self.instance.tipo_vehiculo_id != tipo.pk
            and self.instance.espacios.filter(estado=Espacio.Estado.OCUPADO).exists()
        ):
            raise serializers.ValidationError("No se puede cambiar el tipo mientras haya espacios ocupados en la zona.")
        return tipo


class EspacioSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    tipo_vehiculo = serializers.CharField(source="zona.tipo_vehiculo.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    ocupante = serializers.SerializerMethodField()
    # Si se crea sin código, se asigna el siguiente libre de la zona
    codigo = serializers.CharField(max_length=10, required=False, allow_blank=True)

    class Meta:
        model = Espacio
        fields = ["id", "codigo", "zona", "zona_nombre", "tipo_vehiculo", "estado", "estado_display", "ocupante"]

    def get_ocupante(self, espacio):
        """Si el espacio está ocupado, devuelve el tiquete abierto que lo ocupa."""
        if espacio.estado != Espacio.Estado.OCUPADO:
            return None
        tiquete = next(
            (t for t in espacio.tiquetes.all() if t.estado == Tiquete.Estado.ABIERTO),
            None,
        )
        if tiquete is None:
            return None
        minutos = int((timezone.now() - tiquete.fecha_entrada).total_seconds() // 60)
        return {
            "tiquete": tiquete.codigo,
            "placa": tiquete.vehiculo.placa,
            "tipo_vehiculo": tiquete.vehiculo.tipo_vehiculo.nombre,
            "fecha_entrada": tiquete.fecha_entrada,
            "minutos": minutos,
            "es_mensualidad": tiquete.es_mensualidad,
        }

    def validate_codigo(self, valor):
        valor = valor.strip().upper()
        if valor and Espacio.objects.filter(codigo=valor).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError(f"Ya existe el espacio {valor}.")
        return valor

    def validate(self, attrs):
        estado = attrs.get("estado")
        if estado == Espacio.Estado.OCUPADO and getattr(self.instance, "estado", None) != Espacio.Estado.OCUPADO:
            raise serializers.ValidationError({"estado": "Un espacio solo se ocupa registrando la entrada de un vehículo."})

        if self.instance and self.instance.estado == Espacio.Estado.OCUPADO:
            if estado and estado != Espacio.Estado.OCUPADO:
                raise serializers.ValidationError({"estado": "No se puede desactivar un espacio ocupado."})
            if "zona" in attrs and attrs["zona"] != self.instance.zona:
                raise serializers.ValidationError({"zona": "No se puede mover un espacio ocupado."})

        if self.instance is None and not attrs.get("codigo"):
            attrs["codigo"] = attrs["zona"].siguientes_codigos(1)[0]
        return attrs


class EspacioLoteSerializer(serializers.Serializer):
    """POST /api/espacios/lote/ {zona: "B", tipo_vehiculo: 1, cantidad: 10}. Si la zona no existe, se crea."""

    zona = serializers.CharField(max_length=10)
    tipo_vehiculo = serializers.PrimaryKeyRelatedField(queryset=TipoVehiculo.objects.all(), required=False)
    cantidad = serializers.IntegerField(min_value=1, max_value=100)

    def validate(self, attrs):
        attrs["zona"] = attrs["zona"].strip().upper()
        zona = Zona.objects.filter(nombre=attrs["zona"]).first()
        tipo = attrs.get("tipo_vehiculo")
        if zona is None and tipo is None:
            raise serializers.ValidationError({"tipo_vehiculo": "Indica el tipo de vehículo de la zona nueva."})
        if zona is not None and tipo is not None and zona.tipo_vehiculo_id != tipo.pk:
            raise serializers.ValidationError(
                {"tipo_vehiculo": f"La zona {zona.nombre} es de tipo {zona.tipo_vehiculo}."}
            )
        return attrs

    def create(self, validated_data):
        zona, _ = Zona.objects.get_or_create(
            nombre=validated_data["zona"], defaults={"tipo_vehiculo": validated_data.get("tipo_vehiculo")}
        )
        return zona.crear_espacios(validated_data["cantidad"])
