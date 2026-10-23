from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.reportes.bitacora import BitacoraMixin, registrar

from .models import Usuario
from .permissions import EsAdministrador
from .serializers import LoginSerializer, UsuarioAdminSerializer, UsuarioSerializer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  {email, password} -> {access, refresh, usuario}"""

    serializer_class = LoginSerializer


@api_view(["GET"])
def me(request):
    """GET /api/auth/me/ -> datos del usuario autenticado."""
    return Response(UsuarioSerializer(request.user).data)


class UsuarioViewSet(BitacoraMixin, viewsets.ModelViewSet):
    """CRUD de usuarios, solo para el administrador. DELETE desactiva en lugar de borrar."""

    queryset = Usuario.objects.order_by("rol", "first_name", "last_name")
    serializer_class = UsuarioAdminSerializer
    permission_classes = [EsAdministrador]
    nombre_bitacora = "USUARIO"

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        if usuario.pk == request.user.pk:
            return Response({"detail": "No puedes desactivarte a ti mismo."}, status=status.HTTP_400_BAD_REQUEST)
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        registrar(request.user, "DESACTIVAR_USUARIO", str(usuario))
        return Response(UsuarioAdminSerializer(usuario, context={"request": request}).data)
