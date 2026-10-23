import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

/** Contenedor de la configuración (solo administrador): pestañas con una ruta hija cada una. */
@Component({
  selector: 'app-configuracion',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './configuracion.component.html',
  styles: `
    .pestanas { display: flex; gap: 4px; margin-bottom: 24px; border-bottom: 1px solid var(--linea); overflow-x: auto; }
    .pestanas a { padding: 10px 16px; font-size: 0.9rem; color: var(--texto-suave); border-bottom: 3px solid transparent; margin-bottom: -1px; white-space: nowrap; }
    .pestanas a:hover { color: var(--negro); }
    .pestanas a.activa { color: var(--negro); font-weight: 600; border-bottom-color: var(--amarillo); }
    .pestanas i { margin-right: 6px; }
  `,
})
export class ConfiguracionComponent {
  protected pestanas = [
    { ruta: 'tarifas', texto: 'Tarifas', icono: 'fa-tags' },
    { ruta: 'horarios', texto: 'Horarios', icono: 'fa-clock' },
    { ruta: 'usuarios', texto: 'Usuarios', icono: 'fa-users' },
    { ruta: 'parqueadero', texto: 'Parqueadero', icono: 'fa-building' },
  ];
}
