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
  segundos: number;
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
  /** Valor de la primera hora; las siguientes se cobran con `valor`. null: todas valen lo mismo. */
  valor_primera_hora: string | null;
  minutos_fraccion: number;
  minutos_gracia: number;
  tope_diario: string | null;
  /** Por cada noche que el vehículo pasa dentro con el parqueadero cerrado. null: sin pernoctación. */
  valor_pernoctacion: string | null;
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
  espacios_ocupados: number;
  espacios_inactivos: number;
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
  /** Tiempo total dentro del parqueadero */
  segundos: number;
  /** Minutos completos (segundos // 60) */
  minutos: number;
  /** Minutos que se cobran por horas: con pernoctación, solo los del horario de atención */
  minutos_cobrados: number;
  noches: number;
  valor_tiempo: number;
  valor_noches: number;
  valor_pernoctacion: number | null;
  tarifa: string | null;
  sin_tarifa: boolean;
  /** valor_tiempo + valor_noches */
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
  /** Abierto: tiempo que lleva dentro. Cerrado: tiempo cobrado. */
  segundos_transcurridos: number | null;
  valor: string | null;
  multa: string;
  noches: number;
  estado: 'ABIERTO' | 'CERRADO' | 'ANULADO';
  estado_display: string;
  es_mensualidad: boolean;
  usuario_entrada: string;
  usuario_salida: string | null;
  metodo_pago: string | null;
  motivo_anulacion: string;
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

/** Total y cantidad de pagos de un grupo (método, tipo, trabajador...). */
export interface GrupoIngresos {
  nombre: string;
  total: number;
  cantidad: number;
}

export interface IngresoDia {
  fecha: string;
  total: number;
  cantidad: number;
}

export interface DashboardResumen {
  /** "turno" para el trabajador: solo lo que él registró hoy. */
  alcance: 'parqueadero' | 'turno';
  fecha: string;
  espacios: {
    total: number;
    ocupados: number;
    disponibles: number;
    inactivos: number;
    ocupacion: number;
    por_tipo: { tipo: string; total: number; ocupados: number; disponibles: number }[];
  };
  hoy: {
    ingresos: number;
    pagos: number;
    por_metodo: GrupoIngresos[];
    por_concepto: GrupoIngresos[];
    entradas: number;
    salidas: number;
  };
  /** Solo para el administrador */
  semana?: IngresoDia[];
  mensualidades?: { vigentes: number; por_vencer: number };
}

export interface FiltrosReporte {
  desde: string;
  hasta: string;
  tipo?: number | null;
  metodo?: MetodoPago | '';
  usuario?: number | null;
  concepto?: 'PARQUEO' | 'MENSUALIDAD' | '';
}

export interface FilaReporte {
  fecha: string;
  concepto: string;
  referencia: string;
  placa: string;
  tipo_vehiculo: string;
  metodo: string;
  usuario: string;
  valor: number;
}

export interface ReporteIngresos {
  desde: string;
  hasta: string;
  total: number;
  cantidad: number;
  por_dia: IngresoDia[];
  por_tipo: GrupoIngresos[];
  por_metodo: GrupoIngresos[];
  por_usuario: GrupoIngresos[];
  por_concepto: GrupoIngresos[];
  detalle: FilaReporte[];
}

export interface RegistroBitacora {
  id: number;
  fecha: string;
  usuario: number;
  usuario_nombre: string;
  usuario_rol: string;
  accion: string;
  detalle: string;
}

export interface Pagina<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
