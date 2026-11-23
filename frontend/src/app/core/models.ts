export type Rol = 'ADMIN' | 'TRABAJADOR';

export interface Usuario {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  nombre: string;
  rol: Rol;
  rol_display: string;
  is_active: boolean;
}

export interface LoginRespuesta {
  access: string;
  refresh: string;
  usuario: Usuario;
}

export interface Ocupante {
  tiquete: string;
  placa: string;
  tipo_vehiculo: string;
  fecha_entrada: string;
  minutos: number;
  es_mensualidad: boolean;
}

export interface Espacio {
  id: number;
  codigo: string;
  zona: number;
  zona_nombre: string;
  tipo_vehiculo: string;
  estado: 'DISPONIBLE' | 'OCUPADO' | 'INACTIVO';
  estado_display: string;
  ocupante: Ocupante | null;
}

export interface Vehiculo {
  id: number;
  placa: string;
  tipo_vehiculo: number;
  tipo_vehiculo_nombre: string;
  marca: string;
  modelo: string;
  color: string;
  cliente: number | null;
  cliente_nombre: string | null;
}

export interface Tarifa {
  id: number;
  tipo_vehiculo: number;
  tipo_vehiculo_nombre: string;
  modalidad: 'HORA' | 'FRACCION';
  modalidad_display: string;
  valor: string;
  minutos_fraccion: number;
  minutos_gracia: number;
  tope_diario: string | null;
  vigente: boolean;
  creada: string;
}

export interface Horario {
  id: number;
  dia_semana: number;
  dia: string;
  hora_apertura: string;
  hora_cierre: string;
  abierto: boolean;
}

export interface Parqueadero {
  id: number;
  nombre: string;
  nit: string;
  direccion: string;
  telefono: string;
  multa_tiquete_perdido: string;
}

export interface TipoVehiculo {
  id: number;
  nombre: string;
}

export interface Zona {
  id: number;
  nombre: string;
  tipo_vehiculo: number;
  tipo_vehiculo_nombre: string;
  total_espacios: number;
}

/** Datos que el administrador envía al crear o editar un usuario. */
export interface UsuarioForm {
  email: string;
  first_name: string;
  last_name: string;
  rol: Rol;
  is_active?: boolean;
  password?: string;
}

export type MetodoPago = 'EFECTIVO' | 'TARJETA' | 'TRANSFERENCIA';

export const METODOS_PAGO: { valor: MetodoPago; texto: string; icono: string }[] = [
  { valor: 'EFECTIVO', texto: 'Efectivo', icono: 'fa-money-bill-wave' },
  { valor: 'TARJETA', texto: 'Tarjeta', icono: 'fa-credit-card' },
  { valor: 'TRANSFERENCIA', texto: 'Transferencia', icono: 'fa-building-columns' },
];

/** Valor que se cobraría si el vehículo saliera ahora (lo calcula el backend). */
export interface Cobro {
  minutos: number;
  tarifa: string | null;
  sin_tarifa: boolean;
  valor: number;
  multa: number;
  total: number;
}

export interface Tiquete {
  id: number;
  codigo: string;
  placa: string;
  tipo_vehiculo: string;
  vehiculo_descripcion: string;
  espacio: string;
  fecha_entrada: string;
  fecha_salida: string | null;
  minutos: number | null;
  minutos_transcurridos: number | null;
  valor: string | null;
  multa: string;
  estado: 'ABIERTO' | 'CERRADO' | 'ANULADO';
  estado_display: string;
  es_mensualidad: boolean;
  usuario_entrada: string;
  usuario_salida: string | null;
  metodo_pago: string | null;
  /** Solo en tiquetes/activos/ */
  valor_actual?: number;
  /** Solo en tiquetes/{codigo}/ si está abierto */
  cobro?: Cobro;
}

export interface EntradaForm {
  placa: string;
  tipo_vehiculo?: number;
  espacio?: number;
  marca?: string;
  modelo?: string;
  color?: string;
  forzar?: boolean;
}

/** Lo que se sabe de una placa antes de registrar la entrada. */
export interface ConsultaPlaca {
  placa: string;
  vehiculo: {
    id: number;
    tipo_vehiculo: number;
    tipo_vehiculo_nombre: string;
    marca: string;
    modelo: string;
    color: string;
  } | null;
  tiquete_abierto: { codigo: string; espacio: string } | null;
  mensualidad: {
    id: number;
    cliente: string;
    fecha_fin: string;
    espacio_fijo: string | null;
    espacio_fijo_id: number | null;
  } | null;
}

export interface Cliente {
  id: number;
  nombre: string;
  documento: string;
  telefono: string;
  correo: string;
}

export interface PlanMensual {
  id: number;
  nombre: string;
  tipo_vehiculo: number;
  tipo_vehiculo_nombre: string;
  valor: string;
  dias: number;
  activo: boolean;
}

export interface Mensualidad {
  id: number;
  cliente: number;
  cliente_nombre: string;
  cliente_documento: string;
  cliente_telefono: string;
  vehiculo: number;
  placa: string;
  tipo_vehiculo: string;
  plan: number;
  plan_nombre: string;
  espacio_fijo: number | null;
  espacio_fijo_codigo: string | null;
  fecha_inicio: string;
  fecha_fin: string;
  estado: 'VIGENTE' | 'VENCIDA';
  estado_display: string;
  valor_pagado: number;
  dias_restantes: number;
}

export interface VentaMensualidad {
  documento: string;
  nombre: string;
  telefono: string;
  correo: string;
  placa: string;
  plan: number;
  espacio_fijo: number | null;
  fecha_inicio: string;
  metodo: MetodoPago;
}
