import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  Cliente,
  ConsultaPlaca,
  DashboardResumen,
  FiltrosReporte,
  Pagina,
  RegistroBitacora,
  ReporteIngresos,
  EntradaForm,
  Espacio,
  Horario,
  Mensualidad,
  MetodoPago,
  Parqueadero,
  PlanMensual,
  Tarifa,
  Tiquete,
  TipoVehiculo,
  Usuario,
  UsuarioForm,
  Vehiculo,
  VentaMensualidad,
  Zona,
} from './models';

export interface FiltrosBitacora {
  desde?: string;
  hasta?: string;
  usuario?: number | null;
  accion?: string;
  q?: string;
  page?: number;
}

/** Filtros -> query string, omitiendo los vacíos. */
function parametros(filtros: object): HttpParams {
  let params = new HttpParams();
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== null && valor !== undefined && valor !== '') params = params.set(clave, String(valor));
  }
  return params;
}

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

  /** Espacios libres para un tipo de vehículo; los fijos de otras mensualidades no aparecen. */
  espaciosDisponibles(tipo: string, placa = ''): Observable<Espacio[]> {
    let params = new HttpParams().set('tipo', tipo);
    if (placa) params = params.set('placa', placa);
    return this.http.get<Espacio[]>(`${this.url}/espacios/disponibles/`, { params });
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

  // --- Tiquetes (entrada, salida, cobro) ---

  consultarPlaca(placa: string): Observable<ConsultaPlaca> {
    return this.http.get<ConsultaPlaca>(`${this.url}/tiquetes/consultar-placa/`, { params: { placa } });
  }

  registrarEntrada(datos: EntradaForm): Observable<Tiquete> {
    return this.http.post<Tiquete>(`${this.url}/tiquetes/entrada/`, datos);
  }

  /** Datos del tiquete; si está abierto incluye el cobro calculado al momento. */
  tiquete(codigo: string, perdido = false): Observable<Tiquete> {
    const params = perdido ? new HttpParams().set('perdido', '1') : undefined;
    return this.http.get<Tiquete>(`${this.url}/tiquetes/${encodeURIComponent(codigo)}/`, { params });
  }

  registrarSalida(codigo: string, datos: { metodo?: MetodoPago; tiquete_perdido?: boolean }): Observable<Tiquete> {
    return this.http.post<Tiquete>(`${this.url}/tiquetes/${encodeURIComponent(codigo)}/salida/`, datos);
  }

  tiquetesActivos(placa = ''): Observable<Tiquete[]> {
    const params = placa ? new HttpParams().set('placa', placa) : undefined;
    return this.http.get<Tiquete[]>(`${this.url}/tiquetes/activos/`, { params });
  }

  /** Últimos 100 tiquetes, opcionalmente filtrados. */
  tiquetes(filtros: { estado?: string; placa?: string } = {}): Observable<Tiquete[]> {
    let params = new HttpParams();
    if (filtros.estado) params = params.set('estado', filtros.estado);
    if (filtros.placa) params = params.set('placa', filtros.placa);
    return this.http.get<Tiquete[]>(`${this.url}/tiquetes/`, { params });
  }

  // --- Clientes y mensualidades ---

  clientePorDocumento(documento: string): Observable<Cliente[]> {
    return this.http.get<Cliente[]>(`${this.url}/clientes/`, { params: { documento } });
  }

  planesMensuales(soloActivos = false): Observable<PlanMensual[]> {
    const params = soloActivos ? new HttpParams().set('activos', '1') : undefined;
    return this.http.get<PlanMensual[]>(`${this.url}/planes-mensuales/`, { params });
  }

  crearPlan(datos: Partial<PlanMensual>): Observable<PlanMensual> {
    return this.http.post<PlanMensual>(`${this.url}/planes-mensuales/`, datos);
  }

  actualizarPlan(id: number, datos: Partial<PlanMensual>): Observable<PlanMensual> {
    return this.http.patch<PlanMensual>(`${this.url}/planes-mensuales/${id}/`, datos);
  }

  /** Si el plan ya se vendió, el backend lo desactiva en lugar de borrarlo. */
  eliminarPlan(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/planes-mensuales/${id}/`);
  }

  mensualidades(filtros: { estado?: string; q?: string } = {}): Observable<Mensualidad[]> {
    let params = new HttpParams();
    if (filtros.estado) params = params.set('estado', filtros.estado);
    if (filtros.q) params = params.set('q', filtros.q);
    return this.http.get<Mensualidad[]>(`${this.url}/mensualidades/`, { params });
  }

  venderMensualidad(datos: VentaMensualidad): Observable<Mensualidad> {
    return this.http.post<Mensualidad>(`${this.url}/mensualidades/`, datos);
  }

  renovarMensualidad(id: number, metodo: MetodoPago): Observable<Mensualidad> {
    return this.http.post<Mensualidad>(`${this.url}/mensualidades/${id}/renovar/`, { metodo });
  }

  /** Solo admin. Si el tiquete estaba abierto libera el espacio; si estaba cerrado, su pago deja de contar. */
  anularTiquete(codigo: string, motivo: string): Observable<Tiquete> {
    return this.http.post<Tiquete>(`${this.url}/tiquetes/${encodeURIComponent(codigo)}/anular/`, { motivo });
  }

  // --- Dashboard, reportes y bitácora ---

  dashboard(): Observable<DashboardResumen> {
    return this.http.get<DashboardResumen>(`${this.url}/dashboard/resumen/`);
  }

  reporteIngresos(filtros: FiltrosReporte): Observable<ReporteIngresos> {
    return this.http.get<ReporteIngresos>(`${this.url}/reportes/ingresos/`, { params: parametros(filtros) });
  }

  /** PDF o Excel. Se pide como archivo (blob) para que el interceptor agregue el token. */
  descargarReporte(filtros: FiltrosReporte, formato: 'pdf' | 'xlsx'): Observable<Blob> {
    const params = parametros(filtros).set('formato', formato);
    return this.http.get(`${this.url}/reportes/ingresos/`, { params, responseType: 'blob' });
  }

  bitacora(filtros: FiltrosBitacora): Observable<Pagina<RegistroBitacora>> {
    return this.http.get<Pagina<RegistroBitacora>>(`${this.url}/bitacora/`, { params: parametros(filtros) });
  }

  accionesBitacora(): Observable<string[]> {
    return this.http.get<string[]>(`${this.url}/bitacora/acciones/`);
  }
}
