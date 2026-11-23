from datetime import date, timedelta

from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.configuracion.models import Parqueadero, TipoVehiculo
from apps.espacios.models import Espacio
from apps.mensualidades.reglas import hoy, marcar_vencidas, vigentes_hoy
from apps.operaciones.models import Pago, Tiquete
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EsAdministrador
from parkcontrol.excepciones import ReglaNegocio

from . import consultas, exportar
from .models import Bitacora
from .serializers import BitacoraSerializer

MAX_DIAS_REPORTE = 366


def leer_fecha(texto, nombre, defecto):
    if not texto:
        return defecto
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ReglaNegocio(f"La fecha '{nombre}' debe tener el formato AAAA-MM-DD.")


# --- Dashboard (RF-20) ---

@api_view(["GET"])
def dashboard_resumen(request):
    """
    GET /api/dashboard/resumen/
    Ocupación en tiempo real e ingresos de hoy. El administrador ve todo el parqueadero;
    el trabajador ve los ingresos y movimientos de su turno (lo que él registró hoy).
    """
    fecha = hoy()
    es_admin = request.user.es_admin

    # Ocupación por tipo de vehículo (los inactivos no cuentan como espacios del parqueadero)
    por_tipo = []
    for tipo in TipoVehiculo.objects.annotate(
        total=Count("zonas__espacios", filter=~Q(zonas__espacios__estado=Espacio.Estado.INACTIVO)),
        ocupados=Count("zonas__espacios", filter=Q(zonas__espacios__estado=Espacio.Estado.OCUPADO)),
    ):
        if tipo.total:
            por_tipo.append({"tipo": tipo.nombre, "total": tipo.total, "ocupados": tipo.ocupados,
                             "disponibles": tipo.total - tipo.ocupados})
    total = sum(t["total"] for t in por_tipo)
    ocupados = sum(t["ocupados"] for t in por_tipo)

    # Ingresos de hoy (del turno, si es trabajador)
    pagos = consultas.filtrar_pagos(fecha, fecha, usuario=None if es_admin else request.user)
    resumen = consultas.resumen_ingresos(pagos, fecha, fecha)
    entradas = Tiquete.objects.filter(fecha_entrada__date=fecha)
    salidas = Tiquete.objects.filter(fecha_salida__date=fecha, estado=Tiquete.Estado.CERRADO)
    if not es_admin:
        entradas = entradas.filter(usuario_entrada=request.user)
        salidas = salidas.filter(usuario_salida=request.user)

    datos = {
        "alcance": "parqueadero" if es_admin else "turno",
        "fecha": fecha,
        "espacios": {
            "total": total,
            "ocupados": ocupados,
            "disponibles": total - ocupados,
            "inactivos": Espacio.objects.filter(estado=Espacio.Estado.INACTIVO).count(),
            "ocupacion": round(ocupados * 100 / total) if total else 0,
            "por_tipo": por_tipo,
        },
        "hoy": {
            "ingresos": resumen["total"],
            "pagos": resumen["cantidad"],
            "por_metodo": resumen["por_metodo"],
            "por_concepto": resumen["por_concepto"],
            "entradas": entradas.count(),
            "salidas": salidas.count(),
        },
    }

    if es_admin:
        marcar_vencidas()
        semana = fecha - timedelta(days=6)
        datos["semana"] = consultas.resumen_ingresos(consultas.filtrar_pagos(semana, fecha), semana, fecha)["por_dia"]
        datos["mensualidades"] = {
            "vigentes": vigentes_hoy().count(),
            "por_vencer": vigentes_hoy().filter(fecha_fin__lte=fecha + timedelta(days=5)).count(),
        }
    return Response(datos)


# --- Reporte de ingresos (RF-21, RF-22) ---

