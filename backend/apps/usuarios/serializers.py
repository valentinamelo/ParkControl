from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source="get_full_name", read_only=True)
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "email", "first_name", "last_name", "nombre", "rol", "rol_display", "is_active"]


class LoginSerializer(TokenObtainPairSerializer):
    """Devuelve los tokens JWT y, además, los datos del usuario con su rol."""

    default_error_messages = {
        "no_active_account": "Correo o contraseña incorrectos.",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["rol"] = user.rol
        token["nombre"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["usuario"] = UsuarioSerializer(self.user).data
        return data
