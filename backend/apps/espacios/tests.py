from apps.configuracion.models import TipoVehiculo
from apps.usuarios.tests import ApiTestBase

from .models import Espacio, Zona


class EspaciosTests(ApiTestBase):
    """RF-04 a RF-06: crear espacios uno a uno o en lote, editar y desactivar."""

    def test_trabajador_no_crea_espacios(self):
        self.como_trabajador()
        r = self.client.post("/api/espacios/lote/", {"zona": "A", "cantidad": 2}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_lote_en_zona_existente_continua_la_numeracion(self):
        self.como_admin()
        r = self.client.post("/api/espacios/lote/", {"zona": "a", "cantidad": 3}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual([e["codigo"] for e in r.data], ["A-06", "A-07", "A-08"])

    def test_lote_en_zona_nueva(self):
        self.como_admin()
        moto = TipoVehiculo.objects.get(nombre="Moto")
        r = self.client.post("/api/espacios/lote/", {"zona": "M", "cantidad": 10}, format="json")
        self.assertIn("tipo_vehiculo", r.data)
        r = self.client.post("/api/espacios/lote/", {"zona": "M", "tipo_vehiculo": moto.pk, "cantidad": 10}, format="json")
        self.assertEqual(len(r.data), 10)
        self.assertEqual(r.data[-1]["codigo"], "M-10")
        self.assertEqual(Zona.objects.get(nombre="M").tipo_vehiculo, moto)

    def test_lote_con_tipo_distinto_al_de_la_zona(self):
        self.como_admin()
        moto = TipoVehiculo.objects.get(nombre="Moto")
        r = self.client.post("/api/espacios/lote/", {"zona": "A", "tipo_vehiculo": moto.pk, "cantidad": 1}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_crear_uno_sin_codigo_toma_el_siguiente(self):
        self.como_admin()
        zona_c = Zona.objects.get(nombre="C")
        r = self.client.post("/api/espacios/", {"zona": zona_c.pk}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["codigo"], "C-06")
        r = self.client.post("/api/espacios/", {"zona": zona_c.pk, "codigo": "c-06"}, format="json")
        self.assertIn("codigo", r.data)

    def test_desactivar_y_activar_libre(self):
        self.como_admin()
        a01 = Espacio.objects.get(codigo="A-01")
        r = self.client.patch(f"/api/espacios/{a01.pk}/", {"estado": "INACTIVO"}, format="json")
        self.assertEqual(r.data["estado"], "INACTIVO")
        r = self.client.patch(f"/api/espacios/{a01.pk}/", {"estado": "DISPONIBLE"}, format="json")
        self.assertEqual(r.data["estado"], "DISPONIBLE")

    def test_no_se_desactiva_ni_elimina_un_ocupado(self):
        self.como_admin()
        a02 = Espacio.objects.get(codigo="A-02")
        r = self.client.patch(f"/api/espacios/{a02.pk}/", {"estado": "INACTIVO"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.delete(f"/api/espacios/{a02.pk}/").status_code, 400)
        self.assertEqual(Espacio.objects.get(pk=a02.pk).estado, "OCUPADO")

    def test_no_se_ocupa_a_mano(self):
        self.como_admin()
        a01 = Espacio.objects.get(codigo="A-01")
        r = self.client.patch(f"/api/espacios/{a01.pk}/", {"estado": "OCUPADO"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_eliminar_espacio_libre_sin_historial(self):
        self.como_admin()
        a05 = Espacio.objects.get(codigo="A-05")
        self.assertEqual(self.client.delete(f"/api/espacios/{a05.pk}/").status_code, 204)

    def test_cambiar_tipo_de_zona(self):
        self.como_admin()
        moto = TipoVehiculo.objects.get(nombre="Moto")
        zona_a = Zona.objects.get(nombre="A")  # tiene espacios ocupados
        r = self.client.patch(f"/api/zonas/{zona_a.pk}/", {"tipo_vehiculo": moto.pk}, format="json")
        self.assertEqual(r.status_code, 400)
        self.client.post("/api/espacios/lote/", {"zona": "D", "tipo_vehiculo": moto.pk, "cantidad": 2}, format="json")
        carro = TipoVehiculo.objects.get(nombre="Carro")
        zona_d = Zona.objects.get(nombre="D")
        r = self.client.patch(f"/api/zonas/{zona_d.pk}/", {"tipo_vehiculo": carro.pk}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/api/espacios/?tipo=Carro").data[-1]["codigo"], "D-02")

    def test_no_se_elimina_zona_con_espacios(self):
        self.como_admin()
        zona_b = Zona.objects.get(nombre="B")
        self.assertEqual(self.client.delete(f"/api/zonas/{zona_b.pk}/").status_code, 400)
