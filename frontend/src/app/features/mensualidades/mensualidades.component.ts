import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, filter, map, switchMap } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { erroresDeCampo, mensajeError } from '../../core/errores';
import { pesos } from '../../core/formato';
import { Espacio, METODOS_PAGO, Mensualidad, MetodoPago, PlanMensual } from '../../core/models';
import { ModalComponent } from '../../shared/modal/modal.component';

/** "2026-11-03" en la zona horaria del navegador (no en UTC). */
function fechaLocal(fecha = new Date()): string {
  const d = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60_000);
  return d.toISOString().slice(0, 10);
}

type Filtro = 'VIGENTE' | 'VENCIDA' | '';

/** RF-17: vender y renovar mensualidades (admin y trabajador). */
@Component({
  selector: 'app-mensualidades',
  imports: [DatePipe, ReactiveFormsModule, ModalComponent],
  templateUrl: './mensualidades.component.html',
})
export class MensualidadesComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();
  private textoBuscado = '';

  protected mensualidades = signal<Mensualidad[]>([]);
  protected filtro = signal<Filtro>('VIGENTE');
  protected cargando = signal(true);
  protected error = signal('');
  protected aviso = signal('');
  protected pesos = pesos;
  protected metodos = METODOS_PAGO;
  protected filtros: { valor: Filtro; texto: string }[] = [
    { valor: 'VIGENTE', texto: 'Vigentes' },
    { valor: 'VENCIDA', texto: 'Vencidas' },
    { valor: '', texto: 'Todas' },
  ];

  // --- Venta ---
  private fb = inject(FormBuilder).nonNullable;
  protected planes = signal<PlanMensual[]>([]);
  protected espaciosPlan = signal<Espacio[]>([]);
  protected clienteExistente = signal(false);
  protected modalVenta = signal(false);
  protected guardando = signal(false);
  protected errorForm = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  protected form = this.fb.group({
    documento: ['', Validators.required],
    nombre: [''],
    telefono: [''],
    correo: ['', Validators.email],
    placa: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9 -]{4,10}$/)]],
    plan: [0, Validators.min(1)],
    espacio_fijo: this.fb.control<number | null>(null),
    fecha_inicio: [fechaLocal(), Validators.required],
    metodo: ['EFECTIVO' as MetodoPago],
  });
  private planId = toSignal(this.form.controls.plan.valueChanges, { initialValue: 0 });
  private inicio = toSignal(this.form.controls.fecha_inicio.valueChanges, { initialValue: fechaLocal() });
  protected planElegido = computed(() => this.planes().find((p) => p.id === this.planId()) ?? null);
  /** Fecha final que tendrá: el día de inicio cuenta como el primero. */
  protected finVenta = computed(() => {
    const plan = this.planElegido();
    if (!plan || !this.inicio()) return null;
    const fin = new Date(`${this.inicio()}T00:00:00`);
    fin.setDate(fin.getDate() + plan.dias - 1);
    return fin;
  });
  protected hoy = fechaLocal();

  // --- Renovación ---
  protected renovando = signal<Mensualidad | null>(null);
  protected metodoRenovacion = signal<MetodoPago>('EFECTIVO');

  ngOnInit(): void {
    this.busqueda$
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap(() => this.consulta()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (m) => {
          this.mensualidades.set(m);
          this.cargando.set(false);
        },
        error: (e: HttpErrorResponse) => {
          this.error.set(mensajeError(e));
          this.cargando.set(false);
        },
      });
    this.busqueda$.next('');
    this.api.planesMensuales(true).subscribe((p) => this.planes.set(p));

    // Espacios que se pueden dejar como fijos: los activos del tipo del plan
    this.form.controls.plan.valueChanges
      .pipe(
        map((id) => this.planes().find((p) => p.id === id)),
        filter((plan) => plan !== undefined),
        switchMap((plan) => this.api.espacios({ tipo: plan!.tipo_vehiculo_nombre })),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((e) => {
        this.espaciosPlan.set(e.filter((espacio) => espacio.estado !== 'INACTIVO'));
        this.form.controls.espacio_fijo.setValue(null);
      });

    // Si el documento ya es de un cliente, se llenan sus datos
    this.form.controls.documento.valueChanges
      .pipe(
        map((d) => d.trim()),
        debounceTime(400),
        distinctUntilChanged(),
        filter((d) => d.length >= 3),
        switchMap((d) => this.api.clientePorDocumento(d)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(([cliente]) => {
        this.clienteExistente.set(Boolean(cliente));
        if (cliente) {
          this.form.patchValue({ nombre: cliente.nombre, telefono: cliente.telefono, correo: cliente.correo });
        }
      });
  }

  private consulta() {
    this.cargando.set(true);
    return this.api.mensualidades({ estado: this.filtro(), q: this.textoBuscado.trim() });
  }

  private recargar(): void {
    this.consulta().subscribe((m) => {
      this.mensualidades.set(m);
      this.cargando.set(false);
    });
  }

  buscar(texto: string): void {
    this.textoBuscado = texto;
    this.busqueda$.next(texto);
  }

  cambiarFiltro(filtro: Filtro): void {
    this.filtro.set(filtro);
    this.recargar();
  }

  // --- Venta ---

  abrirVenta(): void {
    this.errorForm.set('');
    this.erroresCampo.set({});
    this.clienteExistente.set(false);
    this.form.reset({ fecha_inicio: fechaLocal(), metodo: 'EFECTIVO', plan: this.planes()[0]?.id ?? 0 });
    this.modalVenta.set(true);
  }

  vender(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.errorForm.set('');
    this.api.venderMensualidad(this.form.getRawValue()).subscribe({
      next: (m) => {
        this.guardando.set(false);
        this.modalVenta.set(false);
        this.aviso.set(`Mensualidad de ${m.placa} vendida hasta el ${this.fecha(m.fecha_fin)} (${pesos(m.valor_pagado)}).`);
        this.recargar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresCampo.set(erroresDeCampo(e));
        this.errorForm.set(mensajeError(e, false));
      },
    });
  }

  // --- Renovación ---

  abrirRenovacion(m: Mensualidad): void {
    this.errorForm.set('');
    this.metodoRenovacion.set('EFECTIVO');
    this.renovando.set(m);
  }

  renovar(): void {
    const m = this.renovando();
    if (!m) return;
    this.guardando.set(true);
    this.api.renovarMensualidad(m.id, this.metodoRenovacion()).subscribe({
      next: (nueva) => {
        this.guardando.set(false);
        this.renovando.set(null);
        this.aviso.set(`Mensualidad de ${nueva.placa} renovada del ${this.fecha(nueva.fecha_inicio)} al ${this.fecha(nueva.fecha_fin)}.`);
        this.recargar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.errorForm.set(mensajeError(e));
      },
    });
  }

  /** "2026-12-02" -> "02/12/2026" sin pasar por UTC. */
  protected fecha(iso: string): string {
    const [a, m, d] = iso.split('-');
    return `${d}/${m}/${a}`;
  }

  protected errorDe(campo: 'documento' | 'nombre' | 'correo' | 'placa' | 'plan' | 'espacio_fijo' | 'fecha_inicio'): string {
    const control = this.form.controls[campo];
    if (control.touched && control.invalid) {
      const mensajes: Record<string, string> = {
        documento: 'El documento es obligatorio.',
        correo: 'Escribe un correo válido.',
        placa: 'Escribe una placa válida (p. ej. ABC123).',
        plan: 'Elige un plan.',
        fecha_inicio: 'Elige la fecha de inicio.',
      };
      return mensajes[campo] ?? '';
    }
    return this.erroresCampo()[campo] ?? '';
  }
}
