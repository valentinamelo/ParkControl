from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.reportes.bitacora import BitacoraMixin

from .models import Vehiculo
from .serializers import VehiculoSerializer, normalizar_placa


class VehiculoViewSet(BitacoraMixin, viewsets.ModelViewSet):
    """GET /api/vehiculos/?placa=ABC. Admin y trabajador registran, editan y eliminan."""

    serializer_class = VehiculoSerializer
    nombre_bitacora = "VEHICULO"

    def get_queryset(self):
        qs = Vehiculo.objects.select_related("tipo_vehiculo", "cliente").all()
        placa = self.request.query_params.get("placa")
        if placa:
            qs = qs.filter(placa__icontains=normalizar_placa(placa))
        return qs

    def destroy(self, request, *args, **kwargs):
        vehiculo = self.get_object()
        if vehiculo.tiquetes.exists() or vehiculo.mensualidades.exists():
            return Response(
                {"detail": "El vehículo tiene tiquetes o mensualidades registrados; no se puede eliminar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)
