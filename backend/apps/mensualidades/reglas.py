"""Vigencia de las mensualidades (sección 7 de la planeación)."""
from datetime import timedelta

from django.utils import timezone

from .models import Mensualidad


def hoy():
    return timezone.localdate()


def fecha_fin(fecha_inicio, plan):
    """Un plan de 30 días que empieza el 1 cubre hasta el 30, inclusive."""
    return fecha_inicio + timedelta(days=plan.dias - 1)


def marcar_vencidas():
    """Pasa a VENCIDA las mensualidades cuya fecha final ya pasó. Devuelve cuántas cambió."""
    return Mensualidad.objects.filter(estado=Mensualidad.Estado.VIGENTE, fecha_fin__lt=hoy()).update(
        estado=Mensualidad.Estado.VENCIDA
    )


def mensualidad_vigente(vehiculo, fecha=None):
    """La mensualidad que cubre al vehículo en esa fecha, o None."""
    fecha = fecha or hoy()
    return (
        Mensualidad.objects.filter(
            vehiculo=vehiculo, estado=Mensualidad.Estado.VIGENTE, fecha_inicio__lte=fecha, fecha_fin__gte=fecha
        )
        .select_related("plan", "espacio_fijo", "cliente")
        .first()
    )


def vigentes_hoy():
    fecha = hoy()
    return Mensualidad.objects.filter(estado=Mensualidad.Estado.VIGENTE, fecha_inicio__lte=fecha, fecha_fin__gte=fecha)


def espacios_reservados(excepto_vehiculo=None):
    """Ids de los espacios fijos de mensualidades vigentes: no se ofrecen a otros vehículos."""
    qs = vigentes_hoy().filter(espacio_fijo__isnull=False)
    if excepto_vehiculo is not None:
        qs = qs.exclude(vehiculo=excepto_vehiculo)
    return qs.values("espacio_fijo")
