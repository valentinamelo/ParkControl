import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { EMPTY, catchError, forkJoin, switchMap, timer } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { mensajeError } from '../../core/errores';
import { duracion, pesos } from '../../core/formato';
import { DashboardResumen, Tiquete } from '../../core/models';
import { BarrasComponent } from '../../shared/graficos/barras.component';
import { ColumnasComponent } from '../../shared/graficos/columnas.component';
import { StatCardComponent } from '../../shared/stat-card/stat-card.component';
import { INTERVALO_ACTUALIZACION } from '../movimientos/movimientos.component';

/** RF-20: ocupación en tiempo real e ingresos del día (el trabajador ve los de su turno). */
@Component({
  selector: 'app-dashboard',
  imports: [DatePipe, RouterLink, StatCardComponent, BarrasComponent, ColumnasComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);
  protected auth = inject(AuthService);

  protected resumen = signal<DashboardResumen | null>(null);
  protected dentro = signal<Tiquete[]>([]);
  protected error = signal('');
  protected duracion = duracion;
  protected pesos = pesos;

  ngOnInit(): void {
    timer(0, INTERVALO_ACTUALIZACION)
      .pipe(
        switchMap(() =>
          forkJoin([this.api.dashboard(), this.api.tiquetesActivos()]).pipe(
            catchError((e: HttpErrorResponse) => {
              this.error.set(mensajeError(e));
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(([resumen, dentro]) => {
        this.error.set('');
        this.resumen.set(resumen);
        // Los que llevan más tiempo primero
        this.dentro.set([...dentro].sort((a, b) => (b.minutos_transcurridos ?? 0) - (a.minutos_transcurridos ?? 0)));
      });
  }
}
