from apps.configuracion.models import TipoVehiculo
from apps.usuarios.tests import ApiTestBase

from .models import Vehiculo


class VehiculosTests(ApiTestBase):
    """RF-09: registrar, buscar, editar y eliminar vehículos (ambos roles)."""

    def setUp(self):
        self.como_trabajador()
        self.carro = TipoVehiculo.objects.get(nombre="Carro")

    def test_registrar_normaliza_la_placa(self):
        r = self.client.post("/api/vehiculos/", {"placa": "qwe-12 3", "tipo_vehiculo": self.carro.pk}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["placa"], "QWE123")

    def test_placa_repetida_o_invalida(self):
        for placa in ("ABC123", "abc 123"):
            r = self.client.post("/api/vehiculos/", {"placa": placa, "tipo_vehiculo": self.carro.pk}, format="json")
            self.assertEqual(r.data["placa"], ["Ya existe un vehículo con la placa ABC123."])
        r = self.client.post("/api/vehiculos/", {"placa": "A#1", "tipo_vehiculo": self.carro.pk}, format="json")
        self.assertIn("placa", r.data)

    def test_editar(self):
        ghi = Vehiculo.objects.get(placa="GHI987")
        r = self.client.patch(f"/api/vehiculos/{ghi.pk}/", {"color": "Negro"}, format="json")
        self.assertEqual(r.data["color"], "Negro")

    def test_no_cambia_tipo_si_esta_dentro(self):
        abc = Vehiculo.objects.get(placa="ABC123")
        moto = TipoVehiculo.objects.get(nombre="Moto")
        r = self.client.patch(f"/api/vehiculos/{abc.pk}/", {"tipo_vehiculo": moto.pk}, format="json")
        self.assertIn("tipo_vehiculo", r.data)

    def test_eliminar(self):
        ghi = Vehiculo.objects.get(placa="GHI987")  # sin tiquetes
        self.assertEqual(self.client.delete(f"/api/vehiculos/{ghi.pk}/").status_code, 204)
        abc = Vehiculo.objects.get(placa="ABC123")  # con tiquete
        self.assertEqual(self.client.delete(f"/api/vehiculos/{abc.pk}/").status_code, 400)
