from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.operaciones.models import Pago
from apps.reportes.bitacora import BitacoraMixin, registrar
from apps.usuarios.permissions import AdminOSoloLectura
from apps.vehiculos.models import Cliente, Vehiculo
from apps.vehiculos.serializers import normalizar_placa
from parkcontrol.excepciones import ReglaNegocio

from .models import Mensualidad, PlanMensual
from .reglas import fecha_fin, hoy, marcar_vencidas
from .serializers import MensualidadSerializer, PlanMensualSerializer, RenovacionSerializer, VentaSerializer


class PlanMensualViewSet(BitacoraMixin, viewsets.ModelViewSet):
    """RF-16. GET ?activos=1 para los que se pueden vender. DELETE de un plan ya vendido solo lo desactiva."""

    serializer_class = PlanMensualSerializer
    permission_classes = [AdminOSoloLectura]
    nombre_bitacora = "PLAN_MENSUAL"

    def get_queryset(self):
        qs = PlanMensual.objects.select_related("tipo_vehiculo")
        if self.request.query_params.get("activos"):
            qs = qs.filter(activo=True)
        return qs

    def perform_destroy(self, instance):
        if instance.mensualidades.exists():
            instance.activo = False
            instance.save(update_fields=["activo"])
            registrar(self.request.user, "DESACTIVAR_PLAN_MENSUAL", str(instance))
        else:
            super().perform_destroy(instance)


class MensualidadViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    RF-17 (admin y trabajador):
    GET  /api/mensualidades/?estado=VIGENTE&q=ABC      lista (q busca placa, cliente o documento)
    POST /api/mensualidades/                            vende una mensualidad
    POST /api/mensualidades/{id}/renovar/               crea la siguiente, que empieza al vencer esta
    """

    serializer_class = MensualidadSerializer

    def get_queryset(self):
        qs = Mensualidad.objects.select_related(
            "cliente", "vehiculo__tipo_vehiculo", "plan", "espacio_fijo"
        ).prefetch_related("pagos")
        estado = self.request.query_params.get("estado")
        q = self.request.query_params.get("q", "").strip()
        if estado:
            qs = qs.filter(estado=estado.upper())
        if q:
            qs = qs.filter(
                Q(vehiculo__placa__icontains=normalizar_placa(q)) | Q(cliente__nombre__icontains=q) | Q(cliente__documento__icontains=q)
            )
        return qs

    def list(self, request, *args, **kwargs):
        marcar_vencidas()  # regla 3: también se verifica al consultar
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        venta = VentaSerializer(data=request.data)
        venta.is_valid(raise_exception=True)
        datos = venta.validated_data
        plan = datos["plan"]

        cliente, _ = Cliente.objects.get_or_create(
            documento=datos["documento"].strip(),
            defaults={"nombre": datos["nombre"].strip(), "telefono": datos["telefono"], "correo": datos["correo"]},
        )
        vehiculo, creado = Vehiculo.objects.get_or_create(placa=datos["placa"], defaults={"tipo_vehiculo": plan.tipo_vehiculo})
        if vehiculo.cliente_id != cliente.pk:
            vehiculo.cliente = cliente
            vehiculo.save(update_fields=["cliente"])

        mensualidad = Mensualidad.objects.create(
            cliente=cliente, vehiculo=vehiculo, plan=plan, espacio_fijo=datos.get("espacio_fijo"),
            fecha_inicio=datos["fecha_inicio"], fecha_fin=fecha_fin(datos["fecha_inicio"], plan),
        )
        Pago.objects.create(mensualidad=mensualidad, valor=plan.valor, metodo=datos["metodo"], usuario=request.user)
        registrar(request.user, "VENDER_MENSUALIDAD", f"{mensualidad} - {cliente} - ${plan.valor}")
        return Response(self.get_serializer(self.get_queryset().get(pk=mensualidad.pk)).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def renovar(self, request, pk=None):
        anterior = self.get_object()
        datos = RenovacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        plan = datos.validated_data.get("plan", anterior.plan)
        if not plan.activo:
            raise ReglaNegocio(f"El plan {plan.nombre} ya no se vende; elige otro.")
        if plan.tipo_vehiculo_id != anterior.vehiculo.tipo_vehiculo_id:
            raise ReglaNegocio(f"El plan {plan.nombre} no es para {anterior.vehiculo.tipo_vehiculo}.")

        ultima = anterior.vehiculo.mensualidades.order_by("-fecha_fin").first()
        if ultima.pk != anterior.pk:
            raise ReglaNegocio(f"Esta mensualidad ya fue renovada hasta el {ultima.fecha_fin:%d/%m/%Y}.")

        # Regla 2: la nueva empieza al vencer la anterior (o hoy, si ya venció)
        inicio = max(anterior.fecha_fin + timedelta(days=1), hoy())
        nueva = Mensualidad.objects.create(
            cliente=anterior.cliente, vehiculo=anterior.vehiculo, plan=plan, espacio_fijo=anterior.espacio_fijo,
            fecha_inicio=inicio, fecha_fin=fecha_fin(inicio, plan),
        )
        Pago.objects.create(mensualidad=nueva, valor=plan.valor, metodo=datos.validated_data["metodo"], usuario=request.user)
        registrar(request.user, "RENOVAR_MENSUALIDAD", f"{nueva} - {nueva.cliente} - ${plan.valor}")
        return Response(self.get_serializer(self.get_queryset().get(pk=nueva.pk)).data, status=status.HTTP_201_CREATED)
