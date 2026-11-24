from django.db import transaction
from django.db.models import Count, Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.mensualidades.reglas import espacios_reservados
from apps.operaciones.models import Tiquete
from apps.reportes.bitacora import BitacoraMixin, registrar
from apps.usuarios.permissions import AdminOSoloLectura
from apps.vehiculos.models import Vehiculo
from apps.vehiculos.serializers import normalizar_placa
from parkcontrol.excepciones import ReglaNegocio

from .models import Espacio, Zona
from .serializers import EspacioLoteSerializer, EspacioSerializer, ZonaSerializer

# Todos ven el mapa; solo el administrador crea, edita, desactiva o elimina.


def _lista(codigos, maximo=5):
    """["A-01", "A-02", ...] -> "A-01, A-02, A-03, A-04, A-05 y 3 más" """
    codigos = sorted(codigos)
    texto = ", ".join(codigos[:maximo])
    return texto + (f" y {len(codigos) - maximo} más" if len(codigos) > maximo else "")


class ZonaViewSet(BitacoraMixin, viewsets.ModelViewSet):
    """
    Una zona completa se puede desactivar (POST /api/zonas/{id}/desactivar/), volver a activar
    (POST /api/zonas/{id}/activar/) o eliminar con todos sus espacios (DELETE), siempre que
    sus espacios estén libres: sin vehículos dentro ni reservados por una mensualidad vigente.
    """

    serializer_class = ZonaSerializer
    permission_classes = [AdminOSoloLectura]
    nombre_bitacora = "ZONA"

    def get_queryset(self):
        return Zona.objects.select_related("tipo_vehiculo").annotate(
            total_espacios=Count("espacios"),
            espacios_ocupados=Count("espacios", filter=Q(espacios__estado=Espacio.Estado.OCUPADO)),
            espacios_inactivos=Count("espacios", filter=Q(espacios__estado=Espacio.Estado.INACTIVO)),
        )

    def _respuesta(self, zona):
        return Response(self.get_serializer(self.get_queryset().get(pk=zona.pk)).data)

    @staticmethod
    def _exigir_libre(zona, accion):
        """
        Bloquea los espacios de la zona (para que no entre un vehículo mientras tanto) y falla
        si alguno está ocupado o reservado. Debe llamarse dentro de una transacción.
        """
        espacios = list(Espacio.objects.select_for_update().filter(zona=zona))
        ocupados = [e.codigo for e in espacios if e.estado == Espacio.Estado.OCUPADO]
        if ocupados:
            raise ReglaNegocio(
                f"No se puede {accion} la zona {zona.nombre}: hay vehículos en {_lista(ocupados)}. "
                "Registra su salida primero."
            )
        reservados = list(
            Espacio.objects.filter(zona=zona, pk__in=espacios_reservados()).values_list("codigo", flat=True)
        )
        if reservados:
            raise ReglaNegocio(
                f"No se puede {accion} la zona {zona.nombre}: {_lista(reservados)} "
                f"{'es el espacio fijo' if len(reservados) == 1 else 'son espacios fijos'} de una mensualidad vigente. "
                "Cambia el espacio de esa mensualidad primero."
            )
        return espacios

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def desactivar(self, request, pk=None):
        """Desactiva todos los espacios de la zona: no se ofrecen para nuevas entradas."""
        zona = self.get_object()
        self._exigir_libre(zona, "desactivar")
        cantidad = Espacio.objects.filter(zona=zona, estado=Espacio.Estado.DISPONIBLE).update(
            estado=Espacio.Estado.INACTIVO
        )
        registrar(request.user, "DESACTIVAR_ZONA", f"{zona}: {cantidad} espacios desactivados")
        return self._respuesta(zona)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def activar(self, request, pk=None):
        """Vuelve a dejar disponibles todos los espacios inactivos de la zona."""
        zona = self.get_object()
        cantidad = Espacio.objects.filter(zona=zona, estado=Espacio.Estado.INACTIVO).update(
            estado=Espacio.Estado.DISPONIBLE
        )
        registrar(request.user, "ACTIVAR_ZONA", f"{zona}: {cantidad} espacios activados")
        return self._respuesta(zona)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Elimina la zona con todos sus espacios, si están libres y nunca se han usado."""
        zona = self.get_object()
        espacios = self._exigir_libre(zona, "eliminar")
        con_historial = list(
            Espacio.objects.filter(zona=zona, tiquetes__isnull=False).distinct().values_list("codigo", flat=True)
        )
        if con_historial:
            raise ReglaNegocio(
                f"No se puede eliminar la zona {zona.nombre}: {_lista(con_historial)} "
                f"{'tiene' if len(con_historial) == 1 else 'tienen'} movimientos registrados que deben conservarse. "
                "Desactiva la zona en lugar de eliminarla."
            )
        detalle = f"{zona} con {len(espacios)} espacios"
        Espacio.objects.filter(zona=zona).delete()
        zona.delete()
        registrar(request.user, "ELIMINAR_ZONA", detalle)
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    @action(detail=False)
    def disponibles(self, request):
        """
        GET /api/espacios/disponibles/?tipo=Carro&placa=ABC123
        Espacios DISPONIBLES del tipo pedido. Los espacios fijos de mensualidades vigentes
        se reservan: solo se ofrecen al vehículo de esa mensualidad.
        """
        if not request.query_params.get("tipo"):
            return Response({"detail": "Indica el tipo de vehículo."}, status=status.HTTP_400_BAD_REQUEST)
        placa = normalizar_placa(request.query_params.get("placa", ""))
        vehiculo = Vehiculo.objects.filter(placa=placa).first() if placa else None
        espacios = self.get_queryset().filter(estado=Espacio.Estado.DISPONIBLE).exclude(
            pk__in=espacios_reservados(excepto_vehiculo=vehiculo)
        )
        return Response(self.get_serializer(espacios, many=True).data)
