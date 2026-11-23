from datetime import time, timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from apps.configuracion.models import Horario, Parqueadero, Tarifa, TipoVehiculo
from apps.espacios.models import Espacio
from apps.reportes.models import Bitacora
from apps.usuarios.tests import ApiTestBase

from .models import Pago, Tiquete
from .reglas import calcular_valor, minutos_entre


def tarifa(valor=4000, fraccion=60, gracia=0, tope=None):
    return Tarifa(valor=valor, minutos_fraccion=fraccion, minutos_gracia=gracia, tope_diario=tope)


class CalculoTarifaTests(SimpleTestCase):
    """RF-14: valor = min(⌈(minutos - gracia) / fracción⌉ × valor, tope_diario)."""

    def test_ejemplo_de_la_planeacion(self):
        # 2 h 45 min a $4.000 la hora -> 3 horas -> $12.000
        self.assertEqual(calcular_valor(tarifa(), 165), 12000)

    def test_limites_de_la_fraccion(self):
        self.assertEqual(calcular_valor(tarifa(), 0), 0)
        self.assertEqual(calcular_valor(tarifa(), 1), 4000)
        self.assertEqual(calcular_valor(tarifa(), 60), 4000)
        self.assertEqual(calcular_valor(tarifa(), 61), 8000)

    def test_gracia(self):
        t = tarifa(gracia=10)
        self.assertEqual(calcular_valor(t, 10), 0)  # no supera la gracia
        self.assertEqual(calcular_valor(t, 11), 4000)
        self.assertEqual(calcular_valor(t, 70), 4000)  # 60 cobrables
        self.assertEqual(calcular_valor(t, 71), 8000)

    def test_por_fraccion(self):
        t = tarifa(valor=1000, fraccion=15)
        self.assertEqual(calcular_valor(t, 15), 1000)
        self.assertEqual(calcular_valor(t, 16), 2000)
        self.assertEqual(calcular_valor(t, 100), 7000)

    def test_tope_diario(self):
        t = tarifa(tope=30000)
        self.assertEqual(calcular_valor(t, 7 * 60), 28000)
        self.assertEqual(calcular_valor(t, 8 * 60), 30000)
        self.assertEqual(calcular_valor(t, 23 * 60), 30000)

    def test_mas_de_un_dia_cobra_tope_por_dia(self):
        t = tarifa(tope=30000)
        self.assertEqual(calcular_valor(t, 24 * 60), 30000)
        self.assertEqual(calcular_valor(t, 24 * 60 + 30), 34000)
        self.assertEqual(calcular_valor(t, 2 * 24 * 60 + 600), 90000)

    def test_minutos_completos(self):
        entrada = timezone.now()
        self.assertEqual(minutos_entre(entrada, entrada + timedelta(minutes=165, seconds=59)), 165)
        self.assertEqual(minutos_entre(entrada, entrada - timedelta(minutes=5)), 0)


class OperacionTestBase(ApiTestBase):
    def setUp(self):
        # Las pruebas no deben depender de la hora a la que se corren
        Horario.objects.update(abierto=True, hora_apertura=time(0), hora_cierre=time(23, 59, 59))
        self.carro = TipoVehiculo.objects.get(nombre="Carro")
        self.moto = TipoVehiculo.objects.get(nombre="Moto")

    def entrada(self, **datos):
        return self.client.post("/api/tiquetes/entrada/", datos, format="json")

    def atrasar(self, codigo, minutos):
        """Simula que el vehículo entró hace `minutos`."""
        Tiquete.objects.filter(codigo=codigo).update(fecha_entrada=timezone.now() - timedelta(minutes=minutos))


