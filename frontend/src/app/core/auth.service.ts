import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { LoginRespuesta, Rol, Usuario } from './models';

const CLAVE_TOKEN = 'pc_access';
const CLAVE_USUARIO = 'pc_usuario';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private usuarioActual = signal<Usuario | null>(this.leerUsuario());

  readonly usuario = this.usuarioActual.asReadonly();
  readonly autenticado = computed(() => this.usuarioActual() !== null);
  readonly esAdmin = computed(() => this.usuarioActual()?.rol === 'ADMIN');

  login(email: string, password: string): Observable<LoginRespuesta> {
    return this.http
      .post<LoginRespuesta>(`${environment.apiUrl}/auth/login/`, { email, password })
      .pipe(
        tap((r) => {
          localStorage.setItem(CLAVE_TOKEN, r.access);
          localStorage.setItem(CLAVE_USUARIO, JSON.stringify(r.usuario));
          this.usuarioActual.set(r.usuario);
        }),
      );
  }

  logout(): void {
    localStorage.removeItem(CLAVE_TOKEN);
    localStorage.removeItem(CLAVE_USUARIO);
    this.usuarioActual.set(null);
    this.router.navigate(['/login']);
  }

  token(): string | null {
    return localStorage.getItem(CLAVE_TOKEN);
  }

  /** Ruta de inicio según el rol: el admin ve el dashboard, el trabajador va a movimientos. */
  rutaInicio(rol?: Rol): string {
    return (rol ?? this.usuarioActual()?.rol) === 'ADMIN' ? '/dashboard' : '/movimientos';
  }

  private leerUsuario(): Usuario | null {
    try {
      const guardado = localStorage.getItem(CLAVE_USUARIO);
      return guardado && localStorage.getItem(CLAVE_TOKEN) ? (JSON.parse(guardado) as Usuario) : null;
    } catch {
      return null;
    }
  }
}
