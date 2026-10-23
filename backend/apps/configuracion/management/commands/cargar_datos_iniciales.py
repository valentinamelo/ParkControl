"""
Carga datos de prueba para desarrollo:

    python manage.py cargar_datos_iniciales

Es idempotente: se puede correr varias veces sin duplicar registros.
"""
from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.configuracion.models import Horario, Parqueadero, Tarifa, TipoVehiculo
from apps.espacios.models import Espacio, Zona
from apps.mensualidades.models import PlanMensual
from apps.operaciones.models import Tiquete
from apps.usuarios.models import Usuario
from apps.vehiculos.models import Vehiculo

USUARIOS = [
    # email, contraseña, nombre, apellido, rol
    ("admin@parkcontrol.com", "Admin123*", "Administrador", "ParkControl", Usuario.Rol.ADMIN),
    ("trabajador@parkcontrol.com", "Trabajador123*", "Trabajador", "Turno 1", Usuario.Rol.TRABAJADOR),
]

# zona, tipo, cantidad de espacios
ZONAS = [("A", "Carro", 5), ("B", "Carro", 5), ("C", "Moto", 5)]

VEHICULOS = [
    # placa, tipo, marca, modelo, color
    ("ABC123", "Carro", "Renault", "Logan", "Gris"),
    ("DEF456", "Carro", "Mazda", "3", "Rojo"),
    ("JKL321", "Carro", "Chevrolet", "Spark", "Blanco"),
    ("XYZ789", "Moto", "Yamaha", "FZ", "Negro"),
    ("MNO65F", "Moto", "Honda", "CB 125", "Azul"),
    ("GHI987", "Carro", "Kia", "Picanto", "Plata"),
]

# placa, espacio, minutos que lleva dentro
OCUPADOS = [
    ("ABC123", "A-02", 165),
    ("DEF456", "A-04", 70),
    ("JKL321", "B-05", 45),
    ("XYZ789", "C-01", 105),
    ("MNO65F", "C-03", 20),
]


class Command(BaseCommand):
    help = "Carga usuarios, tipos de vehículo, tarifas, horarios, espacios y vehículos de prueba."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Parqueadero
        Parqueadero.objects.get_or_create(pk=1, defaults={"nombre": "ParkControl", "direccion": "Pasto, Nariño"})

        # 2. Usuarios
        for email, clave, nombre, apellido, rol in USUARIOS:
            usuario, creado = Usuario.objects.get_or_create(
                email=email,
                defaults={"first_name": nombre, "last_name": apellido, "rol": rol, "is_staff": rol == Usuario.Rol.ADMIN,
                          "is_superuser": rol == Usuario.Rol.ADMIN},
            )
            if creado:
                usuario.set_password(clave)
                usuario.save()

        # 3. Tipos de vehículo y tarifas
        carro, _ = TipoVehiculo.objects.get_or_create(nombre="Carro")
        moto, _ = TipoVehiculo.objects.get_or_create(nombre="Moto")
        tipos = {"Carro": carro, "Moto": moto}
        Tarifa.objects.get_or_create(
            tipo_vehiculo=carro, vigente=True,
            defaults={"modalidad": Tarifa.Modalidad.HORA, "valor": 4000, "minutos_fraccion": 60,
                      "minutos_gracia": 0, "tope_diario": 30000},
        )
        Tarifa.objects.get_or_create(
            tipo_vehiculo=moto, vigente=True,
            defaults={"modalidad": Tarifa.Modalidad.HORA, "valor": 2000, "minutos_fraccion": 60,
                      "minutos_gracia": 0, "tope_diario": 15000},
        )

        # 4. Horarios: lunes a sábado 6:00-22:00, domingo 8:00-18:00
        for dia in range(7):
            apertura, cierre = (time(8), time(18)) if dia == 6 else (time(6), time(22))
            Horario.objects.get_or_create(dia_semana=dia, defaults={"hora_apertura": apertura, "hora_cierre": cierre})

        # 5. Zonas y espacios
        for nombre, tipo, cantidad in ZONAS:
            zona, _ = Zona.objects.get_or_create(nombre=nombre, defaults={"tipo_vehiculo": tipos[tipo]})
            for i in range(1, cantidad + 1):
                Espacio.objects.get_or_create(codigo=f"{nombre}-{i:02d}", defaults={"zona": zona})

        # 6. Planes de mensualidad
        PlanMensual.objects.get_or_create(nombre="Mensual carro", tipo_vehiculo=carro, defaults={"valor": 180000})
        PlanMensual.objects.get_or_create(nombre="Mensual moto", tipo_vehiculo=moto, defaults={"valor": 70000})

        # 7. Vehículos
        for placa, tipo, marca, modelo, color in VEHICULOS:
            Vehiculo.objects.get_or_create(
                placa=placa, defaults={"tipo_vehiculo": tipos[tipo], "marca": marca, "modelo": modelo, "color": color}
            )

        # 8. Vehículos dentro del parqueadero (tiquetes abiertos)
        trabajador = Usuario.objects.get(email="trabajador@parkcontrol.com")
        ahora = timezone.now()
        for n, (placa, codigo_espacio, minutos) in enumerate(OCUPADOS, start=1):
            espacio = Espacio.objects.get(codigo=codigo_espacio)
            vehiculo = Vehiculo.objects.get(placa=placa)
            _, creado = Tiquete.objects.get_or_create(
                codigo=f"PC-{n:06d}",
                defaults={"vehiculo": vehiculo, "espacio": espacio, "usuario_entrada": trabajador,
                          "fecha_entrada": ahora - timedelta(minutes=minutos)},
            )
            if creado:
                espacio.estado = Espacio.Estado.OCUPADO
                espacio.save()

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados."))
        self.stdout.write("  Administrador: admin@parkcontrol.com / Admin123*")
        self.stdout.write("  Trabajador:    trabajador@parkcontrol.com / Trabajador123*")