class EntradaTests(OperacionTestBase):
    """RF-11 y RF-12."""

    def setUp(self):
        super().setUp()
        self.como_trabajador()

    def test_entrada_de_vehiculo_registrado(self):
        r = self.entrada(placa="ghi-987")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["codigo"], "PC-000006")  # consecutivo después de los 5 del fixture
        self.assertEqual(r.data["placa"], "GHI987")
        self.assertEqual(r.data["espacio"], "A-01")  # primer espacio de carro libre
        self.assertEqual(Espacio.objects.get(codigo="A-01").estado, "OCUPADO")
        self.assertFalse(r.data["es_mensualidad"])
        self.assertTrue(Bitacora.objects.filter(accion="ENTRADA", detalle__contains="GHI987").exists())

    def test_vehiculo_nuevo_se_registra_en_la_entrada(self):
        r = self.entrada(placa="NUE12A")
        self.assertEqual(r.status_code, 400)
        r = self.entrada(placa="NUE12A", tipo_vehiculo=self.moto.pk, marca="Honda")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["espacio"].startswith("C-"))
        self.assertEqual(r.data["vehiculo_descripcion"], "Honda")

    def test_espacio_elegido(self):
        b02 = Espacio.objects.get(codigo="B-02")
        r = self.entrada(placa="GHI987", espacio=b02.pk)
        self.assertEqual(r.data["espacio"], "B-02")

    def test_espacio_no_compatible_u_ocupado(self):
        c02 = Espacio.objects.get(codigo="C-02")  # de moto
        self.assertEqual(self.entrada(placa="GHI987", espacio=c02.pk).status_code, 400)
        a02 = Espacio.objects.get(codigo="A-02")  # ocupado
        self.assertEqual(self.entrada(placa="GHI987", espacio=a02.pk).status_code, 400)

    def test_placa_con_tiquete_abierto(self):
        r = self.entrada(placa="ABC123")
        self.assertEqual(r.status_code, 400)
        self.assertIn("PC-000001", r.data["detail"])

    def test_tipo_distinto_al_registrado(self):
        r = self.entrada(placa="GHI987", tipo_vehiculo=self.moto.pk)
        self.assertEqual(r.status_code, 400)

    def test_sin_espacios_disponibles(self):
        Espacio.objects.filter(zona__tipo_vehiculo=self.carro, estado="DISPONIBLE").update(estado="INACTIVO")
        r = self.entrada(placa="GHI987")
        self.assertIn("No hay espacios", r.data["detail"])

    def test_error_deshace_el_vehiculo_nuevo(self):
        Tarifa.objects.filter(tipo_vehiculo=self.moto).update(vigente=False)
        r = self.entrada(placa="SIN12T", tipo_vehiculo=self.moto.pk)
        self.assertIn("tarifa", r.data["detail"])
        self.assertFalse(Tiquete.objects.filter(vehiculo__placa="SIN12T").exists())
        self.assertEqual(self.client.get("/api/vehiculos/?placa=SIN12T").data, [])

    def test_fuera_de_horario(self):
        Horario.objects.update(abierto=False)
        r = self.entrada(placa="GHI987", forzar=True)
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.data["fuera_de_horario"])
        # El admin puede confirmarla
        self.como_admin()
        self.assertEqual(self.entrada(placa="GHI987").status_code, 400)
        self.assertEqual(self.entrada(placa="GHI987", forzar=True).status_code, 201)

    def test_consultar_placa(self):
        r = self.client.get("/api/tiquetes/consultar-placa/?placa=abc123").data
        self.assertEqual(r["vehiculo"]["tipo_vehiculo_nombre"], "Carro")
        self.assertEqual(r["tiquete_abierto"]["codigo"], "PC-000001")
        self.assertIsNone(self.client.get("/api/tiquetes/consultar-placa/?placa=NOEXISTE").data["vehiculo"])

    def test_disponibles_por_tipo(self):
        r = self.client.get("/api/espacios/disponibles/?tipo=Moto")
        self.assertEqual([e["codigo"] for e in r.data], ["C-02", "C-04", "C-05"])


