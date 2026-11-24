import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { EMPTY, Subject, catchError, merge, switchMap, timer } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { mensajeError } from '../../core/errores';
import { duracion, pesos } from '../../core/formato';
import { Tiquete } from '../../core/models';

/** Cada cuánto se actualiza la lista de vehículos dentro (la planeación pide 10–15 s). */
export const INTERVALO_ACTUALIZACION = 15_000;

@Component({
  selector: 'app-movimientos',
  imports: [DatePipe, RouterLink],
  templateUrl: './movimientos.component.html',
})
export class MovimientosComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);
  private recargar$ = new Subject<void>();

  protected activos = signal<Tiquete[]>([]);
  protected recientes = signal<Tiquete[]>([]);
  protected disponibles = signal(0);
  protected cargando = signal(true);
  protected error = signal('');
  /** Salida recién registrada: llega desde la pantalla de salida en el estado de la navegación. */
  protected ultimaSalida = signal<Tiquete | null>(
    inject(Router).currentNavigation()?.extras.state?.['salida'] ?? null,
  );
  protected duracion = duracion;
  protected pesos = pesos;

  protected total = computed(() => this.activos().length);

  ngOnInit(): void {
    // Carga al entrar, cada 15 s y cuando se pulsa "Actualizar"
    merge(timer(0, INTERVALO_ACTUALIZACION), this.recargar$)
      .pipe(
        // Si una consulta falla se muestra el error, pero se sigue intentando en la siguiente vuelta
        switchMap(() =>
          this.api.tiquetesActivos().pipe(
            catchError((e: HttpErrorResponse) => {
              this.error.set(mensajeError(e));
              this.cargando.set(false);
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((t) => {
        this.activos.set(t);
        this.cargando.set(false);
        this.error.set('');
        this.cargarResumen();
      });
  }

  cargar(): void {
    this.recargar$.next();
  }

  private cargarResumen(): void {
    this.api.espacios({ estado: 'DISPONIBLE' }).subscribe((e) => this.disponibles.set(e.length));
    this.api.tiquetes({ estado: 'CERRADO' }).subscribe((t) => this.recientes.set(t.slice(0, 8)));
  }
}
