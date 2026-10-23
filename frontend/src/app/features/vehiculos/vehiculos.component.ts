import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { erroresDeCampo, mensajeError } from '../../core/errores';
import { TipoVehiculo, Vehiculo } from '../../core/models';
import { ModalComponent } from '../../shared/modal/modal.component';

@Component({
  selector: 'app-vehiculos',
  imports: [ReactiveFormsModule, ModalComponent],
  templateUrl: './vehiculos.component.html',
})
export class VehiculosComponent implements OnInit {
  private api = inject(ApiService);
  private busqueda$ = new Subject<string>();
  private textoBuscado = '';

  protected vehiculos = signal<Vehiculo[]>([]);
  protected tipos = signal<TipoVehiculo[]>([]);
  protected cargando = signal(true);
  protected error = signal('');
  protected aviso = signal('');

  // Formulario de registro / edición (en un modal)
  protected modalAbierto = signal(false);
  protected editando = signal<Vehiculo | null>(null);
  protected guardando = signal(false);
  protected errorForm = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  protected form = inject(FormBuilder).nonNullable.group({
    placa: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9 -]{4,10}$/)]],
    tipo_vehiculo: [0, Validators.min(1)],
    marca: [''],
    modelo: [''],
    color: [''],
  });

  ngOnInit(): void {
    // Busca en la API 300 ms después de que el usuario deja de escribir
    this.busqueda$
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap((placa) => {
          this.cargando.set(true);
          return this.api.vehiculos(placa.trim());
        }),
      )
      .subscribe({
        next: (v) => {
          this.vehiculos.set(v);
          this.cargando.set(false);
        },
        error: () => {
          this.error.set('No se pudieron cargar los vehículos.');
          this.cargando.set(false);
        },
      });
    this.busqueda$.next('');
    this.api.tiposVehiculo().subscribe((t) => this.tipos.set(t));
  }

  buscar(texto: string): void {
    this.textoBuscado = texto;
    this.busqueda$.next(texto);
  }

  /** Vuelve a pedir la lista con la búsqueda actual (después de guardar o eliminar). */
  private recargar(): void {
    this.api.vehiculos(this.textoBuscado.trim()).subscribe((v) => this.vehiculos.set(v));
  }

  abrirFormulario(vehiculo: Vehiculo | null = null): void {
    this.editando.set(vehiculo);
    this.errorForm.set('');
    this.erroresCampo.set({});
    this.form.reset({
      placa: vehiculo?.placa ?? '',
      tipo_vehiculo: vehiculo?.tipo_vehiculo ?? this.tipos()[0]?.id ?? 0,
      marca: vehiculo?.marca ?? '',
      modelo: vehiculo?.modelo ?? '',
      color: vehiculo?.color ?? '',
    });
    this.modalAbierto.set(true);
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    const datos = this.form.getRawValue();
    const editando = this.editando();
    const peticion = editando ? this.api.actualizarVehiculo(editando.id, datos) : this.api.crearVehiculo(datos);

    peticion.subscribe({
      next: (v) => {
        this.guardando.set(false);
        this.modalAbierto.set(false);
        this.aviso.set(editando ? `Vehículo ${v.placa} actualizado.` : `Vehículo ${v.placa} registrado.`);
        this.recargar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresCampo.set(erroresDeCampo(e));
        this.errorForm.set(mensajeError(e, false));
      },
    });
  }

  eliminar(vehiculo: Vehiculo): void {
    if (!confirm(`¿Eliminar el vehículo ${vehiculo.placa}?`)) return;
    this.error.set('');
    this.api.eliminarVehiculo(vehiculo.id).subscribe({
      next: () => {
        this.aviso.set(`Vehículo ${vehiculo.placa} eliminado.`);
        this.recargar();
      },
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  /** Error de un campo: el del backend o el de la validación local. */
  protected errorDe(campo: 'placa' | 'tipo_vehiculo'): string {
    const control = this.form.controls[campo];
    if (control.touched && control.invalid) {
      return campo === 'placa' ? 'Escribe una placa válida (p. ej. ABC123).' : 'Elige el tipo de vehículo.';
    }
    return this.erroresCampo()[campo] ?? '';
  }
}