class SalidaTests(OperacionTestBase):
    """RF-13, RF-14, RF-15 y RF-19."""

    def setUp(self):
        super().setUp()
        self.como_trabajador()
        self.codigo = self.entrada(placa="GHI987").data["codigo"]
        self.atrasar(self.codigo, 165)

    def test_previsualiza_el_cobro(self):
        r = self.client.get(f"/api/tiquetes/{self.codigo.lower()}/")
        self.assertEqual(r.data["cobro"]["minutos"], 165)
        self.assertEqual(r.data["cobro"]["valor"], 12000)
        self.assertEqual(r.data["cobro"]["total"], 12000)
        self.assertEqual(Tiquete.objects.get(codigo=self.codigo).estado, "ABIERTO")  # solo consulta

    def test_salida_cobra_y_libera(self):
        r = self.client.post(f"/api/tiquetes/{self.codigo}/salida/", {"metodo": "TARJETA"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["estado"], "CERRADO")
        self.assertEqual(r.data["valor"], "12000")
        self.assertEqual(r.data["metodo_pago"], "Tarjeta")
        self.assertEqual(r.data["usuario_salida"], "Trabajador Turno 1")
        self.assertEqual(Pago.objects.get(tiquete__codigo=self.codigo).valor, 12000)
        self.assertEqual(Espacio.objects.get(codigo="A-01").estado, "DISPONIBLE")
        self.assertTrue(Bitacora.objects.filter(accion="SALIDA", detalle__contains=self.codigo).exists())

    def test_no_se_cierra_dos_veces(self):
        self.client.post(f"/api/tiquetes/{self.codigo}/salida/", {"metodo": "EFECTIVO"}, format="json")
        r = self.client.post(f"/api/tiquetes/{self.codigo}/salida/", {"metodo": "EFECTIVO"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Pago.objects.filter(tiquete__codigo=self.codigo).count(), 1)

    def test_metodo_obligatorio_si_hay_cobro(self):
        r = self.client.post(f"/api/tiquetes/{self.codigo}/salida/", {}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_sin_cobro_dentro_de_la_gracia(self):
        Tarifa.objects.filter(tipo_vehiculo=self.carro, vigente=True).update(minutos_gracia=15)
        self.atrasar(self.codigo, 10)
        r = self.client.post(f"/api/tiquetes/{self.codigo}/salida/", {}, format="json")
        self.assertEqual(r.data["valor"], "0")
        self.assertFalse(Pago.objects.filter(tiquete__codigo=self.codigo).exists())

    def test_tiquete_perdido_suma_multa(self):
        Parqueadero.objects.update(multa_tiquete_perdido=5000)
        r = self.client.post(
            f"/api/tiquetes/{self.codigo}/salida/", {"metodo": "EFECTIVO", "tiquete_perdido": True}, format="json"
        )
        self.assertEqual(r.data["valor"], "17000")
        self.assertEqual(r.data["multa"], "5000")

    def test_cambio_de_tarifa_no_afecta_tiquetes_cerrados(self):
        self.client.post(f"/api/tiquetes/{self.codigo}/salida/", {"metodo": "EFECTIVO"}, format="json")
        self.como_admin()
        vigente = Tarifa.objects.get(tipo_vehiculo=self.carro, vigente=True)
        self.client.patch(f"/api/tarifas/{vigente.pk}/", {"valor": 9000}, format="json")
        self.assertEqual(Tiquete.objects.get(codigo=self.codigo).valor, 12000)

    def test_activos_con_tiempo_y_valor(self):
        r = self.client.get("/api/tiquetes/activos/")
        self.assertEqual(len(r.data), 6)
        fila = next(t for t in r.data if t["codigo"] == self.codigo)
        self.assertEqual(fila["minutos_transcurridos"], 165)
        self.assertEqual(fila["valor_actual"], 12000)
        self.assertEqual(len(self.client.get("/api/tiquetes/activos/?placa=ghi").data), 1)

    def test_tiquete_inexistente(self):
        self.assertEqual(self.client.get("/api/tiquetes/PC-999999/").status_code, 404)
