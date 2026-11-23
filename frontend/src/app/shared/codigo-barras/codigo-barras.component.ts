import { Component, ElementRef, effect, input, viewChild } from '@angular/core';
import JsBarcode from 'jsbarcode';

/** Código de barras Code128 en SVG (se imprime nítido). Lo lee cualquier lector USB. */
@Component({
  selector: 'app-codigo-barras',
  template: `<svg #svg role="img" [attr.aria-label]="'Código de barras ' + valor()"></svg>`,
  styles: `svg { display: block; max-width: 100%; height: auto; margin: 0 auto; }`,
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
        width: 2,
        margin: 0,
        fontSize: 16,
        font: 'monospace',
      });
    });
  }
}
