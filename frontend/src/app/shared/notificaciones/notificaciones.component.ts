import { Component, inject } from '@angular/core';

import { NotificacionesService } from '../../core/notificaciones.service';

@Component({
  selector: 'app-notificaciones',
  template: `
    <div class="pila" aria-live="polite">
      @for (n of servicio.lista(); track n.id) {
        <div class="notificacion" [class.exito]="n.tipo === 'exito'" [class.alerta]="n.tipo === 'error'"
             [attr.role]="n.tipo === 'error' ? 'alert' : 'status'">
          <i aria-hidden="true" class="fa-solid" [class.fa-circle-check]="n.tipo === 'exito'"
             [class.fa-triangle-exclamation]="n.tipo === 'error'"></i>
          <span>{{ n.texto }}</span>
          <button type="button" class="cerrar" aria-label="Cerrar mensaje" (click)="servicio.cerrar(n.id)">
            <i aria-hidden="true" class="fa-solid fa-xmark"></i>
          </button>
        </div>
      }
    </div>
  `,
  styles: `
    .pila {
      position: fixed; top: 20px; right: 20px; z-index: 1000;
      display: flex; flex-direction: column; gap: 10px;
      width: min(420px, calc(100vw - 40px)); pointer-events: none;
    }
    .notificacion {
      display: flex; align-items: flex-start; gap: 10px; margin: 0; pointer-events: auto;
      padding: 14px 14px 14px 16px; border-radius: var(--radio); line-height: 1.4;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15); animation: entrar 0.2s ease-out;
    }
    .notificacion.alerta { border-left: 4px solid var(--error); }
    .notificacion.exito { border-left: 4px solid var(--amarillo); }
    .notificacion > i { margin-top: 2px; }
    .notificacion span { flex: 1; }
    .cerrar { background: none; border: 0; padding: 2px 4px; cursor: pointer; color: inherit; opacity: 0.7; }
    .cerrar:hover { opacity: 1; }
    @keyframes entrar { from { opacity: 0; transform: translateY(-8px); } }
  `,
})
export class NotificacionesComponent {
  protected servicio = inject(NotificacionesService);
}
