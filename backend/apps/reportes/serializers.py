from rest_framework import serializers

from .models import Bitacora


class BitacoraSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    usuario_rol = serializers.CharField(source="usuario.get_rol_display", read_only=True)

    class Meta:
        model = Bitacora
        fields = ["id", "fecha", "usuario", "usuario_nombre", "usuario_rol", "accion", "detalle"]

    def get_usuario_nombre(self, registro):
        return registro.usuario.get_full_name() or registro.usuario.email
