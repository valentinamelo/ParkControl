from rest_framework import viewsets

from .models import Vehiculo
from .serializers import VehiculoSerializer

# Avance 1: solo lectura. En el avance 2 se agrega crear, editar y eliminar.


class VehiculoViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/vehiculos/?placa=ABC"""

    serializer_class = VehiculoSerializer

    def get_queryset(self):
        qs = Vehiculo.objects.select_related("tipo_vehiculo", "cliente").all()
        placa = self.request.query_params.get("placa")
        if placa:
            qs = qs.filter(placa__icontains=placa.replace(" ", "").replace("-", ""))
        return qs
