import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Espacio, Horario, Parqueadero, Tarifa, Vehiculo } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private url = environment.apiUrl;

  espacios(filtros: { estado?: string; tipo?: string } = {}): Observable<Espacio[]> {
    let params = new HttpParams();
    if (filtros.estado) params = params.set('estado', filtros.estado);
    if (filtros.tipo) params = params.set('tipo', filtros.tipo);
    return this.http.get<Espacio[]>(`${this.url}/espacios/`, { params });
  }

  vehiculos(placa = ''): Observable<Vehiculo[]> {
    const params = placa ? new HttpParams().set('placa', placa) : undefined;
    return this.http.get<Vehiculo[]>(`${this.url}/vehiculos/`, { params });
  }

  tarifas(): Observable<Tarifa[]> {
    return this.http.get<Tarifa[]>(`${this.url}/tarifas/`);
  }

  horarios(): Observable<Horario[]> {
    return this.http.get<Horario[]>(`${this.url}/horarios/`);
  }

  parqueadero(): Observable<Parqueadero> {
    return this.http.get<Parqueadero>(`${this.url}/parqueadero/`);
  }
}
