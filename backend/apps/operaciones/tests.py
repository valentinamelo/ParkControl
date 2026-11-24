from datetime import datetime, time, timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from apps.configuracion.models import Horario, Parqueadero, Tarifa, TipoVehiculo
from apps.espacios.models import Espacio
from apps.reportes.models import Bitacora
from apps.usuarios.tests import ApiTestBase

from .codigos import ALFABETO, LONGITUD, normalizar_codigo, prefijo
from .models import Pago, Tiquete
from .reglas import calcular_cobro, calcular_valor, minutos_entre

CODIGO_ALEATORIO = rf"^[CM]-[{ALFABETO}]{{{LONGITUD}}}$"


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
        # Tiquete abierto de ABC123 en los datos iniciales (el código es aleatorio)
        self.codigo_abc = Tiquete.objects.get(vehiculo__placa="ABC123").codigo

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
        self.assertRegex(r.data["codigo"], CODIGO_ALEATORIO)
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
        self.assertIn(self.codigo_abc, r.data["detail"])

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
        self.assertEqual(r["tiquete_abierto"]["codigo"], self.codigo_abc)
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


class CodigoTiqueteTests(OperacionTestBase):
    """Los códigos no son consecutivos, para que no se puedan adivinar ni falsificar."""

    def setUp(self):
        super().setUp()
        self.como_trabajador()

    def test_datos_iniciales_con_codigos_aleatorios(self):
        for codigo, tipo in Tiquete.objects.values_list("codigo", "vehiculo__tipo_vehiculo__nombre"):
            self.assertRegex(codigo, CODIGO_ALEATORIO)
            self.assertEqual(codigo[0], tipo[0])

    def test_prefijo_segun_el_tipo_de_vehiculo(self):
        carro = self.entrada(placa="CAR123", tipo_vehiculo=self.carro.pk).data["codigo"]
        moto = self.entrada(placa="MOT12A", tipo_vehiculo=self.moto.pk).data["codigo"]
        self.assertTrue(carro.startswith("C-"), carro)
        self.assertTrue(moto.startswith("M-"), moto)
        self.assertEqual(prefijo(TipoVehiculo(nombre="Ómnibus")), "O")  # sin tilde

    def test_codigos_no_consecutivos_ni_repetidos(self):
        codigos = [self.entrada(placa=f"ALE{i}23", tipo_vehiculo=self.moto.pk).data["codigo"] for i in range(2)]
        self.assertEqual(len(set(codigos)), 2)
        for codigo in codigos:
            self.assertRegex(codigo, CODIGO_ALEATORIO)
            self.assertFalse(any(c in codigo[3:] for c in "01OI"))  # sin caracteres que se confunden

    def test_busqueda_tolera_minusculas_y_simbolos(self):
        cuerpo = self.codigo_abc[2:]
        for escrito in (self.codigo_abc.lower(), f"C{cuerpo}", f"C'{cuerpo}", f" c-{cuerpo.lower()} "):
            with self.subTest(escrito=escrito):
                self.assertEqual(normalizar_codigo(escrito), self.codigo_abc)
                self.assertEqual(self.client.get(f"/api/tiquetes/{escrito.strip()}/").data["placa"], "ABC123")

    def test_codigos_antiguos_siguen_funcionando(self):
        for antiguo in ("PC-000001", "PC-7K4M2QXR"):
            with self.subTest(antiguo=antiguo):
                Tiquete.objects.filter(vehiculo__placa="ABC123").update(codigo=antiguo)
                self.assertEqual(normalizar_codigo(antiguo.lower().replace("-", "")), antiguo)
                self.assertEqual(self.client.get(f"/api/tiquetes/{antiguo}/").data["placa"], "ABC123")


