from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import FileResponse, Http404, JsonResponse
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.configuracion.views import HorarioViewSet, TarifaViewSet, TipoVehiculoViewSet, parqueadero
from apps.espacios.views import EspacioViewSet, ZonaViewSet
from apps.mensualidades.views import MensualidadViewSet, PlanMensualViewSet
from apps.operaciones.views import TiqueteViewSet
from apps.reportes.views import BitacoraView, bitacora_acciones, dashboard_resumen, reporte_ingresos
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

def salud(request):
    """GET /api/salud/ -> para el health check del hosting (sin autenticación)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"estado": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/salud/", salud, name="salud"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", me, name="me"),
    path("api/parqueadero/", parqueadero, name="parqueadero"),
    path("api/dashboard/resumen/", dashboard_resumen, name="dashboard-resumen"),
    path("api/reportes/ingresos/", reporte_ingresos, name="reporte-ingresos"),
    path("api/bitacora/", BitacoraView.as_view(), name="bitacora"),
    path("api/bitacora/acciones/", bitacora_acciones, name="bitacora-acciones"),
    path("api/", include(router.urls)),
]


def aplicacion_angular(request):
    """En producción, cualquier ruta que no sea de la API la resuelve Angular (index.html)."""
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("No está el build de Angular. En desarrollo usa http://localhost:4200.")
    return FileResponse(index.open("rb"), content_type="text/html")


urlpatterns += [re_path(r"^(?!api/|admin/|static/).*$", aplicacion_angular)]
