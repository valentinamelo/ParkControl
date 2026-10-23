import { inject } from '@angular/core';
import { Routes } from '@angular/router';

import { AuthService } from './core/auth.service';
import { authGuard, invitadoGuard, rolGuard } from './core/guards';
import { LayoutComponent } from './shared/layout/layout.component';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [invitadoGuard],
    loadComponent: () => import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    component: LayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'movimientos',
        loadComponent: () =>
          import('./features/movimientos/movimientos.component').then((m) => m.MovimientosComponent),
      },
      {
        path: 'espacios',
        loadComponent: () => import('./features/espacios/espacios.component').then((m) => m.EspaciosComponent),
      },
      {
        path: 'vehiculos',
        loadComponent: () => import('./features/vehiculos/vehiculos.component').then((m) => m.VehiculosComponent),
      },
      {
        path: 'configuracion',
        canActivate: [rolGuard],
        data: { roles: ['ADMIN'] },
        loadComponent: () =>
          import('./features/configuracion/configuracion.component').then((m) => m.ConfiguracionComponent),
      },
      // Al entrar a la raíz, cada rol va a su pantalla de inicio
      { path: '', pathMatch: 'full', redirectTo: () => inject(AuthService).rutaInicio() },
    ],
  },
  { path: '**', redirectTo: '' },
];
