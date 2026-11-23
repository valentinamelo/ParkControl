import { Component, ElementRef, OnDestroy, OnInit, output, signal, viewChild } from '@angular/core';
import type { IScannerControls } from '@zxing/browser';

/**
 * Lee un código de barras con la cámara (alternativa al lector USB).
 * La librería se carga solo cuando se abre el escáner.
 */
@Component({
  selector: 'app-escaner',
  template: `
    @if (error()) {
      <div class="alerta">{{ error() }}</div>
    } @else {
      <div class="visor">
        <video #video muted playsinline></video>
        <div class="linea"></div>
      </div>
      <p class="nota">Apunta la cámara al código de barras del tiquete.</p>
    }
  `,
  styles: `
    .visor { position: relative; border-radius: var(--radio); overflow: hidden; background: var(--negro); aspect-ratio: 4 / 3; }
    video { width: 100%; height: 100%; object-fit: cover; display: block; }
    .linea { position: absolute; left: 8%; right: 8%; top: 50%; height: 2px; background: var(--amarillo); box-shadow: 0 0 8px var(--amarillo); }
    .nota { margin-top: 10px; text-align: center; }
  `,
})
export class EscanerComponent implements OnInit, OnDestroy {
  leido = output<string>();

  protected error = signal('');
  private video = viewChild<ElementRef<HTMLVideoElement>>('video');
  private controles?: IScannerControls;
  private destruido = false;

  async ngOnInit(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      this.error.set('Este navegador no permite usar la cámara (se necesita https o localhost).');
      return;
    }
    try {
      const { BrowserMultiFormatReader } = await import('@zxing/browser');
      const video = this.video()?.nativeElement;
      if (this.destruido || !video) return;
      this.controles = await new BrowserMultiFormatReader().decodeFromConstraints(
        { video: { facingMode: 'environment' } },
        video,
        (resultado) => {
          if (resultado) {
            this.detener();
            this.leido.emit(resultado.getText());
          }
        },
      );
      if (this.destruido) this.detener();
    } catch {
      this.error.set('No se pudo abrir la cámara. Revisa el permiso del navegador o digita el código.');
    }
  }

  ngOnDestroy(): void {
    this.destruido = true;
    this.detener();
  }

  private detener(): void {
    this.controles?.stop();
    this.controles = undefined;
  }
}
