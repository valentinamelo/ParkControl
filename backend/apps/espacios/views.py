from django.db import transaction
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.operaciones.models import Tiquete
from apps.reportes.bitacora import BitacoraMixin, registrar
from apps.usuarios.permissions import AdminOSoloLectura

from .models import Espacio, Zona
from .serializers import EspacioLoteSerializer, EspacioSerializer, ZonaSerializer

# Todos ven el mapa; solo el administrador crea, edita, desactiva o elimina.


class ZonaViewSet(BitacoraMixin, viewsets.ModelViewSet):
    queryset = Zona.objects.select_related("tipo_vehiculo").all()
    serializer_class = ZonaSerializer
    permission_classes = [AdminOSoloLectura]
    nombre_bitacora = "ZONA"

    def destroy(self, request, *args, **kwargs):
        if self.get_object().espacios.exists():
            return Response(
                {"detail": "La zona tiene espacios. Elimínalos o desactívalos primero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class EspacioViewSet(BitacoraMixin, viewsets.ModelViewSet):
    """GET /api/espacios/?estado=DISPONIBLE&tipo=Carro"""

    serializer_class = EspacioSerializer
    permission_classes = [AdminOSoloLectura]
    nombre_bitacora = "ESPACIO"

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

    def destroy(self, request, *args, **kwargs):
        espacio = self.get_object()
        if espacio.estado == Espacio.Estado.OCUPADO:
            return Response({"detail": "No se puede eliminar un espacio ocupado."}, status=status.HTTP_400_BAD_REQUEST)
        if espacio.tiquetes.exists():
            return Response(
                {"detail": "El espacio tiene movimientos registrados; desactívalo en lugar de eliminarlo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def lote(self, request):
        """POST /api/espacios/lote/ -> crea varios espacios seguidos en una zona."""
        serializer = EspacioLoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        creados = serializer.save()
        registrar(
            request.user, "CREAR_ESPACIOS",
            f"Zona {serializer.validated_data['zona']}: {len(creados)} espacios ({creados[0].codigo} a {creados[-1].codigo})",
        )
        espacios = self.get_queryset().filter(codigo__in=[e.codigo for e in creados])
        return Response(self.get_serializer(espacios, many=True).data, status=status.HTTP_201_CREATED)
