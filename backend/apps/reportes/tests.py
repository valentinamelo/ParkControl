from datetime import timedelta
from io import BytesIO

from openpyxl import load_workbook

from apps.configuracion.models import TipoVehiculo
from apps.espacios.models import Espacio
from apps.mensualidades.models import PlanMensual
from apps.mensualidades.reglas import hoy
from apps.operaciones.models import Pago, Tiquete
from apps.operaciones.tests import OperacionTestBase
from apps.usuarios.models import Usuario

from .models import Bitacora


class FlujoBase(OperacionTestBase):
    """Deja ingresos de hoy: dos salidas del trabajador y una mensualidad vendida por el admin."""

    def setUp(self):
        super().setUp()
        self.como_trabajador()
        for placa, minutos, metodo in [("ABC123", None, "EFECTIVO"), ("XYZ789", None, "TARJETA")]:
            codigo = Tiquete.objects.get(vehiculo__placa=placa, estado="ABIERTO").codigo
            self.client.post(f"/api/tiquetes/{codigo}/salida/", {"metodo": metodo}, format="json")
        # ABC123: 165 min de carro = $12.000; XYZ789: 105 min de moto = $4.000
        self.como_admin()
        self.client.post(
            "/api/mensualidades/",
            {"documento": "1085", "nombre": "Ana", "placa": "GHI987",
             "plan": PlanMensual.objects.get(nombre="Mensual carro").pk, "metodo": "TRANSFERENCIA"},
            format="json",
        )


class DashboardTests(FlujoBase):
    """RF-20."""

    def test_admin_ve_todo_el_parqueadero(self):
        r = self.client.get("/api/dashboard/resumen/").data
        self.assertEqual(r["alcance"], "parqueadero")
        self.assertEqual(r["espacios"]["total"], 15)
        self.assertEqual(r["espacios"]["ocupados"], 3)
        self.assertEqual(r["espacios"]["disponibles"], 12)
        self.assertEqual(r["hoy"]["ingresos"], 12000 + 4000 + 180000)
        self.assertEqual(r["hoy"]["salidas"], 2)
        self.assertEqual(r["mensualidades"]["vigentes"], 1)
        self.assertEqual(len(r["semana"]), 7)
        self.assertEqual(r["semana"][-1]["total"], 196000)
        carro = next(t for t in r["espacios"]["por_tipo"] if t["tipo"] == "Carro")
        self.assertEqual((carro["total"], carro["ocupados"]), (10, 2))

    def test_trabajador_ve_solo_su_turno(self):
        self.como_trabajador()
        r = self.client.get("/api/dashboard/resumen/").data
        self.assertEqual(r["alcance"], "turno")
        self.assertEqual(r["hoy"]["ingresos"], 16000)  # la mensualidad la cobró el admin
        self.assertNotIn("semana", r)

    def test_inactivos_no_cuentan(self):
        Espacio.objects.filter(codigo="A-01").update(estado="INACTIVO")
        r = self.client.get("/api/dashboard/resumen/").data
        self.assertEqual(r["espacios"]["total"], 14)
        self.assertEqual(r["espacios"]["inactivos"], 1)


class ReporteIngresosTests(FlujoBase):
    """RF-21 y RF-22."""

    def reporte(self, **params):
        return self.client.get("/api/reportes/ingresos/", params)

    def test_resumen_del_dia(self):
        r = self.reporte().data
        self.assertEqual(r["total"], 196000)
        self.assertEqual(r["cantidad"], 3)
        metodos = {g["nombre"]: g["total"] for g in r["por_metodo"]}
        self.assertEqual(metodos, {"Transferencia": 180000, "Efectivo": 12000, "Tarjeta": 4000})
        conceptos = {g["nombre"]: g["total"] for g in r["por_concepto"]}
        self.assertEqual(conceptos, {"Mensualidad": 180000, "Parqueo": 16000})
        self.assertEqual(r["detalle"][0]["referencia"], self.codigo_abc)

    def test_filtros(self):
        moto = TipoVehiculo.objects.get(nombre="Moto")
        self.assertEqual(self.reporte(tipo=moto.pk).data["total"], 4000)
        self.assertEqual(self.reporte(metodo="EFECTIVO").data["total"], 12000)
        self.assertEqual(self.reporte(concepto="MENSUALIDAD").data["total"], 180000)
        trabajador = Usuario.objects.get(email="trabajador@parkcontrol.com")
        self.assertEqual(self.reporte(usuario=trabajador.pk).data["total"], 16000)

    def test_rango_de_fechas(self):
        ayer = hoy() - timedelta(days=1)
        Pago.objects.filter(metodo="EFECTIVO").update(fecha=Pago.objects.get(metodo="EFECTIVO").fecha - timedelta(days=1))
        r = self.reporte(desde=ayer.isoformat(), hasta=ayer.isoformat()).data
        self.assertEqual(r["total"], 12000)
        r = self.reporte(desde=ayer.isoformat(), hasta=hoy().isoformat()).data
        self.assertEqual([d["total"] for d in r["por_dia"]], [12000, 184000])

    def test_fechas_invalidas(self):
        self.assertEqual(self.reporte(desde="2026-13-01").status_code, 400)
        self.assertEqual(self.reporte(desde="2026-11-10", hasta="2026-11-01").status_code, 400)
        self.assertEqual(self.reporte(desde="2024-01-01", hasta="2026-01-01").status_code, 400)
        self.assertEqual(self.reporte(metodo="BITCOIN").status_code, 400)

    def test_tiquete_anulado_no_cuenta(self):
        self.client.post(f"/api/tiquetes/{self.codigo_abc}/anular/", {"motivo": "Cobro duplicado"}, format="json")
        self.assertEqual(self.reporte().data["total"], 184000)

    def test_exportar_pdf(self):
        r = self.reporte(formato="pdf")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertIn("attachment", r["Content-Disposition"])
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_exportar_excel(self):
        r = self.reporte(formato="xlsx")
        self.assertEqual(r.status_code, 200)
        libro = load_workbook(BytesIO(r.content))
        self.assertEqual(libro.sheetnames, ["Resumen", "Por día", "Detalle"])
        self.assertEqual(libro["Resumen"]["B5"].value, 196000)
        self.assertEqual(libro["Detalle"].max_row, 3 + 1 + 1)  # encabezado + 3 pagos + fila vacía + total

    def test_formato_invalido(self):
        self.assertEqual(self.reporte(formato="csv").status_code, 400)


