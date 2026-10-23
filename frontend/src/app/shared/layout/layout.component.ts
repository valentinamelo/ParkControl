import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { Rol } from '../../core/models';

interface ItemMenu {
  ruta: string;
  texto: string;
  icono: string;
  roles: Rol[];
}

const MENU: ItemMenu[] = [
  { ruta: '/dashboard', texto: 'Dashboard', icono: 'fa-gauge', roles: ['ADMIN', 'TRABAJADOR'] },
  { ruta: '/movimientos', texto: 'Movimientos', icono: 'fa-right-left', roles: ['ADMIN', 'TRABAJADOR'] },
  { ruta: '/espacios', texto: 'Espacios', icono: 'fa-square-parking', roles: ['ADMIN', 'TRABAJADOR'] },
  { ruta: '/vehiculos', texto: 'Vehículos', icono: 'fa-car', roles: ['ADMIN', 'TRABAJADOR'] },
  { ruta: '/configuracion', texto: 'Configuración', icono: 'fa-gear', roles: ['ADMIN'] },
];

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.css',
})
export class LayoutComponent {
  protected auth = inject(AuthService);

  /** El menú solo muestra las opciones permitidas para el rol del usuario. */
  protected menu = computed(() => {
    const rol = this.auth.usuario()?.rol;
    return MENU.filter((item) => rol && item.roles.includes(rol));
  });
}
