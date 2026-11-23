import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/api.service';
import { erroresDeCampo, mensajeError } from '../../../core/errores';
import { pesos } from '../../../core/formato';
import { PlanMensual, TipoVehiculo } from '../../../core/models';
import { ModalComponent } from '../../../shared/modal/modal.component';

/** RF-16: planes de mensualidad por tipo de vehículo. Un plan ya vendido no se borra, se desactiva. */
@Component({
  selector: 'app-config-planes',
  imports: [ReactiveFormsModule, ModalComponent],
  templateUrl: './planes.component.html',
})
export class PlanesComponent implements OnInit {
  private api = inject(ApiService);

  protected planes = signal<PlanMensual[]>([]);
  protected tipos = signal<TipoVehiculo[]>([]);
  protected error = signal('');
  protected aviso = signal('');
  protected pesos = pesos;

  protected modalAbierto = signal(false);
  protected editando = signal<PlanMensual | null>(null);
  protected guardando = signal(false);
  protected errorForm = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  protected form = inject(FormBuilder).nonNullable.group({
    nombre: ['', Validators.required],
    tipo_vehiculo: [0, Validators.min(1)],
    valor: [0, [Validators.required, Validators.min(1)]],
    dias: [30, [Validators.required, Validators.min(1)]],
  });

  ngOnInit(): void {
    this.cargar();
    this.api.tiposVehiculo().subscribe((t) => this.tipos.set(t));
  }

  cargar(): void {
    this.api.planesMensuales().subscribe({
      next: (p) => this.planes.set(p),
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  abrirFormulario(plan: PlanMensual | null = null): void {
    this.editando.set(plan);
    this.errorForm.set('');
    this.erroresCampo.set({});
    this.form.reset({
      nombre: plan?.nombre ?? '',
      tipo_vehiculo: plan?.tipo_vehiculo ?? this.tipos()[0]?.id ?? 0,
      valor: plan ? Number(plan.valor) : 0,
      dias: plan?.dias ?? 30,
    });
    this.modalAbierto.set(true);
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { valor, ...resto } = this.form.getRawValue();
    const datos = { ...resto, valor: String(valor) };
    const editando = this.editando();
    const peticion = editando ? this.api.actualizarPlan(editando.id, datos) : this.api.crearPlan(datos);
    this.guardando.set(true);
    peticion.subscribe({
      next: (p) => {
        this.guardando.set(false);
        this.modalAbierto.set(false);
        this.aviso.set(editando ? `Plan ${p.nombre} actualizado. Las mensualidades ya vendidas no cambian.` : `Plan ${p.nombre} creado.`);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresCampo.set(erroresDeCampo(e));
        this.errorForm.set(mensajeError(e, false));
      },
    });
  }

  cambiarEstado(plan: PlanMensual): void {
    this.error.set('');
    this.aviso.set('');
    const peticion: Observable<unknown> = plan.activo
      ? this.api.eliminarPlan(plan.id)
      : this.api.actualizarPlan(plan.id, { activo: true });
    peticion.subscribe({
      next: () => {
        this.aviso.set(plan.activo ? `El plan ${plan.nombre} ya no se vende.` : `El plan ${plan.nombre} se vuelve a vender.`);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  protected errorDe(campo: 'nombre' | 'valor' | 'dias'): string {
    const control = this.form.controls[campo];
    if (control.touched && control.invalid) {
      return campo === 'nombre' ? 'El nombre es obligatorio.' : 'Debe ser mayor que cero.';
    }
    return this.erroresCampo()[campo] ?? '';
  }
}
