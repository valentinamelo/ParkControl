from apps.configuracion.models import TipoVehiculo
from apps.mensualidades.models import PlanMensual
from apps.operaciones.models import Tiquete
from apps.reportes.models import Bitacora
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

    def test_zona_ocupada_no_se_desactiva_ni_elimina(self):
        self.como_admin()
        zona_a = Zona.objects.get(nombre="A")  # A-02 está ocupado en los datos iniciales
        r = self.client.post(f"/api/zonas/{zona_a.pk}/desactivar/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("A-02", r.data["detail"])
        self.assertEqual(self.client.delete(f"/api/zonas/{zona_a.pk}/").status_code, 400)
        self.assertFalse(zona_a.espacios.filter(estado="INACTIVO").exists())  # no cambió nada
        self.assertTrue(Zona.objects.filter(pk=zona_a.pk).exists())

    def zona_nueva(self, nombre="D", cantidad=3):
        carro = TipoVehiculo.objects.get(nombre="Carro")
        self.client.post("/api/espacios/lote/", {"zona": nombre, "tipo_vehiculo": carro.pk, "cantidad": cantidad},
                         format="json")
        return Zona.objects.get(nombre=nombre)

    def test_desactivar_y_activar_zona_libre(self):
        self.como_admin()
        zona = self.zona_nueva()
        r = self.client.post(f"/api/zonas/{zona.pk}/desactivar/")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual((r.data["total_espacios"], r.data["espacios_inactivos"]), (3, 3))
        self.assertEqual(zona.espacios.filter(estado="DISPONIBLE").count(), 0)
        disponibles = self.client.get("/api/espacios/disponibles/?tipo=Carro").data
        self.assertFalse(any(e["zona_nombre"] == "D" for e in disponibles))  # no se ofrecen para entradas

        r = self.client.post(f"/api/zonas/{zona.pk}/activar/")
        self.assertEqual(r.data["espacios_inactivos"], 0)
        self.assertEqual(zona.espacios.filter(estado="DISPONIBLE").count(), 3)
        self.assertTrue(Bitacora.objects.filter(accion="DESACTIVAR_ZONA").exists())
        self.assertTrue(Bitacora.objects.filter(accion="ACTIVAR_ZONA").exists())

    def test_eliminar_zona_libre_borra_sus_espacios(self):
        self.como_admin()
        zona = self.zona_nueva()
        self.assertEqual(self.client.delete(f"/api/zonas/{zona.pk}/").status_code, 204)
        self.assertFalse(Zona.objects.filter(nombre="D").exists())
        self.assertFalse(Espacio.objects.filter(codigo__startswith="D-").exists())
        self.assertTrue(Bitacora.objects.filter(accion="ELIMINAR_ZONA", detalle__contains="3 espacios").exists())

    def tiquete_cerrado_en(self, espacio, codigo="C-HISTORIA"):
        """Un tiquete ya cerrado que usó el espacio (copia del tiquete abierto de los datos iniciales)."""
        cerrado = Tiquete.objects.first()
        cerrado.pk, cerrado.codigo, cerrado.espacio_codigo = None, codigo, ""
        cerrado.estado, cerrado.espacio = Tiquete.Estado.CERRADO, espacio
        cerrado.save()
        return cerrado

    def test_zona_con_movimientos_se_elimina_y_el_historial_se_conserva(self):
        self.como_admin()
        zona = self.zona_nueva()
        self.tiquete_cerrado_en(zona.espacios.get(codigo="D-01"))
        r = self.client.delete(f"/api/zonas/{zona.pk}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Zona.objects.filter(nombre="D").exists())

        tiquete = Tiquete.objects.get(codigo="C-HISTORIA")  # el movimiento sigue registrado
        self.assertIsNone(tiquete.espacio)
        self.assertEqual(tiquete.espacio_codigo, "D-01")
        self.assertEqual(self.client.get("/api/tiquetes/C-HISTORIA/").data["espacio"], "D-01")
        self.assertTrue(Bitacora.objects.filter(accion="ELIMINAR_ZONA", detalle__contains="1 movimientos").exists())

    def test_espacio_con_movimientos_se_elimina_y_el_historial_se_conserva(self):
        self.como_admin()
        a05 = Espacio.objects.get(codigo="A-05")
        self.tiquete_cerrado_en(a05)
        self.assertEqual(self.client.delete(f"/api/espacios/{a05.pk}/").status_code, 204)
        self.assertEqual(Tiquete.objects.get(codigo="C-HISTORIA").espacio_codigo, "A-05")

    def test_el_codigo_del_espacio_se_guarda_al_crear_el_tiquete(self):
        tiquete = Tiquete.objects.select_related("espacio").first()
        self.assertEqual(tiquete.espacio_codigo, tiquete.espacio.codigo)

    def test_zona_con_espacio_fijo_de_mensualidad_vigente(self):
        self.como_admin()
        zona = self.zona_nueva()
        d01 = zona.espacios.get(codigo="D-01")
        r = self.client.post("/api/mensualidades/", {
            "documento": "1085", "nombre": "Ana Ruiz", "placa": "GHI987", "metodo": "EFECTIVO",
            "plan": PlanMensual.objects.get(nombre="Mensual carro").pk, "espacio_fijo": d01.pk,
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        r = self.client.post(f"/api/zonas/{zona.pk}/desactivar/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("mensualidad vigente", r.data["detail"])
        self.assertEqual(self.client.delete(f"/api/zonas/{zona.pk}/").status_code, 400)

    def test_trabajador_no_desactiva_ni_elimina_zonas(self):
        self.como_trabajador()
        zona = Zona.objects.get(nombre="B")
        self.assertEqual(self.client.post(f"/api/zonas/{zona.pk}/desactivar/").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/zonas/{zona.pk}/").status_code, 403)

    def test_lista_de_zonas_con_conteos(self):
        self.como_admin()
        zona_a = next(z for z in self.client.get("/api/zonas/").data if z["nombre"] == "A")
        self.assertEqual(zona_a["total_espacios"], Espacio.objects.filter(zona__nombre="A").count())
        ocupados = Espacio.objects.filter(zona__nombre="A", estado="OCUPADO").count()
        self.assertEqual(zona_a["espacios_ocupados"], ocupados)
