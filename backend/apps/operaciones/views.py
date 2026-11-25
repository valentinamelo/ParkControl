from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.configuracion.models import Parqueadero
from apps.espacios.models import Espacio
from apps.mensualidades.reglas import espacios_reservados, mensualidad_vigente
from apps.reportes.bitacora import registrar
from apps.usuarios.permissions import EsAdministrador
from apps.vehiculos.models import Vehiculo
from apps.vehiculos.serializers import normalizar_placa
from parkcontrol.excepciones import ReglaNegocio

from .codigos import generar_codigo, normalizar_codigo
from .models import Pago, Tiquete
from .reglas import calcular_cobro, dentro_de_horario, horarios_por_dia, segundos_entre, tarifa_vigente
from .serializers import AnulacionSerializer, EntradaSerializer, SalidaSerializer, TiqueteSerializer


class TiqueteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/tiquetes/?estado=&placa=      historial (últimos 100)
    GET  /api/tiquetes/activos/?placa=      vehículos dentro (RF-19)
    GET  /api/tiquetes/{codigo}/?perdido=1  previsualiza el cobro (RF-14)
    POST /api/tiquetes/entrada/             registra la entrada (RF-11, RF-12, RF-18)
    POST /api/tiquetes/{codigo}/salida/     cobra y libera el espacio (RF-13, RF-15)
    POST /api/tiquetes/{codigo}/anular/     solo admin, con motivo (RF-24)
    """

    serializer_class = TiqueteSerializer
    lookup_field = "codigo"

    def get_queryset(self):
        qs = Tiquete.objects.select_related(
            "vehiculo__tipo_vehiculo", "espacio", "usuario_entrada", "usuario_salida", "pago"
        )
        estado = self.request.query_params.get("estado")
        placa = self.request.query_params.get("placa")
        if estado:
            qs = qs.filter(estado=estado.upper())
        if placa:
            qs = qs.filter(vehiculo__placa__icontains=normalizar_placa(placa))
        return qs

    def list(self, request, *args, **kwargs):
        tiquetes = self.get_queryset()[:100]
        return Response(self.get_serializer(tiquetes, many=True).data)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), codigo=normalizar_codigo(self.kwargs["codigo"]))

    # --- Consultas ---

    @action(detail=False)
    def activos(self, request):
        tiquetes = self.get_queryset().filter(estado=Tiquete.Estado.ABIERTO).order_by("fecha_entrada")
        datos = self.get_serializer(tiquetes, many=True).data
        # Valor que pagaría si saliera ahora (orientativo; el definitivo se calcula al dar salida)
        horarios = horarios_por_dia()
        for tiquete, fila in zip(tiquetes, datos):
            fila["valor_actual"] = self._cobro(tiquete, horarios=horarios)["valor"]
        return Response(datos)

    def retrieve(self, request, *args, **kwargs):
        tiquete = self.get_object()
        datos = self.get_serializer(tiquete).data
        if tiquete.estado == Tiquete.Estado.ABIERTO:
            datos["cobro"] = self._cobro(tiquete, perdido=bool(request.query_params.get("perdido")))
        return Response(datos)

    @action(detail=False, url_path="consultar-placa")
    def consultar_placa(self, request):
        """
        GET /api/tiquetes/consultar-placa/?placa=ABC123
        Lo que la pantalla de entrada necesita saber de una placa antes de registrarla.
        """
        placa = normalizar_placa(request.query_params.get("placa", ""))
        vehiculo = Vehiculo.objects.select_related("tipo_vehiculo").filter(placa=placa).first()
        respuesta = {"placa": placa, "vehiculo": None, "tiquete_abierto": None, "mensualidad": None}
        if vehiculo is None:
            return Response(respuesta)
        respuesta["vehiculo"] = {
            "id": vehiculo.pk, "tipo_vehiculo": vehiculo.tipo_vehiculo_id,
            "tipo_vehiculo_nombre": vehiculo.tipo_vehiculo.nombre,
            "marca": vehiculo.marca, "modelo": vehiculo.modelo, "color": vehiculo.color,
        }
        abierto = vehiculo.tiquetes.filter(estado=Tiquete.Estado.ABIERTO).select_related("espacio").first()
        if abierto:
            respuesta["tiquete_abierto"] = {"codigo": abierto.codigo, "espacio": abierto.espacio.codigo}
        mensualidad = mensualidad_vigente(vehiculo)
        if mensualidad:
            respuesta["mensualidad"] = {
                "id": mensualidad.pk, "cliente": mensualidad.cliente.nombre, "fecha_fin": mensualidad.fecha_fin,
                "espacio_fijo": mensualidad.espacio_fijo.codigo if mensualidad.espacio_fijo else None,
                "espacio_fijo_id": mensualidad.espacio_fijo_id,
            }
        return Response(respuesta)

    def _cobro(self, tiquete, perdido=False, momento=None, horarios=None):
        """
        Tiempo, valor según la tarifa vigente (con pernoctación si la tiene) y multa.
        Mensualidad vigente: $0 (RF-18).
        """
        momento = momento or timezone.now()
        tarifa = None if tiquete.es_mensualidad else tarifa_vigente(tiquete.vehiculo.tipo_vehiculo)
        if tarifa:
            cobro = calcular_cobro(tarifa, tiquete.fecha_entrada, momento, horarios)
        else:
            segundos = segundos_entre(tiquete.fecha_entrada, momento)
            cobro = {"segundos": segundos, "minutos": segundos // 60, "minutos_cobrados": 0, "noches": 0,
                     "valor_tiempo": 0, "valor_noches": 0, "valor": 0}
        multa = int(Parqueadero.objects.get_or_create(pk=1)[0].multa_tiquete_perdido) if perdido else 0
        return {
            **cobro,
            "tarifa": str(tarifa) if tarifa else None,
            "valor_pernoctacion": int(tarifa.valor_pernoctacion) if tarifa and tarifa.valor_pernoctacion else None,
            "sin_tarifa": tarifa is None and not tiquete.es_mensualidad,
            "multa": multa,
            "total": cobro["valor"] + multa,
        }

    # --- Entrada ---

    @action(detail=False, methods=["post"])
    def entrada(self, request):
        serializer = EntradaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        # Fuera de horario: el trabajador no puede; el admin puede confirmar y registrarla igual
        if not dentro_de_horario():
            if not (request.user.es_admin and datos["forzar"]):
                return Response(
                    {"detail": "El parqueadero está fuera del horario de atención."
                    + (" Confirma si quieres registrar la entrada de todas formas." if request.user.es_admin
                       else " Solo el administrador puede autorizar esta entrada."),
                     "fuera_de_horario": True},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            vehiculo = Vehiculo.objects.select_related("tipo_vehiculo").filter(placa=datos["placa"]).first()
            tipo = datos.get("tipo_vehiculo")
            if vehiculo is None:
                if tipo is None:
                    raise ReglaNegocio("Es un vehículo nuevo: indica si es carro o moto.")
                vehiculo = Vehiculo.objects.create(
                    placa=datos["placa"], tipo_vehiculo=tipo,
                    marca=datos["marca"], modelo=datos["modelo"], color=datos["color"],
                )
                registrar(request.user, "CREAR_VEHICULO", str(vehiculo))
            elif tipo is not None and tipo != vehiculo.tipo_vehiculo:
                raise ReglaNegocio(f"El vehículo {vehiculo.placa} está registrado como {vehiculo.tipo_vehiculo}.")

            # Regla 1: una placa no puede tener otro tiquete abierto
            abierto = vehiculo.tiquetes.filter(estado=Tiquete.Estado.ABIERTO).first()
            if abierto:
                raise ReglaNegocio(f"El vehículo {vehiculo.placa} ya está dentro con el tiquete {abierto.codigo}.")

            # Regla 5: mensualidad vigente -> no se cobra y usa su espacio fijo si está libre
            mensualidad = mensualidad_vigente(vehiculo)
            if mensualidad is None and tarifa_vigente(vehiculo.tipo_vehiculo) is None:
                raise ReglaNegocio(f"No hay tarifa vigente para {vehiculo.tipo_vehiculo}. El administrador debe configurarla.")

            # Regla 2: solo espacios DISPONIBLES del mismo tipo (y no reservados para otra mensualidad)
            libres = (
                Espacio.objects.select_for_update()
                .filter(estado=Espacio.Estado.DISPONIBLE, zona__tipo_vehiculo=vehiculo.tipo_vehiculo)
                .exclude(pk__in=espacios_reservados(excepto_vehiculo=vehiculo))
                .order_by("codigo")
            )
            if "espacio" in datos:
                espacio = libres.filter(pk=datos["espacio"].pk).first()
                if espacio is None:
                    raise ReglaNegocio(f"El espacio {datos['espacio'].codigo} no está disponible para {vehiculo.tipo_vehiculo}.")
            else:
                fijo = mensualidad.espacio_fijo_id if mensualidad else None
                espacio = (fijo and libres.filter(pk=fijo).first()) or libres.first()
                if espacio is None:
                    raise ReglaNegocio(f"No hay espacios disponibles para {vehiculo.tipo_vehiculo}.")

            # Regla 6: el espacio pasa a OCUPADO y se genera el código del tiquete (aleatorio, no consecutivo)
            tiquete = Tiquete.objects.create(
                codigo=generar_codigo(vehiculo.tipo_vehiculo), vehiculo=vehiculo, espacio=espacio,
                fecha_entrada=timezone.now(), es_mensualidad=mensualidad is not None, usuario_entrada=request.user,
            )
            espacio.estado = Espacio.Estado.OCUPADO
            espacio.save(update_fields=["estado"])
            registrar(
                request.user, "ENTRADA",
                f"{tiquete.codigo} {vehiculo.placa} en {espacio.codigo}" + (" (mensualidad)" if mensualidad else ""),
            )

        return Response(self.get_serializer(self.get_queryset().get(pk=tiquete.pk)).data, status=status.HTTP_201_CREATED)

    # --- Salida ---

    @action(detail=True, methods=["post"])
    def salida(self, request, codigo=None):
        serializer = SalidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        with transaction.atomic():
            tiquete = get_object_or_404(
                Tiquete.objects.select_for_update().select_related("vehiculo__tipo_vehiculo", "espacio"),
                codigo=normalizar_codigo(codigo),
            )
            if tiquete.estado != Tiquete.Estado.ABIERTO:
                raise ReglaNegocio(f"El tiquete {tiquete.codigo} ya está {tiquete.get_estado_display().lower()}.")

            ahora = timezone.now()
            cobro = self._cobro(tiquete, perdido=datos["tiquete_perdido"], momento=ahora)
            if cobro["sin_tarifa"]:
                raise ReglaNegocio(f"No hay tarifa vigente para {tiquete.vehiculo.tipo_vehiculo}.")
            if cobro["total"] > 0 and "metodo" not in datos:
                raise ReglaNegocio("Indica el método de pago.")

            tiquete.fecha_salida = ahora
            tiquete.minutos = cobro["minutos"]
            tiquete.segundos = cobro["segundos"]
            tiquete.valor = cobro["total"]
            tiquete.multa = cobro["multa"]
            tiquete.noches = cobro["noches"]
            tiquete.estado = Tiquete.Estado.CERRADO
            tiquete.usuario_salida = request.user
            tiquete.save()
            if cobro["total"] > 0:
                Pago.objects.create(tiquete=tiquete, valor=cobro["total"], metodo=datos["metodo"], usuario=request.user)

            espacio = tiquete.espacio
            if espacio.estado == Espacio.Estado.OCUPADO:
                espacio.estado = Espacio.Estado.DISPONIBLE
                espacio.save(update_fields=["estado"])
            registrar(
                request.user, "SALIDA",
                f"{tiquete.codigo} {tiquete.vehiculo.placa} ${cobro['total']}"
                + (" (tiquete perdido)" if datos["tiquete_perdido"] else "")
                + (" (mensualidad)" if tiquete.es_mensualidad else ""),
            )

        return Response(self.get_serializer(self.get_queryset().get(pk=tiquete.pk)).data)

    # --- Anulación (RF-24) ---

    @action(detail=True, methods=["post"], permission_classes=[EsAdministrador])
    def anular(self, request, codigo=None):
        """
        Un tiquete abierto se anula y libera su espacio (p. ej. se registró por error).
        Uno cerrado se anula para corregir un cobro: su pago deja de contar en los ingresos.
        """
        serializer = AnulacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motivo = serializer.validated_data["motivo"]

        with transaction.atomic():
            tiquete = get_object_or_404(
                Tiquete.objects.select_for_update().select_related("vehiculo", "espacio"), codigo=normalizar_codigo(codigo)
            )
            if tiquete.estado == Tiquete.Estado.ANULADO:
                raise ReglaNegocio(f"El tiquete {tiquete.codigo} ya está anulado.")
            estaba_abierto = tiquete.estado == Tiquete.Estado.ABIERTO
            tiquete.estado = Tiquete.Estado.ANULADO
            tiquete.motivo_anulacion = motivo
            if estaba_abierto:
                tiquete.fecha_salida = timezone.now()
                tiquete.usuario_salida = request.user
                if tiquete.espacio.estado == Espacio.Estado.OCUPADO:
                    tiquete.espacio.estado = Espacio.Estado.DISPONIBLE
                    tiquete.espacio.save(update_fields=["estado"])
            tiquete.save()
            registrar(
                request.user, "ANULAR_TIQUETE",
                f"{tiquete.codigo} {tiquete.vehiculo.placa} ({'abierto' if estaba_abierto else f'cerrado, ${tiquete.valor}'}): {motivo}",
            )

        return Response(self.get_serializer(self.get_queryset().get(pk=tiquete.pk)).data)
