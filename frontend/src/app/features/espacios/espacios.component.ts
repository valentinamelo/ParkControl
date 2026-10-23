import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { erroresDeCampo, mensajeError } from '../../core/errores';
import { duracion } from '../../core/formato';
import { Espacio, TipoVehiculo, Zona } from '../../core/models';
import { ModalComponent } from '../../shared/modal/modal.component';

interface GrupoZona {
  zona: string;
  tipo: string;
  espacios: Espacio[];
}

@Component({
  selector: 'app-espacios',
  imports: [DatePipe, ReactiveFormsModule, ModalComponent],
  templateUrl: './espacios.component.html',
  styleUrl: './espacios.component.css',
})
export class EspaciosComponent implements OnInit {
  private api = inject(ApiService);
  protected auth = inject(AuthService);

  protected espacios = signal<Espacio[]>([]);
  protected seleccionado = signal<Espacio | null>(null);
  protected error = signal('');
  protected aviso = signal('');
  protected duracion = duracion;

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
        grupos.set(e.zona_nombre, { zona: e.zona_nombre, tipo: e.tipo_vehiculo, espacios: [] });
      }
      grupos.get(e.zona_nombre)!.espacios.push(e);
    }
    return [...grupos.values()];
  });

  ngOnInit(): void {
    this.cargar();
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
          this.aviso.set(`Se crearon ${creados.length} espacios: ${creados[0].codigo} a ${creados[creados.length - 1].codigo}.`);
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

  eliminarZona(zona: Zona): void {
    if (!confirm(`¿Eliminar la zona ${zona.nombre}?`)) return;
    this.ejecutar(this.api.eliminarZona(zona.id), `Zona ${zona.nombre} eliminada.`);
  }

  /** Corre una acción del administrador, muestra el resultado y recarga el mapa. */
  private ejecutar(peticion: Observable<unknown>, exito: string): void {
    this.error.set('');
    this.aviso.set('');
    peticion.subscribe({
      next: () => {
        this.aviso.set(exito);
        this.cargar();
      },
      error: (e: HttpErrorResponse) => {
        this.error.set(mensajeError(e));
        this.cargar();  // por si el select quedó con un valor que no se guardó
      },
    });
  }
}
