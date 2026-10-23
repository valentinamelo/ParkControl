from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager que usa el correo como identificador en lugar del username."""

    use_in_migrations = True

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError("El correo es obligatorio")
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        extra.setdefault("rol", Usuario.Rol.TRABAJADOR)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("rol", Usuario.Rol.ADMIN)
        return self._crear(email, password, **extra)


class Usuario(AbstractUser):
    """Usuario del sistema: administrador o trabajador."""

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        TRABAJADOR = "TRABAJADOR", "Trabajador"

    username = None
    email = models.EmailField("correo electrónico", unique=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.TRABAJADOR)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN
