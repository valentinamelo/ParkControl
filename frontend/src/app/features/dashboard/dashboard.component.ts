import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { duracion } from '../../core/formato';
import { Espacio } from '../../core/models';
import { StatCardComponent } from '../../shared/stat-card/stat-card.component';

@Component({
  selector: 'app-dashboard',
  imports: [DatePipe, RouterLink, StatCardComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  protected espacios = signal<Espacio[]>([]);
  protected totalVehiculos = signal(0);
  protected cargando = signal(true);
  protected error = signal('');
  protected duracion = duracion;

  // Indicadores calculados a partir de los espacios (los inactivos no cuentan)
  protected activos = computed(() => this.espacios().filter((e) => e.estado !== 'INACTIVO'));
  protected ocupados = computed(() => this.activos().filter((e) => e.estado === 'OCUPADO'));
  protected disponibles = computed(() => this.activos().filter((e) => e.estado === 'DISPONIBLE'));

  ngOnInit(): void {
    this.api.espacios().subscribe({
      next: (e) => {
        this.espacios.set(e);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los espacios.');
        this.cargando.set(false);
      },
    });
    this.api.vehiculos().subscribe((v) => this.totalVehiculos.set(v.length));
  }
}
