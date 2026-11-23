"""
Consultas de ingresos para el dashboard y los reportes (RF-20, RF-21).
Un ingreso es un Pago: de un tiquete (parqueo) o de una mensualidad. Los pagos de tiquetes
anulados no cuentan.
"""
from collections import defaultdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.operaciones.models import Pago, Tiquete

PARQUEO = "PARQUEO"
MENSUALIDAD = "MENSUALIDAD"
CONCEPTOS = {PARQUEO: "Parqueo", MENSUALIDAD: "Mensualidad"}


def pagos_validos():
    return (
        Pago.objects.select_related(
            "usuario", "tiquete__vehiculo__tipo_vehiculo", "mensualidad__vehiculo__tipo_vehiculo", "mensualidad__plan"
        )
        .exclude(tiquete__estado=Tiquete.Estado.ANULADO)
        .order_by("fecha")
    )


def filtrar_pagos(desde, hasta, tipo=None, metodo=None, usuario=None, concepto=None):
    """Pagos entre dos fechas locales (inclusive), con filtros opcionales."""
    qs = pagos_validos().filter(fecha__date__gte=desde, fecha__date__lte=hasta)
    if tipo:
        qs = qs.filter(Q(tiquete__vehiculo__tipo_vehiculo=tipo) | Q(mensualidad__vehiculo__tipo_vehiculo=tipo))
    if metodo:
        qs = qs.filter(metodo=metodo)
    if usuario:
        qs = qs.filter(usuario=usuario)
    if concepto == PARQUEO:
        qs = qs.filter(tiquete__isnull=False)
    elif concepto == MENSUALIDAD:
        qs = qs.filter(mensualidad__isnull=False)
    return qs


def fila(pago):
    """Un pago como fila del reporte."""
    if pago.tiquete_id:
        vehiculo, concepto, referencia = pago.tiquete.vehiculo, PARQUEO, pago.tiquete.codigo
    else:
        vehiculo, concepto, referencia = pago.mensualidad.vehiculo, MENSUALIDAD, pago.mensualidad.plan.nombre
    return {
        "fecha": timezone.localtime(pago.fecha),
        "concepto": CONCEPTOS[concepto],
        "referencia": referencia,
        "placa": vehiculo.placa,
        "tipo_vehiculo": vehiculo.tipo_vehiculo.nombre,
        "metodo": pago.get_metodo_display(),
        "usuario": pago.usuario.get_full_name() or pago.usuario.email,
        "valor": int(pago.valor),
    }


def _agrupar(filas, clave):
    grupos = defaultdict(lambda: {"total": 0, "cantidad": 0})
    for f in filas:
        grupos[clave(f)]["total"] += f["valor"]
        grupos[clave(f)]["cantidad"] += 1
    return [{"nombre": nombre, **datos} for nombre, datos in sorted(grupos.items(), key=lambda g: -g[1]["total"])]


def resumen_ingresos(pagos, desde, hasta):
    """Total y desgloses por día, tipo de vehículo, método de pago, trabajador y concepto."""
    filas = [fila(p) for p in pagos]
    dias = defaultdict(lambda: {"total": 0, "cantidad": 0})
    for f in filas:
        dias[f["fecha"].date()]["total"] += f["valor"]
        dias[f["fecha"].date()]["cantidad"] += 1
    # Todos los días del rango, también los que no tuvieron ingresos
    por_dia = []
    dia = desde
    while dia <= hasta:
        por_dia.append({"fecha": dia, **dias.get(dia, {"total": 0, "cantidad": 0})})
        dia += timedelta(days=1)

    return {
        "desde": desde,
        "hasta": hasta,
        "total": sum(f["valor"] for f in filas),
        "cantidad": len(filas),
        "por_dia": por_dia,
        "por_tipo": _agrupar(filas, lambda f: f["tipo_vehiculo"]),
        "por_metodo": _agrupar(filas, lambda f: f["metodo"]),
        "por_usuario": _agrupar(filas, lambda f: f["usuario"]),
        "por_concepto": _agrupar(filas, lambda f: f["concepto"]),
        "detalle": filas,
    }
