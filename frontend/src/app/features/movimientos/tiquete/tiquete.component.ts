import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api.service';
import { mensajeError } from '../../../core/errores';
import { duracion, pesos } from '../../../core/formato';
import { Parqueadero, Tiquete } from '../../../core/models';
import { CodigoBarrasComponent } from '../../../shared/codigo-barras/codigo-barras.component';

/** RF-12: tiquete con código de barras listo para imprimir. Si ya está cerrado, sirve de recibo. */
@Component({
  selector: 'app-tiquete',
  imports: [DatePipe, RouterLink, CodigoBarrasComponent],
  templateUrl: './tiquete.component.html',
  styleUrl: './tiquete.component.css',
})
export class TiqueteComponent implements OnInit {
  private api = inject(ApiService);

  /** Parámetros de la ruta (withComponentInputBinding). */
  codigo = input.required<string>();
  nuevo = input<string>();

  protected tiquete = signal<Tiquete | null>(null);
  protected parqueadero = signal<Parqueadero | null>(null);
  protected error = signal('');
  protected duracion = duracion;
  protected pesos = pesos;

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
}
