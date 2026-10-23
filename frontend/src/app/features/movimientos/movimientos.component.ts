import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { ApiService } from '../../core/api.service';
import { duracion } from '../../core/formato';
import { Espacio } from '../../core/models';

@Component({
  selector: 'app-movimientos',
  imports: [DatePipe],
  templateUrl: './movimientos.component.html',
})
export class MovimientosComponent implements OnInit {
  private api = inject(ApiService);

  protected ocupados = signal<Espacio[]>([]);
  protected cargando = signal(true);
  protected error = signal('');
  protected duracion = duracion;
  protected disponibles = signal(0);

  protected total = computed(() => this.ocupados().length);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.api.espacios({ estado: 'OCUPADO' }).subscribe({
      next: (e) => {
        this.ocupados.set(e);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los movimientos.');
        this.cargando.set(false);
      },
    });
    this.api.espacios({ estado: 'DISPONIBLE' }).subscribe((e) => this.disponibles.set(e.length));
  }
}
