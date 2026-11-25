import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api.service';
import { AuthService } from '../../../core/auth.service';
import { mensajeError } from '../../../core/errores';
import { tiempo, pesos } from '../../../core/formato';
import { Parqueadero, Tiquete } from '../../../core/models';
import { CodigoBarrasComponent } from '../../../shared/codigo-barras/codigo-barras.component';
import { ModalComponent } from '../../../shared/modal/modal.component';

/** RF-12: tiquete con código de barras listo para imprimir. Si ya está cerrado, sirve de recibo. */
@Component({
  selector: 'app-tiquete',
  imports: [DatePipe, FormsModule, RouterLink, CodigoBarrasComponent, ModalComponent],
  templateUrl: './tiquete.component.html',
  styleUrl: './tiquete.component.css',
})
export class TiqueteComponent implements OnInit {
  private api = inject(ApiService);
  protected auth = inject(AuthService);

  /** Parámetros de la ruta (withComponentInputBinding). */
  codigo = input.required<string>();
  nuevo = input<string>();

  protected tiquete = signal<Tiquete | null>(null);
  protected parqueadero = signal<Parqueadero | null>(null);
  protected error = signal('');
  protected tiempo = tiempo;
  protected pesos = pesos;

  // Anulación (solo admin, RF-24)
  protected modalAnular = signal(false);
  protected motivo = '';
  protected anulando = signal(false);
  protected errorAnular = signal('');
  protected aviso = signal('');

  ngOnInit(): void {
    this.api.parqueadero().subscribe((p) => this.parqueadero.set(p));
    this.api.tiquete(this.codigo()).subscribe({
      next: (t) => this.tiquete.set(t),
      error: (e: HttpErrorResponse) =>
        this.error.set(e.status === 404 ? `No existe el tiquete ${this.codigo()}.` : mensajeError(e)),
    });
  }

  imprimir(): void {
    window.print();
  }

  abrirAnulacion(): void {
    this.motivo = '';
    this.errorAnular.set('');
    this.modalAnular.set(true);
  }

  anular(): void {
    const t = this.tiquete();
    if (!t) return;
    this.anulando.set(true);
    this.errorAnular.set('');
    this.api.anularTiquete(t.codigo, this.motivo).subscribe({
      next: (anulado) => {
        this.anulando.set(false);
        this.modalAnular.set(false);
        this.tiquete.set(anulado);
        this.aviso.set(
          t.estado === 'ABIERTO'
            ? `Tiquete ${t.codigo} anulado. El espacio ${t.espacio} quedó libre.`
            : `Tiquete ${t.codigo} anulado. Su pago ya no cuenta en los ingresos.`,
        );
      },
      error: (e: HttpErrorResponse) => {
        this.anulando.set(false);
        this.errorAnular.set(mensajeError(e));
      },
    });
  }
}
