from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.configuracion.views import HorarioViewSet, TarifaViewSet, TipoVehiculoViewSet, parqueadero
from apps.espacios.views import EspacioViewSet, ZonaViewSet
from apps.mensualidades.views import MensualidadViewSet, PlanMensualViewSet
from apps.operaciones.views import TiqueteViewSet
from apps.usuarios.views import LoginView, UsuarioViewSet, me
from apps.vehiculos.views import ClienteViewSet, VehiculoViewSet

router = DefaultRouter()
router.register("tipos-vehiculo", TipoVehiculoViewSet, basename="tipo-vehiculo")
router.register("tarifas", TarifaViewSet, basename="tarifa")
router.register("horarios", HorarioViewSet, basename="horario")
router.register("zonas", ZonaViewSet, basename="zona")
router.register("espacios", EspacioViewSet, basename="espacio")
router.register("vehiculos", VehiculoViewSet, basename="vehiculo")
router.register("usuarios", UsuarioViewSet, basename="usuario")
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("tiquetes", TiqueteViewSet, basename="tiquete")
router.register("planes-mensuales", PlanMensualViewSet, basename="plan-mensual")
router.register("mensualidades", MensualidadViewSet, basename="mensualidad")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", me, name="me"),
    path("api/parqueadero/", parqueadero, name="parqueadero"),
    path("api/", include(router.urls)),
]
