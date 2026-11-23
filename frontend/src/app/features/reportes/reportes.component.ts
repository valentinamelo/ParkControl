import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

/** Reportes (solo administrador): ingresos y bitácora, cada uno en una ruta hija. */
@Component({
  selector: 'app-reportes',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="encabezado">
      <div>
        <h1>Reportes</h1>
        <p>Ingresos del parqueadero y registro de quién hizo cada acción.</p>
      </div>
      <span class="badge">Solo administrador</span>
    </header>
    <nav class="pestanas">
      <a routerLink="ingresos" routerLinkActive="activa"><i aria-hidden="true" class="fa-solid fa-chart-column"></i>Ingresos</a>
      <a routerLink="bitacora" routerLinkActive="activa"><i aria-hidden="true" class="fa-solid fa-clock-rotate-left"></i>Bitácora</a>
    </nav>
    <router-outlet />
  `,
})
export class ReportesComponent {}
