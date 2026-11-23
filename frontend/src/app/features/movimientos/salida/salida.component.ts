import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, ElementRef, OnInit, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api.service';
import { mensajeError } from '../../../core/errores';
import { duracion, pesos } from '../../../core/formato';
import { METODOS_PAGO, MetodoPago, Tiquete } from '../../../core/models';
import { EscanerComponent } from '../../../shared/escaner/escaner.component';
import { ModalComponent } from '../../../shared/modal/modal.component';

/**
 * "PC-000123", "pc000123" o "123" -> "PC-000123". Si no parece un código, es una placa
 * (para el tiquete perdido) y devuelve null.
 */
export function normalizarCodigo(texto: string): string | null {
  const limpio = texto.trim().toUpperCase().replace(/\s/g, '');
  const m = limpio.match(/^(?:PC-?)?(\d{1,6})$/);
  return m ? `PC-${m[1].padStart(6, '0')}` : null;
}

/** RF-13 a RF-15: busca el tiquete (lector USB, cámara o digitado), muestra el cobro y registra el pago. */
@Component({
  selector: 'app-salida',
  imports: [DatePipe, FormsModule, RouterLink, ModalComponent, EscanerComponent],
  templateUrl: './salida.component.html',
  styleUrl: './salida.component.css',
})
export class SalidaComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  private campo = viewChild.required<ElementRef<HTMLInputElement>>('campo');

  protected texto = '';
  protected tiquete = signal<Tiquete | null>(null);
  protected perdido = signal(false);
  protected metodo = signal<MetodoPago>('EFECTIVO');
  protected buscando = signal(false);
  protected guardando = signal(false);
  protected error = signal('');
  protected ultimaSalida = signal<Tiquete | null>(null);
  protected camara = signal(false);

  protected metodos = METODOS_PAGO;
  protected duracion = duracion;
  protected pesos = pesos;

  ngOnInit(): void {
    const codigo = this.route.snapshot.queryParamMap.get('codigo');
    if (codigo) {
      this.texto = codigo;
      this.buscar();
    }
  }

  /** El lector USB escribe el código y envía Enter, que dispara esta búsqueda. */
  buscar(): void {
    const texto = this.texto.trim();
    if (!texto) return;
    this.error.set('');
    this.ultimaSalida.set(null);
    this.tiquete.set(null);
    this.buscando.set(true);

    const codigo = normalizarCodigo(texto);
    if (codigo) {
      this.perdido.set(false);
      this.cargarTiquete(codigo);
      return;
    }
    // No es un código: se busca el vehículo dentro por placa (tiquete perdido)
    const placa = texto.toUpperCase().replace(/[\s-]/g, '');
    this.api.tiquetesActivos(placa).subscribe({
      next: (lista) => {
        const exacto = lista.find((t) => t.placa === placa);
        if (!exacto) {
          this.buscando.set(false);
          this.error.set(`No hay ningún vehículo dentro con la placa ${placa}.`);
          return;
        }
        this.perdido.set(true);
        this.cargarTiquete(exacto.codigo);
      },
      error: (e: HttpErrorResponse) => this.fallo(e),
    });
  }

  private cargarTiquete(codigo: string): void {
    this.api.tiquete(codigo, this.perdido()).subscribe({
      next: (t) => {
        this.buscando.set(false);
        if (t.estado !== 'ABIERTO') {
          this.error.set(`El tiquete ${t.codigo} ya está ${t.estado_display.toLowerCase()}.`);
          return;
        }
        this.tiquete.set(t);
      },
      error: (e: HttpErrorResponse) =>
        this.fallo(e, e.status === 404 ? `No existe el tiquete ${codigo}.` : undefined),
    });
  }

  cambiarPerdido(perdido: boolean): void {
    const t = this.tiquete();
    this.perdido.set(perdido);
    if (t) this.cargarTiquete(t.codigo);
  }

  confirmar(): void {
    const t = this.tiquete();
    if (!t?.cobro) return;
    this.guardando.set(true);
    this.error.set('');
    const datos = {
      tiquete_perdido: this.perdido(),
      ...(t.cobro.total > 0 ? { metodo: this.metodo() } : {}),
    };
    this.api.registrarSalida(t.codigo, datos).subscribe({
      next: (cerrado) => {
        this.guardando.set(false);
        this.ultimaSalida.set(cerrado);
        this.limpiar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.error.set(mensajeError(e));
      },
    });
  }

  leidoPorCamara(codigo: string): void {
    this.camara.set(false);
    this.texto = codigo;
    this.buscar();
  }

  /** Deja la pantalla lista para el siguiente vehículo, con el foco en el campo del lector. */
  limpiar(): void {
    this.texto = '';
    this.tiquete.set(null);
    this.perdido.set(false);
    this.metodo.set('EFECTIVO');
    setTimeout(() => this.campo().nativeElement.focus());
  }

  private fallo(e: HttpErrorResponse, mensaje?: string): void {
    this.buscando.set(false);
    this.error.set(mensaje ?? mensajeError(e));
  }
}
