from datetime import timedelta

from apps.espacios.models import Espacio
from apps.operaciones.models import Pago
from apps.operaciones.tests import OperacionTestBase
from apps.vehiculos.models import Cliente

from .models import Mensualidad, PlanMensual
from .reglas import hoy, marcar_vencidas


class MensualidadesTests(OperacionTestBase):
    """RF-16, RF-17 y RF-18."""

    def setUp(self):
        super().setUp()
        self.plan_carro = PlanMensual.objects.get(nombre="Mensual carro")
        self.plan_moto = PlanMensual.objects.get(nombre="Mensual moto")
        self.como_trabajador()

    def vender(self, **datos):
        base = {"documento": "1085", "nombre": "Ana Ruiz", "placa": "GHI987", "plan": self.plan_carro.pk, "metodo": "EFECTIVO"}
        return self.client.post("/api/mensualidades/", {**base, **datos}, format="json")

    def test_trabajador_no_crea_planes(self):
        r = self.client.post("/api/planes-mensuales/", {"nombre": "X", "tipo_vehiculo": self.carro.pk, "valor": 1, "dias": 30}, format="json")
        self.assertEqual(r.status_code, 403)
        self.como_admin()
        r = self.client.post("/api/planes-mensuales/", {"nombre": "Quincenal", "tipo_vehiculo": self.carro.pk, "valor": 100000, "dias": 15}, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_vender_crea_cliente_pago_y_vigencia(self):
        r = self.vender()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["fecha_inicio"], str(hoy()))
        self.assertEqual(r.data["fecha_fin"], str(hoy() + timedelta(days=29)))  # 30 días contando hoy
        self.assertEqual(r.data["dias_restantes"], 30)
        self.assertEqual(r.data["valor_pagado"], 180000)
        cliente = Cliente.objects.get(documento="1085")
        self.assertEqual(cliente.vehiculos.get().placa, "GHI987")
        self.assertEqual(Pago.objects.get(mensualidad_id=r.data["id"]).valor, 180000)

    def test_vehiculo_nuevo_toma_el_tipo_del_plan(self):
        r = self.vender(placa="MOT12X", plan=self.plan_moto.pk)
        self.assertEqual(r.data["tipo_vehiculo"], "Moto")

    def test_validaciones_de_venta(self):
        self.assertIn("plan", self.vender(plan=self.plan_moto.pk).data)  # GHI987 es carro
        self.assertIn("nombre", self.vender(documento="999", nombre="").data)  # cliente nuevo sin nombre
        self.vender()
        self.assertIn("placa", self.vender().data)  # ya tiene una vigente
        c01 = Espacio.objects.get(codigo="C-01")
        self.assertIn("espacio_fijo", self.vender(placa="JKL321", espacio_fijo=c01.pk).data)

    def test_renovar_empieza_al_vencer(self):
        mensualidad = self.vender().data
        r = self.client.post(f"/api/mensualidades/{mensualidad['id']}/renovar/", {"metodo": "TRANSFERENCIA"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["fecha_inicio"], str(hoy() + timedelta(days=30)))
        r = self.client.post(f"/api/mensualidades/{mensualidad['id']}/renovar/", {"metodo": "EFECTIVO"}, format="json")
        self.assertEqual(r.status_code, 400)  # ya fue renovada

    def test_renovar_una_vencida_empieza_hoy(self):
        m = Mensualidad.objects.get(pk=self.vender().data["id"])
        Mensualidad.objects.filter(pk=m.pk).update(fecha_inicio=hoy() - timedelta(days=40), fecha_fin=hoy() - timedelta(days=11))
        r = self.client.post(f"/api/mensualidades/{m.pk}/renovar/", {"metodo": "EFECTIVO"}, format="json")
        self.assertEqual(r.data["fecha_inicio"], str(hoy()))

    def test_marcar_vencidas(self):
        m = Mensualidad.objects.get(pk=self.vender().data["id"])
        Mensualidad.objects.filter(pk=m.pk).update(fecha_fin=hoy() - timedelta(days=1))
        self.assertEqual(marcar_vencidas(), 1)
        self.assertEqual(self.client.get("/api/mensualidades/?estado=VENCIDA&q=ghi").data[0]["id"], m.pk)

    def test_entrada_y_salida_con_mensualidad_no_cobra(self):
        b03 = Espacio.objects.get(codigo="B-03")
        self.vender(espacio_fijo=b03.pk)
        r = self.entrada(placa="GHI987")
        self.assertTrue(r.data["es_mensualidad"])
        self.assertEqual(r.data["espacio"], "B-03")  # usa su espacio fijo
        self.atrasar(r.data["codigo"], 300)
        r = self.client.post(f"/api/tiquetes/{r.data['codigo']}/salida/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["valor"], "0")
        self.assertFalse(Pago.objects.filter(tiquete__codigo=r.data["codigo"]).exists())

    def test_espacio_fijo_reservado_para_otros(self):
        b01 = Espacio.objects.get(codigo="B-01")
        self.vender(espacio_fijo=b01.pk)
        codigos = [e["codigo"] for e in self.client.get("/api/espacios/disponibles/?tipo=Carro").data]
        self.assertNotIn("B-01", codigos)
        codigos = [e["codigo"] for e in self.client.get("/api/espacios/disponibles/?tipo=Carro&placa=GHI987").data]
        self.assertIn("B-01", codigos)
        self.assertEqual(self.entrada(placa="DEF999", tipo_vehiculo=self.carro.pk, espacio=b01.pk).status_code, 400)

    def test_desactivar_plan_vendido(self):
        self.vender()
        self.como_admin()
        self.client.delete(f"/api/planes-mensuales/{self.plan_carro.pk}/")
        self.assertFalse(PlanMensual.objects.get(pk=self.plan_carro.pk).activo)
        self.como_trabajador()
        self.assertIn("plan", self.vender(placa="JKL321", documento="2").data)