class AnulacionTests(OperacionTestBase):
    """RF-24."""

    def test_trabajador_no_anula(self):
        self.como_trabajador()
        r = self.client.post(f"/api/tiquetes/{self.codigo_abc}/anular/", {"motivo": "Error de digitación"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_motivo_obligatorio(self):
        self.como_admin()
        r = self.client.post(f"/api/tiquetes/{self.codigo_abc}/anular/", {"motivo": "  no "}, format="json")
        self.assertIn("motivo", r.data)

    def test_anular_abierto_libera_el_espacio(self):
        self.como_admin()
        r = self.client.post(f"/api/tiquetes/{self.codigo_abc}/anular/", {"motivo": "Entrada registrada por error"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["estado"], "ANULADO")
        self.assertEqual(r.data["motivo_anulacion"], "Entrada registrada por error")
        self.assertEqual(Espacio.objects.get(codigo="A-02").estado, "DISPONIBLE")
        registro = Bitacora.objects.get(accion="ANULAR_TIQUETE")
        self.assertIn("Entrada registrada por error", registro.detalle)
        # La placa puede volver a entrar
        self.assertEqual(self.entrada(placa="ABC123").status_code, 201)

    def test_no_se_anula_dos_veces_ni_se_cobra_un_anulado(self):
        self.como_admin()
        self.client.post(f"/api/tiquetes/{self.codigo_abc}/anular/", {"motivo": "Error de digitación"}, format="json")
        r = self.client.post(f"/api/tiquetes/{self.codigo_abc}/anular/", {"motivo": "Error de digitación"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f"/api/tiquetes/{self.codigo_abc}/salida/", {"metodo": "EFECTIVO"}, format="json")
        self.assertEqual(r.status_code, 400)


class BitacoraTests(FlujoBase):
    """RF-23: quién registró cada entrada, salida, anulación y cambio de configuración."""

    def test_registra_operacion_y_configuracion(self):
        acciones = self.client.get("/api/bitacora/acciones/").data
        self.assertIn("SALIDA", acciones)
        self.assertIn("VENDER_MENSUALIDAD", acciones)
        r = self.client.get("/api/bitacora/", {"accion": "SALIDA"}).data
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["results"][0]["usuario_nombre"], "Trabajador Turno 1")

    def test_filtros(self):
        trabajador = Usuario.objects.get(email="trabajador@parkcontrol.com")
        r = self.client.get("/api/bitacora/", {"usuario": trabajador.pk, "q": "XYZ789"}).data
        self.assertEqual(r["count"], 1)
        r = self.client.get("/api/bitacora/", {"desde": (hoy() + timedelta(days=1)).isoformat()}).data
        self.assertEqual(r["count"], 0)


class PermisosPorRolTests(OperacionTestBase):
    """Matriz de la sección 2 de la planeación: lo que el trabajador no puede hacer, el backend lo rechaza."""

    SOLO_ADMIN = [
        ("get", "/api/usuarios/"),
        ("post", "/api/tarifas/"),
        ("post", "/api/horarios/"),
        ("post", "/api/tipos-vehiculo/"),
        ("post", "/api/zonas/"),
        ("post", "/api/espacios/"),
        ("post", "/api/espacios/lote/"),
        ("put", "/api/parqueadero/"),
        ("post", "/api/planes-mensuales/"),
        ("post", "/api/tiquetes/PC-NOEXISTE/anular/"),
        ("get", "/api/reportes/ingresos/"),
        ("get", "/api/bitacora/"),
        ("get", "/api/bitacora/acciones/"),
    ]
    AMBOS = [
        "/api/auth/me/", "/api/dashboard/resumen/", "/api/espacios/", "/api/espacios/disponibles/?tipo=Carro",
        "/api/vehiculos/", "/api/clientes/", "/api/tarifas/", "/api/horarios/", "/api/parqueadero/",
        "/api/tiquetes/", "/api/tiquetes/activos/", "/api/planes-mensuales/", "/api/mensualidades/",
    ]

    def test_trabajador_rechazado_en_funciones_de_admin(self):
        self.como_trabajador()
        for metodo, url in self.SOLO_ADMIN:
            with self.subTest(url=url, metodo=metodo):
                self.assertEqual(getattr(self.client, metodo)(url, {}, format="json").status_code, 403)

    def test_admin_no_es_rechazado(self):
        self.como_admin()
        for metodo, url in self.SOLO_ADMIN:
            with self.subTest(url=url, metodo=metodo):
                self.assertNotIn(getattr(self.client, metodo)(url, {}, format="json").status_code, (401, 403))

    def test_ambos_roles_consultan(self):
        for autenticar in (self.como_trabajador, self.como_admin):
            autenticar()
            for url in self.AMBOS:
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_salud_es_publica(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/salud/").json(), {"estado": "ok"})

    def test_sin_token_todo_es_401(self):
        for url in self.AMBOS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)
