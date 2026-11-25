import { Injectable, signal } from '@angular/core';

export interface Notificacion {
  id: number;
  tipo: 'exito' | 'error';
  texto: string;
}

/** Cuánto tiempo queda visible cada tipo de mensaje (los errores, más tiempo para leerlos). */
const DURACION = { exito: 4000, error: 9000 };

/**
 * Mensajes flotantes (arriba a la derecha) para el resultado de una acción.
 * Se ven aunque la página esté desplazada hacia abajo y se ocultan solos.
 */
@Injectable({ providedIn: 'root' })
export class NotificacionesService {
  readonly lista = signal<Notificacion[]>([]);
  private siguienteId = 1;

  exito(texto: string): void {
    this.mostrar('exito', texto);
  }

  error(texto: string): void {
    this.mostrar('error', texto);
  }

  cerrar(id: number): void {
    this.lista.update((lista) => lista.filter((n) => n.id !== id));
  }

  private mostrar(tipo: Notificacion['tipo'], texto: string): void {
    const id = this.siguienteId++;
    // Máximo 3 a la vez: si llegan más, se van las más viejas
    this.lista.update((lista) => [...lista.slice(-2), { id, tipo, texto }]);
    setTimeout(() => this.cerrar(id), DURACION[tipo]);
  }
}
