import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable, timer } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { erroresDeCampo, mensajeError } from '../../core/errores';
import { tiempo } from '../../core/formato';
import { NotificacionesService } from '../../core/notificaciones.service';
import { Espacio, TipoVehiculo, Zona } from '../../core/models';
import { ModalComponent } from '../../shared/modal/modal.component';
import { INTERVALO_ACTUALIZACION } from '../movimientos/movimientos.component';

interface GrupoZona {
  zona: string;
  tipo: string;
  espacios: Espacio[];
  /** Todos sus espacios están inactivos */
  inactiva: boolean;
}

@Component({
  selector: 'app-espacios',
  imports: [DatePipe, ReactiveFormsModule, ModalComponent],
  templateUrl: './espacios.component.html',
  styleUrl: './espacios.component.css',
})
export class EspaciosComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);
  private notificaciones = inject(NotificacionesService);
  protected auth = inject(AuthService);

  protected espacios = signal<Espacio[]>([]);
  protected seleccionado = signal<Espacio | null>(null);
  protected error = signal('');
  protected tiempo = tiempo;

  // Solo para el administrador
  protected listaZonas = signal<Zona[]>([]);
  protected tipos = signal<TipoVehiculo[]>([]);
  protected modalLote = signal(false);
  protected guardando = signal(false);
  protected errorLote = signal('');
  protected erroresLote = signal<Record<string, string>>({});
  protected formLote = inject(FormBuilder).nonNullable.group({
    zona: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9]{1,5}$/)]],
    tipo_vehiculo: [0],
    cantidad: [5, [Validators.required, Validators.min(1), Validators.max(100)]],
  });

  /** Agrupa los espacios por zona para dibujar el mapa. */
  protected zonas = computed<GrupoZona[]>(() => {
    const grupos = new Map<string, GrupoZona>();
    for (const e of this.espacios()) {
      if (!grupos.has(e.zona_nombre)) {
        grupos.set(e.zona_nombre, { zona: e.zona_nombre, tipo: e.tipo_vehiculo, espacios: [], inactiva: true });
      }
      const grupo = grupos.get(e.zona_nombre)!;
      grupo.espacios.push(e);
      grupo.inactiva &&= e.estado === 'INACTIVO';
    }
    return [...grupos.values()];
  });

  ngOnInit(): void {
    // El mapa se actualiza solo para ver las entradas y salidas de otros puestos
    timer(0, INTERVALO_ACTUALIZACION)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.cargar());
    if (this.auth.esAdmin()) {
      this.api.tiposVehiculo().subscribe((t) => this.tipos.set(t));
    }
  }

  cargar(): void {
    this.api.espacios().subscribe({
      next: (lista) => {
        this.espacios.set(lista);
        // Mantiene seleccionado el mismo espacio con sus datos nuevos
        const id = this.seleccionado()?.id;
        this.seleccionado.set(lista.find((e) => e.id === id) ?? null);
      },
      error: () => this.error.set('No se pudieron cargar los espacios.'),
    });
    if (this.auth.esAdmin()) {
      this.api.zonas().subscribe((z) => this.listaZonas.set(z));
    }
  }

  seleccionar(espacio: Espacio): void {
    this.seleccionado.set(espacio);
  }

  // --- Agregar espacios en lote (RF-04) ---

  abrirLote(): void {
    this.errorLote.set('');
    this.erroresLote.set({});
    this.formLote.reset({ zona: '', tipo_vehiculo: this.tipos()[0]?.id ?? 0, cantidad: 5 });
    this.modalLote.set(true);
  }

  /** La zona escrita en el formulario si ya existe (entonces su tipo no se elige). */
  protected zonaExistente(): Zona | undefined {
    const nombre = this.formLote.controls.zona.value.trim().toUpperCase();
    return this.listaZonas().find((z) => z.nombre === nombre);
  }

  crearLote(): void {
    if (this.formLote.invalid) {
      this.formLote.markAllAsTouched();
      return;
    }
    const { zona, tipo_vehiculo, cantidad } = this.formLote.getRawValue();
    this.guardando.set(true);
    this.api
      .crearEspaciosEnLote({ zona, cantidad, tipo_vehiculo: this.zonaExistente() ? undefined : tipo_vehiculo })
      .subscribe({
        next: (creados) => {
          this.guardando.set(false);
          this.modalLote.set(false);
          this.notificaciones.exito(
            `Se crearon ${creados.length} espacios: ${creados[0].codigo} a ${creados[creados.length - 1].codigo}.`,
          );
          this.cargar();
        },
        error: (e: HttpErrorResponse) => {
          this.guardando.set(false);
          this.erroresLote.set(erroresDeCampo(e));
          this.errorLote.set(mensajeError(e, false));
        },
      });
  }

  // --- Acciones sobre un espacio (RF-05) ---

  cambiarEstado(espacio: Espacio): void {
    const estado = espacio.estado === 'INACTIVO' ? 'DISPONIBLE' : 'INACTIVO';
    this.ejecutar(
      this.api.actualizarEspacio(espacio.id, { estado }),
      estado === 'INACTIVO' ? `Espacio ${espacio.codigo} desactivado.` : `Espacio ${espacio.codigo} activado.`,
    );
  }

  eliminar(espacio: Espacio): void {
    if (!confirm(`¿Eliminar el espacio ${espacio.codigo}? Si solo quieres dejar de usarlo, desactívalo.`)) return;
    this.ejecutar(this.api.eliminarEspacio(espacio.id), `Espacio ${espacio.codigo} eliminado.`);
  }

  // --- Zonas (RF-06: el tipo de vehículo de cada espacio es el de su zona) ---

  cambiarTipoZona(zona: Zona, tipoId: string): void {
    this.ejecutar(
      this.api.actualizarZona(zona.id, { tipo_vehiculo: Number(tipoId) }),
      `La zona ${zona.nombre} ahora es para ${this.tipos().find((t) => t.id === Number(tipoId))?.nombre}.`,
    );
  }

  /** Una zona está inactiva cuando todos sus espacios lo están. */
  protected zonaInactiva(zona: Zona): boolean {
    return zona.total_espacios > 0 && zona.espacios_inactivos === zona.total_espacios;
  }

  /** Activa o desactiva todos los espacios de la zona. El backend exige que estén libres. */
  cambiarEstadoZona(zona: Zona): void {
    if (this.zonaInactiva(zona)) {
      this.ejecutar(this.api.activarZona(zona.id), `Zona ${zona.nombre} activada: sus espacios vuelven a estar disponibles.`);
      return;
    }
    if (!confirm(`¿Desactivar la zona ${zona.nombre}? Sus ${zona.total_espacios} espacios dejarán de ofrecerse para nuevas entradas.`)) return;
    this.ejecutar(this.api.desactivarZona(zona.id), `Zona ${zona.nombre} desactivada.`);
  }

  eliminarZona(zona: Zona): void {
    const espacios = zona.total_espacios === 1 ? 'su espacio' : `sus ${zona.total_espacios} espacios`;
    const pregunta = zona.total_espacios ? `¿Eliminar la zona ${zona.nombre} y ${espacios}?` : `¿Eliminar la zona ${zona.nombre}?`;
    if (!confirm(`${pregunta} Si solo quieres dejar de usarla, desactívala.`)) return;
    if (this.seleccionado()?.zona === zona.id) this.seleccionado.set(null);
    this.ejecutar(this.api.eliminarZona(zona.id), `Zona ${zona.nombre} eliminada.`);
  }

  /** Corre una acción del administrador, muestra el resultado en una notificación y recarga el mapa. */
  private ejecutar(peticion: Observable<unknown>, exito: string): void {
    peticion.subscribe({
      next: () => {
        this.notificaciones.exito(exito);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => {
        this.notificaciones.error(mensajeError(e));
        this.cargar();  // por si el select quedó con un valor que no se guardó
      },
    });
  }
}
