import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Espacio, Horario, Parqueadero, Tarifa, TipoVehiculo, Usuario, UsuarioForm, Vehiculo, Zona } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private url = environment.apiUrl;

  // --- Espacios y zonas ---

  espacios(filtros: { estado?: string; tipo?: string } = {}): Observable<Espacio[]> {
    let params = new HttpParams();
    if (filtros.estado) params = params.set('estado', filtros.estado);
    if (filtros.tipo) params = params.set('tipo', filtros.tipo);
    return this.http.get<Espacio[]>(`${this.url}/espacios/`, { params });
  }

  /** Crea varios espacios seguidos; si la zona no existe se crea con el tipo indicado. */
  crearEspaciosEnLote(datos: { zona: string; tipo_vehiculo?: number; cantidad: number }): Observable<Espacio[]> {
    return this.http.post<Espacio[]>(`${this.url}/espacios/lote/`, datos);
  }

  actualizarEspacio(id: number, datos: Partial<Pick<Espacio, 'codigo' | 'zona' | 'estado'>>): Observable<Espacio> {
    return this.http.patch<Espacio>(`${this.url}/espacios/${id}/`, datos);
  }

  eliminarEspacio(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/espacios/${id}/`);
  }

  zonas(): Observable<Zona[]> {
    return this.http.get<Zona[]>(`${this.url}/zonas/`);
  }

  actualizarZona(id: number, datos: Partial<Pick<Zona, 'nombre' | 'tipo_vehiculo'>>): Observable<Zona> {
    return this.http.patch<Zona>(`${this.url}/zonas/${id}/`, datos);
  }

  eliminarZona(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/zonas/${id}/`);
  }

  // --- Vehículos ---

  vehiculos(placa = ''): Observable<Vehiculo[]> {
    const params = placa ? new HttpParams().set('placa', placa) : undefined;
    return this.http.get<Vehiculo[]>(`${this.url}/vehiculos/`, { params });
  }

  crearVehiculo(datos: Partial<Vehiculo>): Observable<Vehiculo> {
    return this.http.post<Vehiculo>(`${this.url}/vehiculos/`, datos);
  }

  actualizarVehiculo(id: number, datos: Partial<Vehiculo>): Observable<Vehiculo> {
    return this.http.patch<Vehiculo>(`${this.url}/vehiculos/${id}/`, datos);
  }

  eliminarVehiculo(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/vehiculos/${id}/`);
  }

  // --- Configuración ---

  tiposVehiculo(): Observable<TipoVehiculo[]> {
    return this.http.get<TipoVehiculo[]>(`${this.url}/tipos-vehiculo/`);
  }

  crearTipoVehiculo(nombre: string): Observable<TipoVehiculo> {
    return this.http.post<TipoVehiculo>(`${this.url}/tipos-vehiculo/`, { nombre });
  }

  eliminarTipoVehiculo(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/tipos-vehiculo/${id}/`);
  }

  /** Por defecto solo las vigentes; con historial también las anteriores. */
  tarifas(historial = false): Observable<Tarifa[]> {
    const params = historial ? new HttpParams().set('historial', '1') : undefined;
    return this.http.get<Tarifa[]>(`${this.url}/tarifas/`, { params });
  }

  crearTarifa(datos: Partial<Tarifa>): Observable<Tarifa> {
    return this.http.post<Tarifa>(`${this.url}/tarifas/`, datos);
  }

  /** El backend no modifica la tarifa: crea una nueva vigente y la anterior pasa al historial. */
  cambiarTarifa(id: number, datos: Partial<Tarifa>): Observable<Tarifa> {
    return this.http.patch<Tarifa>(`${this.url}/tarifas/${id}/`, datos);
  }

  horarios(): Observable<Horario[]> {
    return this.http.get<Horario[]>(`${this.url}/horarios/`);
  }

  actualizarHorario(id: number, datos: Partial<Horario>): Observable<Horario> {
    return this.http.patch<Horario>(`${this.url}/horarios/${id}/`, datos);
  }

  parqueadero(): Observable<Parqueadero> {
    return this.http.get<Parqueadero>(`${this.url}/parqueadero/`);
  }

  actualizarParqueadero(datos: Partial<Parqueadero>): Observable<Parqueadero> {
    return this.http.put<Parqueadero>(`${this.url}/parqueadero/`, datos);
  }

  // --- Usuarios (solo admin) ---

  usuarios(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(`${this.url}/usuarios/`);
  }

  crearUsuario(datos: UsuarioForm): Observable<Usuario> {
    return this.http.post<Usuario>(`${this.url}/usuarios/`, datos);
  }

  actualizarUsuario(id: number, datos: Partial<UsuarioForm>): Observable<Usuario> {
    return this.http.patch<Usuario>(`${this.url}/usuarios/${id}/`, datos);
  }

  /** El backend no borra al usuario, lo desactiva. */
  desactivarUsuario(id: number): Observable<Usuario> {
    return this.http.delete<Usuario>(`${this.url}/usuarios/${id}/`);
  }
}
