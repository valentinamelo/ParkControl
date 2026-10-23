import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { catchError, forkJoin, map, of } from 'rxjs';

import { ApiService } from '../../../core/api.service';
import { erroresDeCampo, mensajeError } from '../../../core/errores';
import { Horario } from '../../../core/models';

type FilaDia = FormGroup<{
  id: FormControl<number>;
  dia: FormControl<string>;
  abierto: FormControl<boolean>;
  hora_apertura: FormControl<string>;
  hora_cierre: FormControl<string>;
}>;

/** RF-08: horario de atención por día de la semana. Se editan los 7 días y se guardan juntos. */
@Component({
  selector: 'app-config-horarios',
  imports: [ReactiveFormsModule],
  templateUrl: './horarios.component.html',
  styles: `
    td { padding: 10px 12px; }
    input[type='time'] { max-width: 140px; }
  `,
})
export class HorariosComponent implements OnInit {
  private api = inject(ApiService);
  private fb = inject(FormBuilder).nonNullable;

  protected form = this.fb.group({ dias: this.fb.array<FilaDia>([]) });
  protected dias = this.form.controls.dias;
  protected guardando = signal(false);
  protected error = signal('');
  protected aviso = signal('');
  /** Errores del backend por id de horario. */
  protected erroresFila = signal<Record<number, string>>({});

  ngOnInit(): void {
    this.api.horarios().subscribe({
      next: (h) => this.llenar(h),
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  private filaDia(h: Horario): FilaDia {
    return this.fb.group({
      id: [h.id],
      dia: [h.dia],
      abierto: [h.abierto],
      hora_apertura: [h.hora_apertura.slice(0, 5)],
      hora_cierre: [h.hora_cierre.slice(0, 5)],
    });
  }

  private llenar(horarios: Horario[]): void {
    this.dias.clear();
    horarios.forEach((h) => this.dias.push(this.filaDia(h)));
    this.dias.markAsPristine();
  }

  /** Guarda solo los días que cambiaron; los errores se muestran en la fila de cada día. */
  guardar(): void {
    const cambiados = this.dias.controls.filter((fila) => fila.dirty);
    if (!cambiados.length) return;
    this.guardando.set(true);
    this.error.set('');
    this.aviso.set('');
    this.erroresFila.set({});

    const peticiones = cambiados.map((fila) => {
      const { id, abierto, hora_apertura, hora_cierre } = fila.getRawValue();
      return this.api.actualizarHorario(id, { abierto, hora_apertura, hora_cierre }).pipe(
        map((h) => {
          fila.reset(this.filaDia(h).getRawValue());
          return true;
        }),
        catchError((e: HttpErrorResponse) => {
          const campos = Object.values(erroresDeCampo(e));
          this.erroresFila.update((errores) => ({ ...errores, [id]: campos.join(' ') || mensajeError(e) }));
          return of(false);
        }),
      );
    });

    forkJoin(peticiones).subscribe((resultados) => {
      this.guardando.set(false);
      if (resultados.every(Boolean)) {
        this.aviso.set('Horario guardado.');
      } else {
        this.error.set('Algunos días no se guardaron. Revisa los marcados.');
      }
    });
  }
}
