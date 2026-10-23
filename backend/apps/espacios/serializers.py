from django.utils import timezone
from rest_framework import serializers

from apps.operaciones.models import Tiquete

from .models import Espacio, Zona


class ZonaSerializer(serializers.ModelSerializer):
    tipo_vehiculo_nombre = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)
    total_espacios = serializers.IntegerField(source="espacios.count", read_only=True)

    class Meta:
        model = Zona
        fields = ["id", "nombre", "tipo_vehiculo", "tipo_vehiculo_nombre", "total_espacios"]


class EspacioSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    tipo_vehiculo = serializers.CharField(source="zona.tipo_vehiculo.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    ocupante = serializers.SerializerMethodField()

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
