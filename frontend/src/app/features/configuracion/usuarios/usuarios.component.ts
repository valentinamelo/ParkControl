import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../core/api.service';
import { AuthService } from '../../../core/auth.service';
import { erroresDeCampo, mensajeError } from '../../../core/errores';
import { Rol, Usuario, UsuarioForm } from '../../../core/models';
import { ModalComponent } from '../../../shared/modal/modal.component';

type CampoUsuario = 'email' | 'first_name' | 'password';

/** RF-03: el administrador crea, edita, desactiva y reactiva usuarios. */
@Component({
  selector: 'app-config-usuarios',
  imports: [ReactiveFormsModule, ModalComponent],
  templateUrl: './usuarios.component.html',
})
export class UsuariosComponent implements OnInit {
  private api = inject(ApiService);
  protected auth = inject(AuthService);

  protected usuarios = signal<Usuario[]>([]);
  protected cargando = signal(true);
  protected error = signal('');
  protected aviso = signal('');

  protected modalAbierto = signal(false);
  protected editando = signal<Usuario | null>(null);
  protected guardando = signal(false);
  protected errorForm = signal('');
  protected erroresCampo = signal<Record<string, string>>({});
  protected form = inject(FormBuilder).nonNullable.group({
    first_name: ['', Validators.required],
    last_name: [''],
    email: ['', [Validators.required, Validators.email]],
    rol: ['TRABAJADOR' as Rol],
    password: [''],
  });

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.api.usuarios().subscribe({
      next: (u) => {
        this.usuarios.set(u);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.error.set(mensajeError(e));
        this.cargando.set(false);
      },
    });
  }

  abrirFormulario(usuario: Usuario | null = null): void {
    this.editando.set(usuario);
    this.errorForm.set('');
    this.erroresCampo.set({});
    this.form.reset({
      first_name: usuario?.first_name ?? '',
      last_name: usuario?.last_name ?? '',
      email: usuario?.email ?? '',
      rol: usuario?.rol ?? 'TRABAJADOR',
      password: '',
    });
    // Al crear la contraseña es obligatoria; al editar, vacía significa "no cambiarla"
    this.form.controls.password.setValidators(usuario ? [] : [Validators.required]);
    this.form.controls.password.updateValueAndValidity();
    // El administrador no puede quitarse su propio rol
    if (usuario && this.esYo(usuario)) this.form.controls.rol.disable();
    else this.form.controls.rol.enable();
    this.modalAbierto.set(true);
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const datos: Partial<UsuarioForm> = this.form.getRawValue();
    if (!datos.password) delete datos.password;
    const editando = this.editando();
    const peticion = editando
      ? this.api.actualizarUsuario(editando.id, datos)
      : this.api.crearUsuario(datos as UsuarioForm);

    this.guardando.set(true);
    peticion.subscribe({
      next: (u) => {
        this.guardando.set(false);
        this.modalAbierto.set(false);
        this.aviso.set(editando ? `Usuario ${u.email} actualizado.` : `Usuario ${u.email} creado. Ya puede iniciar sesión.`);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresCampo.set(erroresDeCampo(e));
        this.errorForm.set(mensajeError(e, false));
      },
    });
  }

  cambiarEstado(usuario: Usuario): void {
    const desactivar = usuario.is_active;
    if (desactivar && !confirm(`¿Desactivar a ${usuario.nombre}? No podrá iniciar sesión.`)) return;
    this.error.set('');
    this.aviso.set('');
    const peticion = desactivar
      ? this.api.desactivarUsuario(usuario.id)
      : this.api.actualizarUsuario(usuario.id, { is_active: true });
    peticion.subscribe({
      next: () => {
        this.aviso.set(desactivar ? `${usuario.nombre} fue desactivado.` : `${usuario.nombre} fue activado.`);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => this.error.set(mensajeError(e)),
    });
  }

  protected esYo(usuario: Usuario): boolean {
    return usuario.id === this.auth.usuario()?.id;
  }

  protected errorDe(campo: CampoUsuario): string {
    const control = this.form.controls[campo];
    if (control.touched && control.invalid) {
      return { email: 'Escribe un correo válido.', first_name: 'El nombre es obligatorio.', password: 'La contraseña es obligatoria.' }[campo];
    }
    return this.erroresCampo()[campo] ?? '';
  }
}
