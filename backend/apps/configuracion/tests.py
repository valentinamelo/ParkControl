from apps.operaciones.models import Tiquete
from apps.usuarios.tests import ApiTestBase

from .models import Horario, Tarifa, TipoVehiculo


class ConfiguracionTests(ApiTestBase):
    """RF-07 y RF-08: tarifas, horarios y datos del parqueadero."""

    def tarifa_carro(self):
        return Tarifa.objects.get(tipo_vehiculo__nombre="Carro", vigente=True)

    def test_trabajador_lee_pero_no_cambia(self):
        self.como_trabajador()
        self.assertEqual(self.client.get("/api/tarifas/").status_code, 200)
        r = self.client.patch(f"/api/tarifas/{self.tarifa_carro().pk}/", {"valor": 1}, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.put("/api/parqueadero/", {"nombre": "X"}, format="json").status_code, 403)

    def test_cambiar_tarifa_crea_una_nueva_vigente(self):
        self.como_admin()
        anterior = self.tarifa_carro()
        r = self.client.patch(f"/api/tarifas/{anterior.pk}/", {"valor": 5000}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertNotEqual(r.data["id"], anterior.pk)
        anterior.refresh_from_db()
        self.assertFalse(anterior.vigente)
        self.assertEqual(anterior.valor, 4000)  # el historial no cambia
        self.assertEqual(Tarifa.objects.filter(tipo_vehiculo__nombre="Carro", vigente=True).count(), 1)
        self.assertEqual(self.tarifa_carro().valor, 5000)
        self.assertEqual(self.tarifa_carro().tope_diario, 30000)  # se conservan los demás campos
        self.assertEqual(len(self.client.get("/api/tarifas/?historial=1").data), 3)

    def test_crear_tarifa_reemplaza_la_vigente_del_tipo(self):
        self.como_admin()
        moto = TipoVehiculo.objects.get(nombre="Moto")
        r = self.client.post(
            "/api/tarifas/",
            {"tipo_vehiculo": moto.pk, "modalidad": "FRACCION", "valor": 500, "minutos_fraccion": 15,
             "minutos_gracia": 5, "tope_diario": 12000},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        vigentes = Tarifa.objects.filter(tipo_vehiculo=moto, vigente=True)
        self.assertEqual([t.minutos_fraccion for t in vigentes], [15])

    def test_validaciones_de_tarifa(self):
        self.como_admin()
        pk = self.tarifa_carro().pk
        self.assertIn("valor", self.client.patch(f"/api/tarifas/{pk}/", {"valor": 0}, format="json").data)
        self.assertIn("tope_diario", self.client.patch(f"/api/tarifas/{pk}/", {"tope_diario": 100}, format="json").data)
        r = self.client.patch(f"/api/tarifas/{pk}/", {"modalidad": "FRACCION", "minutos_fraccion": 0}, format="json")
        self.assertIn("minutos_fraccion", r.data)

    def test_tarifa_por_hora_siempre_es_de_60_minutos(self):
        self.como_admin()
        r = self.client.patch(f"/api/tarifas/{self.tarifa_carro().pk}/", {"minutos_fraccion": 15}, format="json")
        self.assertEqual(r.data["minutos_fraccion"], 60)

    def test_horario(self):
        self.como_admin()
        domingo = Horario.objects.get(dia_semana=6)
        r = self.client.patch(f"/api/horarios/{domingo.pk}/", {"hora_apertura": "19:00"}, format="json")
        self.assertIn("hora_cierre", r.data)
        r = self.client.patch(f"/api/horarios/{domingo.pk}/", {"abierto": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Horario.objects.get(dia_semana=6).abierto)

    def test_editar_parqueadero(self):
        self.como_admin()
        r = self.client.patch("/api/parqueadero/", {"nit": "900123456-7"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/api/parqueadero/").data["nit"], "900123456-7")

    def test_no_se_elimina_un_tipo_en_uso(self):
        self.como_admin()
        carro = TipoVehiculo.objects.get(nombre="Carro")
        r = self.client.delete(f"/api/tipos-vehiculo/{carro.pk}/")
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Tiquete.objects.exists())
