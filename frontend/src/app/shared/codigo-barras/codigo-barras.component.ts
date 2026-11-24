import { Component, ElementRef, effect, input, viewChild } from '@angular/core';
import JsBarcode from 'jsbarcode';

/** Código de barras Code128 en SVG (se imprime nítido). Lo lee cualquier lector USB. */
@Component({
  selector: 'app-codigo-barras',
  template: `<svg #svg role="img" [attr.aria-label]="'Código de barras ' + valor()"></svg>`,
  // crispEdges: sin bordes difuminados, que confunden al lector cuando las barras son finas
  styles: `svg { display: block; max-width: 100%; height: auto; margin: 0 auto; shape-rendering: crispEdges; }`,
})
export class CodigoBarrasComponent {
  valor = input.required<string>();
  alto = input(70);

  private svg = viewChild.required<ElementRef<SVGSVGElement>>('svg');

  constructor() {
    effect(() => {
      JsBarcode(this.svg().nativeElement, this.valor(), {
        format: 'CODE128',
        height: this.alto(),
        // 3 px por barra fina: con 2 px, una cámara a distancia ya no distingue las barras juntas
        width: 3,
        // Zona en blanco a los lados: los lectores la necesitan para encontrar el inicio y el fin
        margin: 12,
        fontSize: 16,
        font: 'monospace',
      });
    });
  }
}
