"""
Códigos de tiquete no secuenciales.

Un código consecutivo (PC-000120) deja adivinar los de otros vehículos y falsificar un tiquete
más reciente para pagar menos. Por eso cada tiquete lleva la inicial del tipo de vehículo
(C- carro, M- moto) más 8 caracteres al azar (32^8, más de un billón de combinaciones),
generados con el módulo secrets.
"""
import re
import secrets
import unicodedata

# Sin 0/O ni 1/I, que se confunden al leerlos o escribirlos a mano
ALFABETO = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
LONGITUD = 8


def prefijo(tipo_vehiculo):
    """Inicial del tipo de vehículo sin tilde: Carro -> C, Moto -> M, Bicicleta -> B."""
    inicial = unicodedata.normalize("NFKD", tipo_vehiculo.nombre)[:1].upper()
    return inicial if "A" <= inicial <= "Z" else "V"


def generar_codigo(tipo_vehiculo):
    """Un código nuevo, con el prefijo del tipo de vehículo, que todavía no tiene ningún tiquete."""
    from .models import Tiquete

    while True:
        codigo = f"{prefijo(tipo_vehiculo)}-" + "".join(secrets.choice(ALFABETO) for _ in range(LONGITUD))
        if not Tiquete.objects.filter(codigo=codigo).exists():
            return codigo


def normalizar_codigo(texto):
    """
    "c-7k4m2qxr", "C7K4M2QXR" o "C'7K4M2QXR" (lector con otra distribución de teclado)
    -> "C-7K4M2QXR". También reconoce los formatos anteriores: PC-7K4M2QXR y PC-000123.
    """
    limpio = re.sub(r"[^A-Z0-9]", "", texto.upper())
    if re.fullmatch(rf"[A-Z][A-Z0-9]{{{LONGITUD}}}", limpio):
        return f"{limpio[0]}-{limpio[1:]}"
    if re.fullmatch(rf"PC([A-Z0-9]{{{LONGITUD}}}|\d{{6}})", limpio):
        return f"PC-{limpio[2:]}"
    return texto.strip().upper()
