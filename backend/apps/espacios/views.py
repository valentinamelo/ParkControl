from django.db.models import Prefetch
from rest_framework import viewsets

from apps.operaciones.models import Tiquete

from .models import Espacio, Zona
from .serializers import EspacioSerializer, ZonaSerializer

# Avance 1: solo lectura. En el avance 2 el admin podrá crear, editar y desactivar.


class ZonaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Zona.objects.select_related("tipo_vehiculo").all()
    serializer_class = ZonaSerializer


class EspacioViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/espacios/?estado=DISPONIBLE&tipo=Carro"""

    serializer_class = EspacioSerializer

    def get_queryset(self):
        qs = (
            Espacio.objects.select_related("zona__tipo_vehiculo")
            .prefetch_related(
                Prefetch(
                    "tiquetes",
                    queryset=Tiquete.objects.filter(estado=Tiquete.Estado.ABIERTO).select_related(
                        "vehiculo__tipo_vehiculo"
                    ),
                )
            )
            .order_by("codigo")
        )
        estado = self.request.query_params.get("estado")
        tipo = self.request.query_params.get("tipo")
        if estado:
            qs = qs.filter(estado=estado.upper())
        if tipo:
            qs = qs.filter(zona__tipo_vehiculo__nombre__iexact=tipo)
        return qs
