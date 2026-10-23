import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../core/api.service';
import { erroresDeCampo, mensajeError } from '../../../core/errores';

/** Datos generales del parqueadero (salen en el tiquete a partir del avance 3). */
@Component({
  selector: 'app-config-parqueadero',
  imports: [ReactiveFormsModule],
  template: `
    <form class="card formulario" [formGroup]="form" (ngSubmit)="guardar()">
      <h2>Datos del parqueadero</h2>
      @if (error()) { <div class="alerta">{{ error() }}</div> }
      @if (aviso()) { <div class="exito">{{ aviso() }}</div> }

      <div class="campo">
        <label for="nombre">Nombre</label>
        <input class="input" id="nombre" formControlName="nombre" [class.invalido]="errorDe('nombre')" />
        @if (errorDe('nombre')) { <small class="error">{{ errorDe('nombre') }}</small> }
      </div>
      <div class="campos-2">
        <div class="campo">
          <label for="nit">NIT</label>
          <input class="input" id="nit" formControlName="nit" />
        </div>
        <div class="campo">
          <label for="telefono">Teléfono</label>
          <input class="input" id="telefono" formControlName="telefono" />
        </div>
      </div>
      <div class="campo">
        <label for="direccion">Dirección</label>
        <input class="input" id="direccion" formControlName="direccion" />
      </div>
      <div class="acciones">
        <button class="btn btn-primario" type="submit" [disabled]="guardando() || form.pristine">
          {{ guardando() ? 'Guardando…' : 'Guardar cambios' }}
        </button>
      </div>
    </form>
  `,
  styles: `.formulario { max-width: 640px; }`,
})
export class ParqueaderoComponent implements OnInit {
  private api = inject(ApiService);

  protected guardando = signal(false);
  protected error = signal('');
  protected aviso = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  protected form = inject(FormBuilder).nonNullable.group({
    nombre: ['', Validators.required],
    nit: [''],
    direccion: [''],
    telefono: [''],
  });

  ngOnInit(): void {
    this.api.parqueadero().subscribe({
      next: (p) => this.form.reset(p),
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.error.set('');
    this.aviso.set('');
    this.api.actualizarParqueadero(this.form.getRawValue()).subscribe({
      next: (p) => {
        this.guardando.set(false);
        this.form.reset(p);
        this.aviso.set('Datos del parqueadero guardados.');
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresCampo.set(erroresDeCampo(e));
        this.error.set(mensajeError(e, false));
      },
    });
  }

  protected errorDe(campo: 'nombre'): string {
    const control = this.form.controls[campo];
    if (control.touched && control.invalid) return 'El nombre es obligatorio.';
    return this.erroresCampo()[campo] ?? '';
  }
}
