from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, UsuarioSerializer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  {email, password} -> {access, refresh, usuario}"""

    serializer_class = LoginSerializer


@api_view(["GET"])
def me(request):
    """GET /api/auth/me/ -> datos del usuario autenticado."""
    return Response(UsuarioSerializer(request.user).data)
