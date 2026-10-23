import { Component, OnInit, inject, signal } from '@angular/core';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { Vehiculo } from '../../core/models';

@Component({
  selector: 'app-vehiculos',
  templateUrl: './vehiculos.component.html',
})
export class VehiculosComponent implements OnInit {
  private api = inject(ApiService);
  private busqueda$ = new Subject<string>();

  protected vehiculos = signal<Vehiculo[]>([]);
  protected cargando = signal(true);
  protected error = signal('');

  ngOnInit(): void {
    // Busca en la API 300 ms después de que el usuario deja de escribir
    this.busqueda$
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap((placa) => {
          this.cargando.set(true);
          return this.api.vehiculos(placa.trim());
        }),
      )
      .subscribe({
        next: (v) => {
          this.vehiculos.set(v);
          this.cargando.set(false);
        },
        error: () => {
          this.error.set('No se pudieron cargar los vehículos.');
          this.cargando.set(false);
        },
      });
    this.busqueda$.next('');
  }

  buscar(texto: string): void {
    this.busqueda$.next(texto);
  }
}
