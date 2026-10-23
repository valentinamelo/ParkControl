from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Horario, Parqueadero, Tarifa, TipoVehiculo
from .serializers import HorarioSerializer, ParqueaderoSerializer, TarifaSerializer, TipoVehiculoSerializer

# Avance 1: solo lectura. En el avance 2 pasan a ModelViewSet con AdminOSoloLectura.


class TipoVehiculoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TipoVehiculo.objects.all()
    serializer_class = TipoVehiculoSerializer


class TarifaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tarifa.objects.select_related("tipo_vehiculo").filter(vigente=True)
    serializer_class = TarifaSerializer


class HorarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer


@api_view(["GET"])
def parqueadero(request):
    """GET /api/parqueadero/ -> datos generales del parqueadero."""
    obj, _ = Parqueadero.objects.get_or_create(pk=1)
    return Response(ParqueaderoSerializer(obj).data)
