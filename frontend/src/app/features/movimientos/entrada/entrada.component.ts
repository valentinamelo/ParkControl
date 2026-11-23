import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { EMPTY, catchError, debounceTime, distinctUntilChanged, filter, map, switchMap, tap } from 'rxjs';

import { ApiService } from '../../../core/api.service';
import { AuthService } from '../../../core/auth.service';
import { erroresDeCampo, mensajeError } from '../../../core/errores';
import { ConsultaPlaca, Espacio, TipoVehiculo } from '../../../core/models';

const PLACA_VALIDA = /^[A-Z0-9]{4,8}$/;

function normalizarPlaca(texto: string): string {
  return texto.toUpperCase().replace(/[\s-]/g, '');
}

/** RF-11 y RF-18: registra la entrada, asigna un espacio compatible y genera el tiquete. */
@Component({
  selector: 'app-entrada',
  imports: [DatePipe, ReactiveFormsModule, RouterLink],
  templateUrl: './entrada.component.html',
  styleUrl: './entrada.component.css',
})
export class EntradaComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);
  protected auth = inject(AuthService);

  protected tipos = signal<TipoVehiculo[]>([]);
  protected consulta = signal<ConsultaPlaca | null>(null);
  protected consultando = signal(false);
  protected espacios = signal<Espacio[]>([]);
  protected espacioElegido = signal<number | null>(null);
  protected guardando = signal(false);
  protected error = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  /** El backend avisó que está fuera de horario y el admin puede confirmar. */
  protected confirmarHorario = signal(false);

  protected form = inject(FormBuilder).nonNullable.group({
    placa: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9 -]{4,10}$/)]],
    tipo_vehiculo: [0],
    marca: [''],
    modelo: [''],
    color: [''],
  });

  /** Tipo de vehículo efectivo: el registrado o el que se elige para un vehículo nuevo. */
  private tipoId = signal(0);
  protected tipoNombre = computed(() => {
    const registrado = this.consulta()?.vehiculo?.tipo_vehiculo_nombre;
    return registrado ?? this.tipos().find((t) => t.id === this.tipoId())?.nombre ?? '';
  });
  protected esNuevo = computed(() => this.consulta() !== null && this.consulta()!.vehiculo === null);
  protected yaDentro = computed(() => this.consulta()?.tiquete_abierto ?? null);

  ngOnInit(): void {
    this.api.tiposVehiculo().subscribe((t) => {
      this.tipos.set(t);
      this.form.controls.tipo_vehiculo.setValue(t[0]?.id ?? 0);
    });

    // Al escribir la placa, consulta si el vehículo existe, si ya está dentro o si tiene mensualidad
    this.form.controls.placa.valueChanges
      .pipe(
        map(normalizarPlaca),
        tap(() => this.reiniciarConsulta()),
        debounceTime(350),
        distinctUntilChanged(),
        filter((placa) => PLACA_VALIDA.test(placa)),
        tap(() => this.consultando.set(true)),
        switchMap((placa) => this.api.consultarPlaca(placa).pipe(catchError(() => EMPTY))),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((c) => {
        this.consultando.set(false);
        this.consulta.set(c);
        this.cargarEspacios();
      });

    this.form.controls.tipo_vehiculo.valueChanges.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((id) => {
      this.tipoId.set(id);
      if (this.esNuevo()) this.cargarEspacios();
    });
  }

  private reiniciarConsulta(): void {
    this.consulta.set(null);
    this.espacios.set([]);
    this.espacioElegido.set(null);
    this.confirmarHorario.set(false);
    this.error.set('');
  }

  /** Espacios libres del tipo; preselecciona el fijo de la mensualidad o el primero. */
  private cargarEspacios(): void {
    const consulta = this.consulta();
    if (!consulta || consulta.tiquete_abierto || !this.tipoNombre()) return;
    this.api.espaciosDisponibles(this.tipoNombre(), consulta.placa).subscribe((lista) => {
      this.espacios.set(lista);
      const fijo = consulta.mensualidad?.espacio_fijo_id;
      const preferido = lista.find((e) => e.id === fijo) ?? lista[0];
      this.espacioElegido.set(preferido?.id ?? null);
    });
  }

  registrar(forzar = false): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { placa, tipo_vehiculo, marca, modelo, color } = this.form.getRawValue();
    const datos = {
      placa: normalizarPlaca(placa),
      espacio: this.espacioElegido() ?? undefined,
      forzar,
      ...(this.esNuevo() ? { tipo_vehiculo, marca, modelo, color } : {}),
    };

    this.guardando.set(true);
    this.error.set('');
    this.erroresCampo.set({});
    this.api.registrarEntrada(datos).subscribe({
      next: (t) => this.router.navigate(['/movimientos/tiquete', t.codigo], { queryParams: { nuevo: 1 } }),
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.confirmarHorario.set(Boolean(e.error?.fuera_de_horario) && this.auth.esAdmin());
        this.erroresCampo.set(erroresDeCampo(e));
        this.error.set(mensajeError(e, false));
        this.cargarEspacios(); // otro puesto pudo haber ocupado el espacio elegido
      },
    });
  }

  protected errorPlaca(): string {
    const control = this.form.controls.placa;
    if (control.touched && control.invalid) return 'Escribe una placa válida (p. ej. ABC123).';
    return this.erroresCampo()['placa'] ?? '';
  }
}
