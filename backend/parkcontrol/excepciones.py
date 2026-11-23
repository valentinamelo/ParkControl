from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ReglaNegocio(APIException):
    """Una regla de negocio impide la operación (400). Dentro de transaction.atomic deshace todo lo hecho."""

    status_code = status.HTTP_400_BAD_REQUEST


def manejar_excepciones(exc, context):
    """Igual al de DRF, pero un borrado bloqueado por PROTECT responde 400 con un mensaje claro."""
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "No se puede eliminar porque tiene registros asociados."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return exception_handler(exc, context)
