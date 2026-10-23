import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';
import { Rol } from './models';

/** Solo deja pasar a usuarios con sesión iniciada. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.autenticado() ? true : inject(Router).parseUrl('/login');
};

/** Para el login: si ya hay sesión, manda al inicio de su rol. */
export const invitadoGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.autenticado() ? inject(Router).parseUrl(auth.rutaInicio()) : true;
};

/** Restringe una ruta a los roles indicados en data.roles. */
export const rolGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const roles = (route.data['roles'] as Rol[] | undefined) ?? [];
  const rol = auth.usuario()?.rol;
  return rol && roles.includes(rol) ? true : inject(Router).parseUrl(auth.rutaInicio());
};
