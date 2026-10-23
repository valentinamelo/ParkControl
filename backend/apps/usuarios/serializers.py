from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Para que el administrador cree y edite usuarios. La contraseña solo se escribe."""

    nombre = serializers.CharField(source="get_full_name", read_only=True)
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={"input_type": "password"})

    class Meta:
        model = Usuario
        fields = ["id", "email", "first_name", "last_name", "nombre", "rol", "rol_display", "is_active", "password"]
        # La unicidad del correo se valida en validate_email, sin distinguir mayúsculas
        extra_kwargs = {"first_name": {"required": True, "allow_blank": False}, "email": {"validators": []}}

    def validate_email(self, valor):
        valor = valor.strip().lower()
        if Usuario.objects.filter(email__iexact=valor).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo.")
        return valor

    def validate(self, attrs):
        password = attrs.get("password")
        if self.instance is None and not password:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})
        if password:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})

        # El administrador no puede quitarse a sí mismo el rol ni desactivarse
        usuario = self.context["request"].user
        if self.instance is not None and self.instance.pk == usuario.pk:
            if attrs.get("is_active") is False or attrs.get("rol", usuario.rol) != usuario.rol:
                raise serializers.ValidationError("No puedes desactivarte ni cambiar tu propio rol.")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return Usuario.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", "")
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)
