import { Component, computed, input } from '@angular/core';

import { pesos } from '../../core/formato';
import { GrupoIngresos } from '../../core/models';

/** Desglose de ingresos en barras horizontales: nombre, barra proporcional al mayor, total. */
@Component({
  selector: 'app-barras',
  template: `
    @if (grupos().length) {
      <ul class="barras">
        @for (g of grupos(); track g.nombre) {
          <li>
            <div class="fila-barra">
              <span>{{ g.nombre }} <small class="nota">· {{ g.cantidad }} {{ g.cantidad === 1 ? 'pago' : 'pagos' }}</small></span>
              <b>{{ pesos(g.total) }}</b>
            </div>
            <div class="pista"><div class="relleno" [style.width.%]="porcentaje(g.total)"></div></div>
          </li>
        }
      </ul>
    } @else {
      <p class="nota">{{ vacio() }}</p>
    }
  `,
  styles: `
    .barras { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 12px; }
    .fila-barra { display: flex; justify-content: space-between; gap: 12px; font-size: 0.875rem; margin-bottom: 4px; }
    .pista { height: 8px; border-radius: 99px; background: var(--gris); overflow: hidden; }
    .relleno { height: 100%; border-radius: 99px; background: var(--amarillo); min-width: 2px; }
  `,
})
export class BarrasComponent {
  grupos = input.required<GrupoIngresos[]>();
  vacio = input('Sin ingresos.');

  protected pesos = pesos;
  private maximo = computed(() => Math.max(...this.grupos().map((g) => g.total), 1));

  protected porcentaje(total: number): number {
    return (total * 100) / this.maximo();
  }
}
