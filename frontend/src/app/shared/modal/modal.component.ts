import { Component, input, output } from '@angular/core';

/** Ventana modal: el contenido va entre las etiquetas. Se cierra con la X, con Esc o tocando el fondo. */
@Component({
  selector: 'app-modal',
  host: { '(document:keydown.escape)': 'cerrar.emit()' },
  template: `
    <div class="fondo" (click)="cerrar.emit()">
      <section class="card modal" role="dialog" aria-modal="true" [attr.aria-label]="titulo()" (click)="$event.stopPropagation()">
        <header>
          <h2>{{ titulo() }}</h2>
          <button class="cerrar" type="button" aria-label="Cerrar" (click)="cerrar.emit()">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </header>
        <ng-content />
      </section>
    </div>
  `,
  styles: `
    .fondo { position: fixed; inset: 0; z-index: 10; background: rgba(17, 17, 17, 0.55); display: grid; place-items: center; padding: 16px; }
    .modal { width: 100%; max-width: 480px; max-height: calc(100vh - 32px); overflow-y: auto; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    header h2 { margin: 0; }
    .cerrar { border: 0; background: none; font-size: 1.1rem; cursor: pointer; color: var(--texto-suave); padding: 4px 8px; }
    .cerrar:hover { color: var(--negro); }
  `,
})
export class ModalComponent {
  titulo = input.required<string>();
  cerrar = output<void>();
}
