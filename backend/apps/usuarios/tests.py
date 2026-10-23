from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.reportes.models import Bitacora

from .models import Usuario


class ApiTestBase(APITestCase):
    """Carga los datos iniciales y ayuda a iniciar sesión con cada rol."""

    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos_iniciales", verbosity=0)

    def login(self, email, password):
        return self.client.post("/api/auth/login/", {"email": email, "password": password}, format="json")

    def autenticar(self, email="trabajador@parkcontrol.com", password="Trabajador123*"):
        token = self.login(email, password).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def como_admin(self):
        self.autenticar("admin@parkcontrol.com", "Admin123*")

    def como_trabajador(self):
        self.autenticar()


class AvanceUnoTests(ApiTestBase):
    """Pruebas del avance 1: login por rol y endpoints de lectura."""

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


class UsuariosTests(ApiTestBase):
    """RF-03: el administrador crea, edita y desactiva trabajadores."""

    def test_trabajador_no_gestiona_usuarios(self):
        self.como_trabajador()
        self.assertEqual(self.client.get("/api/usuarios/").status_code, 403)

    def test_crear_trabajador_y_que_pueda_entrar(self):
        self.como_admin()
        r = self.client.post(
            "/api/usuarios/",
            {"email": "Nuevo@ParkControl.com", "first_name": "Ana", "last_name": "Ruiz",
             "rol": "TRABAJADOR", "password": "Clave.Segura9"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertNotIn("password", r.data)
        self.assertEqual(r.data["email"], "nuevo@parkcontrol.com")
        self.client.credentials()
        self.assertEqual(self.login("nuevo@parkcontrol.com", "Clave.Segura9").status_code, 200)

    def test_contrasena_obligatoria_y_segura(self):
        self.como_admin()
        datos = {"email": "x@parkcontrol.com", "first_name": "X", "rol": "TRABAJADOR"}
        self.assertIn("password", self.client.post("/api/usuarios/", datos, format="json").data)
        r = self.client.post("/api/usuarios/", {**datos, "password": "123"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)

    def test_correo_repetido(self):
        self.como_admin()
        r = self.client.post(
            "/api/usuarios/",
            {"email": "TRABAJADOR@parkcontrol.com", "first_name": "X", "rol": "TRABAJADOR", "password": "Clave.Segura9"},
            format="json",
        )
        self.assertIn("email", r.data)

    def test_desactivar_trabajador_impide_login(self):
        self.como_admin()
        trabajador = Usuario.objects.get(email="trabajador@parkcontrol.com")
        r = self.client.delete(f"/api/usuarios/{trabajador.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["is_active"])
        self.assertTrue(Usuario.objects.filter(pk=trabajador.pk).exists())
        self.client.credentials()
        self.assertEqual(self.login("trabajador@parkcontrol.com", "Trabajador123*").status_code, 401)

    def test_admin_no_se_desactiva_a_si_mismo(self):
        self.como_admin()
        admin = Usuario.objects.get(email="admin@parkcontrol.com")
        self.assertEqual(self.client.delete(f"/api/usuarios/{admin.pk}/").status_code, 400)
        r = self.client.patch(f"/api/usuarios/{admin.pk}/", {"rol": "TRABAJADOR"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_cambio_de_configuracion_queda_en_bitacora(self):
        self.como_admin()
        trabajador = Usuario.objects.get(email="trabajador@parkcontrol.com")
        self.client.patch(f"/api/usuarios/{trabajador.pk}/", {"last_name": "Turno 2"}, format="json")
        self.assertTrue(Bitacora.objects.filter(accion="EDITAR_USUARIO", usuario__email="admin@parkcontrol.com").exists())