@api_view(["GET"])
@permission_classes([EsAdministrador])
def reporte_ingresos(request):
    """
    GET /api/reportes/ingresos/?desde=2026-11-01&hasta=2026-11-30&tipo=&metodo=&usuario=&concepto=&formato=json|pdf|xlsx
    Sin fechas, toma el día de hoy.
    """
    p = request.query_params
    desde = leer_fecha(p.get("desde"), "desde", hoy())
    hasta = leer_fecha(p.get("hasta"), "hasta", desde)
    if desde > hasta:
        raise ReglaNegocio("La fecha inicial no puede ser posterior a la final.")
    if (hasta - desde).days >= MAX_DIAS_REPORTE:
        raise ReglaNegocio("El rango máximo del reporte es de un año.")

    filtros, descripcion = {}, []
    if p.get("tipo"):
        tipo = TipoVehiculo.objects.filter(pk=p["tipo"]).first()
        if tipo is None:
            raise ReglaNegocio("El tipo de vehículo no existe.")
        filtros["tipo"] = tipo
        descripcion.append(f"tipo {tipo.nombre}")
    if p.get("metodo"):
        if p["metodo"] not in Pago.Metodo.values:
            raise ReglaNegocio("El método de pago no es válido.")
        filtros["metodo"] = p["metodo"]
        descripcion.append(f"método {Pago.Metodo(p['metodo']).label}")
    if p.get("usuario"):
        usuario = Usuario.objects.filter(pk=p["usuario"]).first()
        if usuario is None:
            raise ReglaNegocio("El trabajador no existe.")
        filtros["usuario"] = usuario
        descripcion.append(f"registrado por {usuario.get_full_name() or usuario.email}")
    if p.get("concepto"):
        if p["concepto"] not in consultas.CONCEPTOS:
            raise ReglaNegocio("El concepto debe ser PARQUEO o MENSUALIDAD.")
        filtros["concepto"] = p["concepto"]
        descripcion.append(consultas.CONCEPTOS[p["concepto"]].lower())

    reporte = consultas.resumen_ingresos(consultas.filtrar_pagos(desde, hasta, **filtros), desde, hasta)
    formato = p.get("formato", "json")
    if formato == "json":
        return Response(reporte)

    parqueadero, _ = Parqueadero.objects.get_or_create(pk=1)
    nombre = f"ingresos_{desde:%Y%m%d}_{hasta:%Y%m%d}"
    if formato == "pdf":
        contenido, tipo_mime, extension = exportar.reporte_pdf(reporte, parqueadero, ", ".join(descripcion)), "application/pdf", "pdf"
    elif formato == "xlsx":
        contenido = exportar.reporte_xlsx(reporte, parqueadero, ", ".join(descripcion))
        tipo_mime, extension = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    else:
        raise ReglaNegocio("El formato debe ser json, pdf o xlsx.")
    respuesta = HttpResponse(contenido, content_type=tipo_mime)
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}.{extension}"'
    return respuesta


# --- Bitácora (RF-23) ---

class PaginaBitacora(PageNumberPagination):
    page_size = 50


class BitacoraView(generics.ListAPIView):
    """GET /api/bitacora/?desde=&hasta=&usuario=&accion=&q=&page="""

    serializer_class = BitacoraSerializer
    permission_classes = [EsAdministrador]
    pagination_class = PaginaBitacora

    def get_queryset(self):
        p = self.request.query_params
        qs = Bitacora.objects.select_related("usuario")
        if p.get("desde"):
            qs = qs.filter(fecha__date__gte=leer_fecha(p["desde"], "desde", None))
        if p.get("hasta"):
            qs = qs.filter(fecha__date__lte=leer_fecha(p["hasta"], "hasta", None))
        if p.get("usuario"):
            qs = qs.filter(usuario=p["usuario"])
        if p.get("accion"):
            qs = qs.filter(accion=p["accion"])
        if p.get("q"):
            qs = qs.filter(detalle__icontains=p["q"])
        return qs


@api_view(["GET"])
@permission_classes([EsAdministrador])
def bitacora_acciones(request):
    """GET /api/bitacora/acciones/ -> acciones registradas, para el filtro."""
    return Response(list(Bitacora.objects.order_by("accion").values_list("accion", flat=True).distinct()))
