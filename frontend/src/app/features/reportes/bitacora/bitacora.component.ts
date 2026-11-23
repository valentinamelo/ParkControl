import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';

import { ApiService } from '../../../core/api.service';
import { mensajeError } from '../../../core/errores';
import { RegistroBitacora, Usuario } from '../../../core/models';

const POR_PAGINA = 50;

/** "CREAR_TIPO_VEHICULO" -> "Crear tipo vehiculo" */
export function accionLegible(accion: string): string {
  const texto = accion.toLowerCase().replace(/_/g, ' ');
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** RF-23: quién registró cada entrada, salida, anulación y cambio de configuración. */
@Component({
  selector: 'app-bitacora',
  imports: [DatePipe, ReactiveFormsModule],
  templateUrl: './bitacora.component.html',
  styles: `
    .filtros { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0 14px; align-items: end; }
    .accion { font-family: ui-monospace, monospace; font-size: 0.78rem; }
    .paginas { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
    td { vertical-align: top; }
  `,
})
export class BitacoraComponent implements OnInit {
  private api = inject(ApiService);

  protected registros = signal<RegistroBitacora[]>([]);
  protected total = signal(0);
  protected pagina = signal(1);
  protected acciones = signal<string[]>([]);
  protected usuarios = signal<Usuario[]>([]);
  protected cargando = signal(false);
  protected error = signal('');
  protected paginas = computed(() => Math.max(1, Math.ceil(this.total() / POR_PAGINA)));
  protected accionLegible = accionLegible;

  protected form = inject(FormBuilder).nonNullable.group({
    desde: [''],
    hasta: [''],
    usuario: [null as number | null],
    accion: [''],
    q: [''],
  });

  ngOnInit(): void {
    this.api.accionesBitacora().subscribe((a) => this.acciones.set(a));
    this.api.usuarios().subscribe((u) => this.usuarios.set(u));
    this.buscar();
  }

  buscar(pagina = 1): void {
    this.cargando.set(true);
    this.error.set('');
    this.api.bitacora({ ...this.form.getRawValue(), page: pagina }).subscribe({
      next: (r) => {
        this.registros.set(r.results);
        this.total.set(r.count);
        this.pagina.set(pagina);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.error.set(mensajeError(e));
        this.cargando.set(false);
      },
    });
  }

  limpiar(): void {
    this.form.reset();
    this.buscar();
  }
}
