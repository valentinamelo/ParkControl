import { Component, input } from '@angular/core';

/** Tarjeta de indicador del dashboard: icono + valor + etiqueta. */
@Component({
  selector: 'app-stat-card',
  template: `
    <div class="card stat">
      <div class="icono"><i class="fa-solid" [class]="icono()"></i></div>
      <div>
        <b>{{ valor() }}</b>
        <span>{{ etiqueta() }}</span>
      </div>
    </div>
  `,
  styles: `
    .stat { display: flex; align-items: center; gap: 14px; padding: 16px 18px; }
    .stat b { display: block; font-size: 1.3rem; line-height: 1.2; }
    .stat span { color: var(--texto-suave); font-size: 0.85rem; }
    .icono { width: 38px; height: 38px; border-radius: 8px; background: var(--negro); color: var(--amarillo); display: grid; place-items: center; }
  `,
})
export class StatCardComponent {
  icono = input.required<string>();
  valor = input.required<string | number>();
  etiqueta = input.required<string>();
}
