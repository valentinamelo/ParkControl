import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { duracion } from '../../core/formato';
import { Espacio } from '../../core/models';

interface GrupoZona {
  zona: string;
  tipo: string;
  espacios: Espacio[];
}

@Component({
  selector: 'app-espacios',
  imports: [DatePipe],
  templateUrl: './espacios.component.html',
  styleUrl: './espacios.component.css',
})
export class EspaciosComponent implements OnInit {
  private api = inject(ApiService);
  protected auth = inject(AuthService);

  protected espacios = signal<Espacio[]>([]);
  protected seleccionado = signal<Espacio | null>(null);
  protected error = signal('');
  protected duracion = duracion;

  /** Agrupa los espacios por zona para dibujar el mapa. */
  protected zonas = computed<GrupoZona[]>(() => {
    const grupos = new Map<string, GrupoZona>();
    for (const e of this.espacios()) {
      if (!grupos.has(e.zona_nombre)) {
        grupos.set(e.zona_nombre, { zona: e.zona_nombre, tipo: e.tipo_vehiculo, espacios: [] });
      }
      grupos.get(e.zona_nombre)!.espacios.push(e);
    }
    return [...grupos.values()];
  });

  ngOnInit(): void {
    this.api.espacios().subscribe({
      next: (e) => this.espacios.set(e),
      error: () => this.error.set('No se pudieron cargar los espacios.'),
    });
  }

  seleccionar(espacio: Espacio): void {
    this.seleccionado.set(espacio);
  }
}
