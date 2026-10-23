from .models import Bitacora


def registrar(usuario, accion, detalle=""):
    """Deja en la bitácora quién hizo qué. La pantalla para consultarla llega en el avance 4."""
    Bitacora.objects.create(usuario=usuario, accion=accion, detalle=detalle)


class BitacoraMixin:
    """Para ModelViewSets: registra en la bitácora cada creación, edición y eliminación."""

    nombre_bitacora = ""  # p. ej. "TARIFA" -> acciones CREAR_TARIFA, EDITAR_TARIFA, ELIMINAR_TARIFA

    def perform_create(self, serializer):
        obj = serializer.save()
        registrar(self.request.user, f"CREAR_{self.nombre_bitacora}", str(obj))

    def perform_update(self, serializer):
        obj = serializer.save()
        registrar(self.request.user, f"EDITAR_{self.nombre_bitacora}", str(obj))

    def perform_destroy(self, instance):
        detalle = str(instance)
        instance.delete()
        registrar(self.request.user, f"ELIMINAR_{self.nombre_bitacora}", detalle)
