from django.core.management import call_command
from rest_framework.test import APITestCase


class AvanceUnoTests(APITestCase):
    """Pruebas del avance 1: login por rol y endpoints de lectura."""

    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos_iniciales", verbosity=0)

    def login(self, email, password):
        return self.client.post("/api/auth/login/", {"email": email, "password": password}, format="json")

    def autenticar(self, email="trabajador@parkcontrol.com", password="Trabajador123*"):
        token = self.login(email, password).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_login_admin_devuelve_rol(self):
        r = self.login("admin@parkcontrol.com", "Admin123*")
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertEqual(r.data["usuario"]["rol"], "ADMIN")

    def test_login_trabajador_devuelve_rol(self):
        r = self.login("trabajador@parkcontrol.com", "Trabajador123*")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["usuario"]["rol"], "TRABAJADOR")

    def test_login_con_clave_incorrecta_falla(self):
        r = self.login("admin@parkcontrol.com", "otra")
        self.assertEqual(r.status_code, 401)

    def test_api_sin_token_responde_401(self):
        self.assertEqual(self.client.get("/api/espacios/").status_code, 401)

    def test_me(self):
        self.autenticar()
        r = self.client.get("/api/auth/me/")
        self.assertEqual(r.data["email"], "trabajador@parkcontrol.com")

    def test_espacios_y_ocupante(self):
        self.autenticar()
        r = self.client.get("/api/espacios/")
        self.assertEqual(len(r.data), 15)
        a02 = next(e for e in r.data if e["codigo"] == "A-02")
        self.assertEqual(a02["estado"], "OCUPADO")
        self.assertEqual(a02["ocupante"]["placa"], "ABC123")
        disponibles = self.client.get("/api/espacios/?estado=DISPONIBLE&tipo=Moto").data
        self.assertTrue(all(e["tipo_vehiculo"] == "Moto" and e["ocupante"] is None for e in disponibles))

    def test_buscar_vehiculo_por_placa(self):
        self.autenticar()
        r = self.client.get("/api/vehiculos/?placa=abc")
        self.assertEqual([v["placa"] for v in r.data], ["ABC123"])

    def test_espacios_solo_lectura_en_avance_1(self):
        self.autenticar("admin@parkcontrol.com", "Admin123*")
        r = self.client.post("/api/espacios/", {"codigo": "Z-01"}, format="json")
        self.assertEqual(r.status_code, 405)
