import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../core/api.service';
import { erroresDeCampo, mensajeError } from '../../../core/errores';
import { pesos } from '../../../core/formato';
import { Tarifa, TipoVehiculo } from '../../../core/models';
import { ModalComponent } from '../../../shared/modal/modal.component';

/** RF-07: tarifas por tipo de vehículo. Cambiar una tarifa crea una nueva y la anterior queda en el historial. */
@Component({
  selector: 'app-config-tarifas',
  imports: [DatePipe, ReactiveFormsModule, ModalComponent],
  templateUrl: './tarifas.component.html',
})
export class TarifasComponent implements OnInit {
  private api = inject(ApiService);
  private fb = inject(FormBuilder).nonNullable;

  protected tarifas = signal<Tarifa[]>([]);
  protected tipos = signal<TipoVehiculo[]>([]);
  protected historial = signal<Tarifa[] | null>(null);
  protected error = signal('');
  protected aviso = signal('');
  protected pesos = pesos;

  /** Tipos de vehículo que todavía no tienen tarifa: no se les podrá cobrar. */
  protected tiposSinTarifa = computed(() =>
    this.tipos().filter((t) => !this.tarifas().some((tarifa) => tarifa.tipo_vehiculo === t.id)),
  );

  // Modal de tarifa
  protected modalAbierto = signal(false);
  protected editando = signal<Tarifa | null>(null);
  protected guardando = signal(false);
  protected errorForm = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  protected form = this.fb.group({
    tipo_vehiculo: [0, Validators.min(1)],
    modalidad: ['HORA' as Tarifa['modalidad']],
    valor: [0, [Validators.required, Validators.min(1)]],
    minutos_fraccion: [60, [Validators.required, Validators.min(1)]],
    minutos_gracia: [0, [Validators.required, Validators.min(0)]],
    tope_diario: this.fb.control<number | null>(null, Validators.min(1)),
  });

  // Nuevo tipo de vehículo
  protected formTipo = this.fb.group({ nombre: ['', Validators.required] });

  ngOnInit(): void {
    this.cargar();
    // Por hora siempre son 60 minutos; por fracción el administrador los define
    this.form.controls.modalidad.valueChanges.subscribe((m) => {
      const fraccion = this.form.controls.minutos_fraccion;
      if (m === 'HORA') {
        fraccion.setValue(60);
        fraccion.disable();
      } else {
        fraccion.enable();
      }
    });
  }

  cargar(): void {
    this.api.tarifas().subscribe({
      next: (t) => this.tarifas.set(t),
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
    this.api.tiposVehiculo().subscribe((t) => this.tipos.set(t));
    if (this.historial()) this.verHistorial(true);
  }

  verHistorial(mostrar: boolean): void {
    if (!mostrar) {
      this.historial.set(null);
      return;
    }
    this.api.tarifas(true).subscribe((t) => this.historial.set(t.filter((tarifa) => !tarifa.vigente)));
  }

  abrirFormulario(tarifa: Tarifa | null, tipoId?: number): void {
    this.editando.set(tarifa);
    this.errorForm.set('');
    this.erroresCampo.set({});
    this.form.reset({
      tipo_vehiculo: tarifa?.tipo_vehiculo ?? tipoId ?? this.tiposSinTarifa()[0]?.id ?? 0,
      modalidad: tarifa?.modalidad ?? 'HORA',
      valor: tarifa ? Number(tarifa.valor) : 0,
      minutos_fraccion: tarifa?.minutos_fraccion ?? 60,
      minutos_gracia: tarifa?.minutos_gracia ?? 0,
      tope_diario: tarifa?.tope_diario ? Number(tarifa.tope_diario) : null,
    });
    this.modalAbierto.set(true);
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { tipo_vehiculo, modalidad, valor, minutos_fraccion, minutos_gracia, tope_diario } = this.form.getRawValue();
    const datos = { modalidad, minutos_fraccion, minutos_gracia, valor: String(valor), tope_diario: tope_diario ? String(tope_diario) : null };
    const editando = this.editando();
    const peticion = editando
      ? this.api.cambiarTarifa(editando.id, datos)
      : this.api.crearTarifa({ ...datos, tipo_vehiculo });

    this.guardando.set(true);
    peticion.subscribe({
      next: (t) => {
        this.guardando.set(false);
        this.modalAbierto.set(false);
        this.aviso.set(
          editando
            ? `Nueva tarifa de ${t.tipo_vehiculo_nombre} vigente. La anterior quedó en el historial.`
            : `Tarifa de ${t.tipo_vehiculo_nombre} creada.`,
        );
        this.cargar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresCampo.set(erroresDeCampo(e));
        this.errorForm.set(mensajeError(e, false));
      },
    });
  }

  crearTipo(): void {
    const nombre = this.formTipo.controls.nombre.value.trim();
    if (!nombre) return;
    this.error.set('');
    this.api.crearTipoVehiculo(nombre).subscribe({
      next: (t) => {
        this.formTipo.reset();
        this.aviso.set(`Tipo de vehículo ${t.nombre} creado. Asígnale una tarifa.`);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  eliminarTipo(tipo: TipoVehiculo): void {
    if (!confirm(`¿Eliminar el tipo de vehículo ${tipo.nombre}?`)) return;
    this.error.set('');
    this.api.eliminarTipoVehiculo(tipo.id).subscribe({
      next: () => {
        this.aviso.set(`Tipo de vehículo ${tipo.nombre} eliminado.`);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  protected nombreTipo(id: number): string {
    return this.tipos().find((t) => t.id === id)?.nombre ?? '';
  }

  protected errorDe(campo: 'valor' | 'minutos_fraccion' | 'minutos_gracia' | 'tope_diario'): string {
    const control = this.form.controls[campo];
    if (control.touched && control.invalid) {
      return campo === 'minutos_gracia' ? 'No puede ser negativo.' : 'Debe ser mayor que cero.';
    }
    return this.erroresCampo()[campo] ?? '';
  }
}
