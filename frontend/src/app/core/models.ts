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
