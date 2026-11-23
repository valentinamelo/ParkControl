"""
Reglas de negocio del cobro y la entrada (sección 7 de la planeación).
Se mantienen aparte de las vistas para poder probarlas con casos límite.
"""
import math

from django.utils import timezone

from apps.configuracion.models import Horario, Tarifa

MINUTOS_DIA = 24 * 60


def minutos_entre(entrada, salida):
    """Minutos completos transcurridos (2 h 45 min 30 s -> 165)."""
    return max(0, int((salida - entrada).total_seconds() // 60))


def calcular_valor(tarifa, minutos):
    """
    valor = min(⌈(minutos - gracia) / fracción⌉ × valor, tope_diario)

    Si los minutos no superan la gracia, el valor es 0. Para estadías de más de un día,
    cada día completo cobra el tope y el resto se calcula con la misma fórmula.
    """
    if minutos <= tarifa.minutos_gracia:
        return 0
    cobrables = minutos - tarifa.minutos_gracia

    def por_fracciones(m):
        return math.ceil(m / tarifa.minutos_fraccion) * int(tarifa.valor)

    if not tarifa.tope_diario:
        return por_fracciones(cobrables)
    tope = int(tarifa.tope_diario)
    dias, resto = divmod(cobrables, MINUTOS_DIA)
    return dias * tope + min(por_fracciones(resto), tope)


def tarifa_vigente(tipo_vehiculo):
    return Tarifa.objects.filter(tipo_vehiculo=tipo_vehiculo, vigente=True).first()


def dentro_de_horario(momento=None):
    """True si el parqueadero atiende en ese momento. Sin horario configurado para el día, no se restringe."""
    momento = timezone.localtime(momento or timezone.now())
    horario = Horario.objects.filter(dia_semana=momento.weekday()).first()
    if horario is None:
        return True
    return horario.abierto and horario.hora_apertura <= momento.time() < horario.hora_cierre
