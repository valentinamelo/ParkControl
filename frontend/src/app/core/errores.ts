import { HttpErrorResponse } from '@angular/common/http';

/**
 * Errores por campo que devuelve DRF: {"placa": ["Ya existe..."]} -> {placa: "Ya existe..."}.
 * Sirve para mostrar cada mensaje debajo de su campo en el formulario.
 */
export function erroresDeCampo(e: HttpErrorResponse): Record<string, string> {
  const errores: Record<string, string> = {};
  if (e.status === 400 && e.error && typeof e.error === 'object' && !Array.isArray(e.error)) {
    for (const [campo, mensajes] of Object.entries(e.error)) {
      if (campo !== 'detail' && campo !== 'non_field_errors') {
        errores[campo] = Array.isArray(mensajes) ? mensajes.join(' ') : String(mensajes);
      }
    }
  }
  return errores;
}

/**
 * Mensaje general para mostrar en una alerta.
 * En un formulario (incluirCampos = false) los errores por campo se muestran aparte.
 */
export function mensajeError(e: HttpErrorResponse, incluirCampos = true): string {
  if (e.status === 0) return 'No hay conexión con el servidor. ¿Está corriendo Django en el puerto 8000?';
  if (e.error?.detail) return e.error.detail;
  if (e.error?.non_field_errors) return e.error.non_field_errors.join(' ');
  if (Array.isArray(e.error)) return e.error.join(' ');
  if (e.status === 403) return 'No tienes permiso para esta acción.';
  if (e.status === 400) {
    const campos = Object.values(erroresDeCampo(e));
    return incluirCampos && campos.length ? campos.join(' ') : 'Revisa los campos marcados.';
  }
  return 'Ocurrió un error inesperado. Intenta de nuevo.';
}