class PernoctacionTests(SimpleTestCase):
    """
    Con pernoctación, las horas se cobran solo dentro del horario de atención y cada noche
    con el parqueadero cerrado se cobra aparte. Horario: lunes a sábado 06:00-22:00.
    """

    def setUp(self):
        self.horarios = {dia: Horario(dia_semana=dia, hora_apertura=time(6), hora_cierre=time(22)) for dia in range(6)}
        self.horarios[6] = Horario(dia_semana=6, abierto=False, hora_apertura=time(8), hora_cierre=time(18))
        self.tarifa = tarifa(valor=4000, tope=30000)
        self.tarifa.valor_pernoctacion = 15000

    def momento(self, dia, hora, minuto=0):
        """dia: fecha de noviembre de 2026 (el 23 es lunes)."""
        return timezone.make_aware(datetime(2026, 11, dia, hora, minuto))

    def cobro(self, entrada, salida, con_pernoctacion=True):
        if not con_pernoctacion:
            self.tarifa.valor_pernoctacion = None
        return calcular_cobro(self.tarifa, entrada, salida, self.horarios)

    def test_dentro_del_horario_no_hay_noche(self):
        c = self.cobro(self.momento(23, 10), self.momento(23, 12, 45))
        self.assertEqual((c["minutos_cobrados"], c["noches"], c["valor"]), (165, 0, 12000))

    def test_una_noche_se_cobra_aparte_de_las_horas(self):
        # Lunes 20:00 a martes 08:00: 2 h el lunes + 2 h el martes, y 1 noche
        c = self.cobro(self.momento(23, 20), self.momento(24, 8))
        self.assertEqual(c["minutos"], 12 * 60)
        self.assertEqual(c["minutos_cobrados"], 240)
        self.assertEqual(c["noches"], 1)
        self.assertEqual((c["valor_tiempo"], c["valor_noches"], c["valor"]), (16000, 15000, 31000))

    def test_llega_poco_antes_del_cierre_y_sale_al_abrir(self):
        c = self.cobro(self.momento(23, 21, 50), self.momento(24, 6, 5))
        self.assertEqual((c["minutos_cobrados"], c["noches"], c["valor"]), (15, 1, 4000 + 15000))

    def test_dia_cerrado_cuenta_como_otra_noche(self):
        # Sábado 21:00 a lunes 07:00 con el domingo cerrado: 1 h + 1 h y 2 noches
        c = self.cobro(self.momento(28, 21), self.momento(30, 7))
        self.assertEqual((c["minutos_cobrados"], c["noches"]), (120, 2))
        self.assertEqual(c["valor"], 8000 + 2 * 15000)

    def test_el_tope_diario_aplica_a_las_horas(self):
        # Domingo abierto 08:00-18:00: sábado 21:00 a lunes 07:00 = 12 h en horario, topadas en $30.000
        self.horarios[6] = Horario(dia_semana=6, hora_apertura=time(8), hora_cierre=time(18))
        c = self.cobro(self.momento(28, 21), self.momento(30, 7))
        self.assertEqual((c["minutos_cobrados"], c["noches"]), (12 * 60, 2))
        self.assertEqual((c["valor_tiempo"], c["valor"]), (30000, 30000 + 2 * 15000))

    def test_sin_pernoctacion_se_cobra_el_tiempo_corrido(self):
        c = self.cobro(self.momento(23, 20), self.momento(24, 8), con_pernoctacion=False)
        self.assertEqual((c["minutos_cobrados"], c["noches"], c["valor"]), (12 * 60, 0, 30000))


class PernoctacionApiTests(OperacionTestBase):
    """La salida guarda las noches cobradas y el administrador configura el valor por noche."""

    def test_salida_despues_de_una_noche(self):
        self.como_trabajador()
        codigo = self.entrada(placa="NOC123", tipo_vehiculo=self.carro.pk).data["codigo"]
        # Después de la entrada, para que la prueba no dependa de la hora a la que se corre
        Horario.objects.update(abierto=True, hora_apertura=time(6), hora_cierre=time(22))
        self.atrasar(codigo, 26 * 60)  # más de un día: pasa al menos una medianoche con el parqueadero cerrado
        cobro = self.client.get(f"/api/tiquetes/{codigo}/").data["cobro"]
        self.assertGreaterEqual(cobro["noches"], 1)
        self.assertEqual(cobro["valor_noches"], cobro["noches"] * 15000)  # tarifa de carro de los datos iniciales
        self.assertEqual(cobro["valor"], cobro["valor_tiempo"] + cobro["valor_noches"])
        r = self.client.post(f"/api/tiquetes/{codigo}/salida/", {"metodo": "EFECTIVO"}, format="json")
        self.assertEqual(r.data["noches"], cobro["noches"])
        self.assertEqual(int(r.data["valor"]), cobro["valor"])

    def test_admin_configura_y_quita_la_pernoctacion(self):
        self.como_admin()
        vigente = Tarifa.objects.get(tipo_vehiculo=self.carro, vigente=True)
        r = self.client.patch(f"/api/tarifas/{vigente.pk}/", {"valor_pernoctacion": 0}, format="json")
        self.assertIn("valor_pernoctacion", r.data)
        r = self.client.patch(f"/api/tarifas/{vigente.pk}/", {"valor_pernoctacion": 20000}, format="json")
        self.assertEqual(r.data["valor_pernoctacion"], "20000")
        self.assertEqual(r.data["valor"], "4000")  # lo demás de la tarifa se conserva
        nueva = r.data["id"]
        r = self.client.patch(f"/api/tarifas/{nueva}/", {"valor_pernoctacion": None}, format="json")
        self.assertIsNone(r.data["valor_pernoctacion"])
