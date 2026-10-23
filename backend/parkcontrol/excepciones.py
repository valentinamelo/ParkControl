from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def manejar_excepciones(exc, context):
    """Igual al de DRF, pero un borrado bloqueado por PROTECT responde 400 con un mensaje claro."""
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "No se puede eliminar porque tiene registros asociados."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return exception_handler(exc, context)
