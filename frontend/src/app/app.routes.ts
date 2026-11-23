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
        path: 'movimientos/entrada',
        loadComponent: () =>
          import('./features/movimientos/entrada/entrada.component').then((m) => m.EntradaComponent),
      },
      {
        path: 'movimientos/salida',
        loadComponent: () => import('./features/movimientos/salida/salida.component').then((m) => m.SalidaComponent),
      },
      {
        path: 'movimientos/tiquete/:codigo',
        loadComponent: () =>
          import('./features/movimientos/tiquete/tiquete.component').then((m) => m.TiqueteComponent),
      },
      {
        path: 'mensualidades',
        loadComponent: () =>
          import('./features/mensualidades/mensualidades.component').then((m) => m.MensualidadesComponent),
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
        children: [
          {
            path: 'tarifas',
            loadComponent: () =>
              import('./features/configuracion/tarifas/tarifas.component').then((m) => m.TarifasComponent),
          },
          {
            path: 'horarios',
            loadComponent: () =>
              import('./features/configuracion/horarios/horarios.component').then((m) => m.HorariosComponent),
          },
          {
            path: 'usuarios',
            loadComponent: () =>
              import('./features/configuracion/usuarios/usuarios.component').then((m) => m.UsuariosComponent),
          },
          {
            path: 'parqueadero',
            loadComponent: () =>
              import('./features/configuracion/parqueadero/parqueadero.component').then((m) => m.ParqueaderoComponent),
          },
          {
            path: 'planes',
            loadComponent: () =>
              import('./features/configuracion/planes/planes.component').then((m) => m.PlanesComponent),
          },
          { path: '', pathMatch: 'full', redirectTo: 'tarifas' },
        ],
      },
      {
        path: 'reportes',
        canActivate: [rolGuard],
        data: { roles: ['ADMIN'] },
        loadComponent: () => import('./features/reportes/reportes.component').then((m) => m.ReportesComponent),
        children: [
          {
            path: 'ingresos',
            loadComponent: () =>
              import('./features/reportes/ingresos/ingresos.component').then((m) => m.IngresosComponent),
          },
          {
            path: 'bitacora',
            loadComponent: () =>
              import('./features/reportes/bitacora/bitacora.component').then((m) => m.BitacoraComponent),
          },
          { path: '', pathMatch: 'full', redirectTo: 'ingresos' },
        ],
      },
      // Al entrar a la raíz, cada rol va a su pantalla de inicio
      { path: '', pathMatch: 'full', redirectTo: () => inject(AuthService).rutaInicio() },
    ],
  },
  { path: '**', redirectTo: '' },
];
