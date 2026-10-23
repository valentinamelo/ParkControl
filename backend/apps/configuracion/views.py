from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.reportes.bitacora import BitacoraMixin, registrar
from apps.usuarios.permissions import AdminOSoloLectura

from .models import Horario, Parqueadero, Tarifa, TipoVehiculo
from .serializers import HorarioSerializer, ParqueaderoSerializer, TarifaSerializer, TipoVehiculoSerializer

# Todos leen la configuración; solo el administrador la cambia.


class TipoVehiculoViewSet(BitacoraMixin, viewsets.ModelViewSet):
    queryset = TipoVehiculo.objects.all()
    serializer_class = TipoVehiculoSerializer
    permission_classes = [AdminOSoloLectura]
    nombre_bitacora = "TIPO_VEHICULO"


class TarifaViewSet(viewsets.ModelViewSet):
    """
    GET /api/tarifas/              -> tarifas vigentes
    GET /api/tarifas/?historial=1  -> también las anteriores

    Cambiar una tarifa no la modifica: se crea una nueva vigente y la anterior queda
    en el historial, así los tiquetes ya cobrados conservan su valor.
    """

    serializer_class = TarifaSerializer
    permission_classes = [AdminOSoloLectura]

    def get_queryset(self):
        qs = Tarifa.objects.select_related("tipo_vehiculo")
        if not self.request.query_params.get("historial"):
            qs = qs.filter(vigente=True)
        return qs

    @transaction.atomic
    def _crear_vigente(self, datos):
        """Crea la tarifa nueva y deja sin vigencia la anterior del mismo tipo de vehículo."""
        Tarifa.objects.filter(tipo_vehiculo=datos["tipo_vehiculo"], vigente=True).update(vigente=False)
        return Tarifa.objects.create(**datos, vigente=True)

    def perform_create(self, serializer):
        serializer.instance = self._crear_vigente(serializer.validated_data)
        registrar(self.request.user, "CREAR_TARIFA", str(serializer.instance))

    def update(self, request, *args, **kwargs):
        anterior = self.get_object()
        if not anterior.vigente:
            return Response({"detail": "Solo se puede cambiar una tarifa vigente."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(anterior, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)

        campos = ["tipo_vehiculo", "modalidad", "valor", "minutos_fraccion", "minutos_gracia", "tope_diario"]
        datos = {campo: getattr(anterior, campo) for campo in campos}
        datos.update(serializer.validated_data)
        datos["tipo_vehiculo"] = anterior.tipo_vehiculo  # el tipo de vehículo de una tarifa no cambia
        nueva = self._crear_vigente(datos)
        registrar(request.user, "CAMBIAR_TARIFA", f"{anterior} -> {nueva}")
        return Response(self.get_serializer(nueva).data)

    def perform_destroy(self, instance):
        # No se borra: queda en el historial sin vigencia
        instance.vigente = False
        instance.save(update_fields=["vigente"])
        registrar(self.request.user, "QUITAR_TARIFA", str(instance))


class HorarioViewSet(BitacoraMixin, viewsets.ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [AdminOSoloLectura]
    nombre_bitacora = "HORARIO"


@api_view(["GET", "PUT", "PATCH"])
@permission_classes([AdminOSoloLectura])
def parqueadero(request):
    """GET /api/parqueadero/ -> datos generales del parqueadero. PUT/PATCH solo el admin."""
    obj, _ = Parqueadero.objects.get_or_create(pk=1)
    if request.method == "GET":
        return Response(ParqueaderoSerializer(obj).data)
    serializer = ParqueaderoSerializer(obj, data=request.data, partial=request.method == "PATCH")
    serializer.is_valid(raise_exception=True)
    serializer.save()
    registrar(request.user, "EDITAR_PARQUEADERO", str(obj))
    return Response(serializer.data)
