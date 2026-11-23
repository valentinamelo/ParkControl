import { Component, computed, input } from '@angular/core';

import { pesos } from '../../core/formato';
import { IngresoDia } from '../../core/models';

const DIAS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];

/** Ingresos por día en columnas. Con muchos días solo se rotulan algunos para que se lean. */
@Component({
  selector: 'app-columnas',
  template: `
    <div class="grafico" role="img" [attr.aria-label]="descripcion()">
      @for (d of dias(); track d.fecha; let i = $index) {
        <div class="columna" [title]="etiquetaLarga(d.fecha) + ': ' + pesos(d.total)">
          <span class="valor">{{ mostrarValor() && d.total ? corto(d.total) : '' }}</span>
          <div class="barra" [class.vacia]="!d.total" [style.height.%]="altura(d.total)"></div>
          <span class="eje">{{ i % paso() === 0 ? etiqueta(d.fecha) : '' }}</span>
        </div>
      }
    </div>
  `,
  styles: `
    .grafico { display: flex; align-items: stretch; gap: 4px; height: 180px; }
    .columna { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; min-width: 0; }
    .barra { width: 100%; max-width: 44px; background: var(--negro); border-radius: 4px 4px 0 0; box-shadow: inset 0 3px 0 var(--amarillo); }
    .barra.vacia { height: 2px !important; background: var(--linea); box-shadow: none; }
    .valor { font-size: 0.7rem; font-weight: 600; margin-bottom: 4px; white-space: nowrap; }
    .eje { font-size: 0.7rem; color: var(--texto-suave); margin-top: 6px; height: 1em; white-space: nowrap; }
  `,
})
export class ColumnasComponent {
  dias = input.required<IngresoDia[]>();

  protected pesos = pesos;
  private maximo = computed(() => Math.max(...this.dias().map((d) => d.total), 1));
  /** Hasta 14 días se rotulan todos; si hay más, uno de cada N. */
  protected paso = computed(() => Math.max(1, Math.ceil(this.dias().length / 14)));
  protected mostrarValor = computed(() => this.dias().length <= 10);
  protected descripcion = computed(
    () => 'Ingresos por día: ' + this.dias().map((d) => `${this.etiquetaLarga(d.fecha)} ${pesos(d.total)}`).join(', '),
  );

  protected altura(total: number): number {
    // Las barras ocupan como máximo el 80 % del alto para dejar espacio al valor
    return (total * 80) / this.maximo();
  }

  private fecha(iso: string): Date {
    return new Date(`${iso}T00:00:00`);
  }

  protected etiqueta(iso: string): string {
    const f = this.fecha(iso);
    return this.dias().length <= 7 ? DIAS[f.getDay()] : `${f.getDate()}/${f.getMonth() + 1}`;
  }

  protected etiquetaLarga(iso: string): string {
    const f = this.fecha(iso);
    return `${DIAS[f.getDay()]} ${f.getDate()}/${f.getMonth() + 1}`;
  }

  /** 196000 -> "$196k" */
  protected corto(total: number): string {
    if (total >= 1_000_000) return `$${(total / 1_000_000).toFixed(1)}M`;
    return total >= 1000 ? `$${Math.round(total / 1000)}k` : `$${total}`;
  }
}
