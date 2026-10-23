from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Usuario


class EsAdministrador(BasePermission):
    """Solo usuarios con rol ADMIN."""

    message = "Esta acción es solo para el administrador."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == Usuario.Rol.ADMIN)


class EsTrabajador(BasePermission):
    """Usuarios con rol TRABAJADOR (el admin también puede hacer lo del trabajador)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in (Usuario.Rol.TRABAJADOR, Usuario.Rol.ADMIN)
        )


class AdminOSoloLectura(BasePermission):
    """Cualquier usuario autenticado lee; solo el admin crea, edita o elimina."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.rol == Usuario.Rol.ADMIN
