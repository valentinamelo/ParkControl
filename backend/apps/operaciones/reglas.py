"""
Reglas de negocio del cobro y la entrada (sección 7 de la planeación).
Se mantienen aparte de las vistas para poder probarlas con casos límite.
"""
import math
from datetime import datetime, time, timedelta

from django.utils import timezone

from apps.configuracion.models import Horario, Tarifa

MINUTOS_DIA = 24 * 60


def minutos_entre(entrada, salida):
    """Minutos completos transcurridos (2 h 45 min 30 s -> 165)."""
    return max(0, int((salida - entrada).total_seconds() // 60))


def calcular_valor(tarifa, minutos):
    """
    valor = min(⌈(minutos - gracia) / fracción⌉ × valor, tope_diario)

    Con valor de primera hora, la primera hora empezada cuesta ese valor y el resto se cobra
    por horas o fracciones: $5.000 la primera hora y $1.000 cada 15 minutos, 1 h 20 min -> $7.000.

    Si los minutos no superan la gracia, el valor es 0. Para estadías de más de un día,
    cada día completo cobra el tope y el resto se calcula con la misma fórmula (la primera hora
    se cobra una sola vez, al inicio de la estadía).
    """
    if minutos <= tarifa.minutos_gracia:
        return 0
    cobrables = minutos - tarifa.minutos_gracia

    def por_tiempo(m, con_primera_hora):
        if con_primera_hora and tarifa.valor_primera_hora:
            return int(tarifa.valor_primera_hora) + por_tiempo(max(0, m - 60), False)
        return math.ceil(m / tarifa.minutos_fraccion) * int(tarifa.valor)

    if not tarifa.tope_diario:
        return por_tiempo(cobrables, True)
    tope = int(tarifa.tope_diario)
    dias, resto = divmod(cobrables, MINUTOS_DIA)
    return dias * tope + min(por_tiempo(resto, dias == 0), tope)


def tarifa_vigente(tipo_vehiculo):
    return Tarifa.objects.filter(tipo_vehiculo=tipo_vehiculo, vigente=True).first()


def horarios_por_dia():
    """{0: Horario del lunes, ..., 6: Horario del domingo}"""
    return {h.dia_semana: h for h in Horario.objects.all()}


def _abierto(horarios, momento):
    horario = horarios.get(momento.weekday())
    if horario is None:  # sin horario configurado para el día, no se restringe
        return True
    return horario.abierto and horario.hora_apertura <= momento.time() < horario.hora_cierre


def dentro_de_horario(momento=None):
    """True si el parqueadero atiende en ese momento."""
    return _abierto(horarios_por_dia(), timezone.localtime(momento or timezone.now()))


def tiempo_en_horario(entrada, salida, horarios=None):
    """
    Divide una estadía en (minutos dentro del horario de atención, noches).
    Una noche es cada medianoche que el vehículo pasa dentro con el parqueadero cerrado:
    de lunes 20:00 a martes 08:00 con horario 06:00-22:00 son 240 minutos y 1 noche.
    """
    horarios = horarios_por_dia() if horarios is None else horarios
    zona = timezone.get_current_timezone()
    entrada, salida = timezone.localtime(entrada), timezone.localtime(salida)
    if salida <= entrada:
        return 0, 0

    def momento(dia, hora):
        return timezone.make_aware(datetime.combine(dia, hora), zona)

    segundos = 0
    dia = entrada.date()
    while dia <= salida.date():
        horario = horarios.get(dia.weekday())
        if horario is None:
            inicio, fin = momento(dia, time.min), momento(dia + timedelta(days=1), time.min)
        elif horario.abierto:
            inicio, fin = momento(dia, horario.hora_apertura), momento(dia, horario.hora_cierre)
        else:
            inicio = fin = None
        if inicio is not None:
            segundos += max(0, (min(fin, salida) - max(inicio, entrada)).total_seconds())
        dia += timedelta(days=1)

    noches = 0
    medianoche = momento(entrada.date() + timedelta(days=1), time.min)
    while medianoche < salida:
        if not _abierto(horarios, medianoche):
            noches += 1
        medianoche += timedelta(days=1)
    return int(segundos // 60), noches


def calcular_cobro(tarifa, entrada, salida, horarios=None):
    """
    Cobro de una estadía con la tarifa dada (RF-14).

    Si la tarifa tiene pernoctación, las horas se cobran solo dentro del horario de atención
    y cada noche con el parqueadero cerrado se cobra aparte. Si no, se cobra el tiempo corrido.
    """
    minutos = minutos_entre(entrada, salida)
    if tarifa.valor_pernoctacion:
        cobrables, noches = tiempo_en_horario(entrada, salida, horarios)
    else:
        cobrables, noches = minutos, 0
    valor_tiempo = calcular_valor(tarifa, cobrables)
    valor_noches = noches * int(tarifa.valor_pernoctacion or 0)
    return {
        "minutos": minutos,
        "minutos_cobrados": cobrables,
        "noches": noches,
        "valor_tiempo": valor_tiempo,
        "valor_noches": valor_noches,
        "valor": valor_tiempo + valor_noches,
    }
