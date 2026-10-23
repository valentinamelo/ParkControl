import { Component, OnInit, inject, signal } from '@angular/core';

import { ApiService } from '../../core/api.service';
import { pesos } from '../../core/formato';
import { Horario, Parqueadero, Tarifa } from '../../core/models';

/** Pantalla solo para el administrador. En el avance 1 muestra la configuración actual. */
@Component({
  selector: 'app-configuracion',
  templateUrl: './configuracion.component.html',
})
export class ConfiguracionComponent implements OnInit {
  private api = inject(ApiService);

  protected parqueadero = signal<Parqueadero | null>(null);
  protected tarifas = signal<Tarifa[]>([]);
  protected horarios = signal<Horario[]>([]);
  protected pesos = pesos;

  ngOnInit(): void {
    this.api.parqueadero().subscribe((p) => this.parqueadero.set(p));
    this.api.tarifas().subscribe((t) => this.tarifas.set(t));
    this.api.horarios().subscribe((h) => this.horarios.set(h));
  }

  hora(valor: string): string {
    return valor.slice(0, 5);
  }
}
