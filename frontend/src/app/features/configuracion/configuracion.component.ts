import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

/** Contenedor de la configuración (solo administrador): pestañas con una ruta hija cada una. */
@Component({
  selector: 'app-configuracion',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './configuracion.component.html',
})
export class ConfiguracionComponent {
  protected pestanas = [
    { ruta: 'tarifas', texto: 'Tarifas', icono: 'fa-tags' },
    { ruta: 'planes', texto: 'Planes mensuales', icono: 'fa-id-card' },
    { ruta: 'horarios', texto: 'Horarios', icono: 'fa-clock' },
    { ruta: 'usuarios', texto: 'Usuarios', icono: 'fa-users' },
    { ruta: 'parqueadero', texto: 'Parqueadero', icono: 'fa-building' },
  ];
}
