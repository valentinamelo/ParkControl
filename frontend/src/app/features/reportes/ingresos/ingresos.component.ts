import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';

import { ApiService } from '../../../core/api.service';
import { mensajeError } from '../../../core/errores';
import { pesos } from '../../../core/formato';
import { FiltrosReporte, METODOS_PAGO, MetodoPago, ReporteIngresos, TipoVehiculo, Usuario } from '../../../core/models';
import { BarrasComponent } from '../../../shared/graficos/barras.component';
import { ColumnasComponent } from '../../../shared/graficos/columnas.component';
import { StatCardComponent } from '../../../shared/stat-card/stat-card.component';

/** "2026-11-23" en la zona horaria del navegador. */
function iso(fecha: Date): string {
  return new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

function rango(nombre: 'hoy' | 'semana' | 'mes' | 'mes-anterior'): { desde: string; hasta: string } {
  const hoy = new Date();
  switch (nombre) {
    case 'hoy':
      return { desde: iso(hoy), hasta: iso(hoy) };
    case 'semana':
      return { desde: iso(new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() - 6)), hasta: iso(hoy) };
    case 'mes':
      return { desde: iso(new Date(hoy.getFullYear(), hoy.getMonth(), 1)), hasta: iso(hoy) };
    case 'mes-anterior':
      return {
        desde: iso(new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1)),
        hasta: iso(new Date(hoy.getFullYear(), hoy.getMonth(), 0)),
      };
  }
}

/** RF-21 y RF-22: ingresos por rango de fechas, tipo de vehículo, método de pago y trabajador. */
@Component({
  selector: 'app-reporte-ingresos',
  imports: [DatePipe, ReactiveFormsModule, StatCardComponent, BarrasComponent, ColumnasComponent],
  templateUrl: './ingresos.component.html',
  styles: `
    .filtros { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0 14px; align-items: end; }
    .rapidos { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
    .grid-desgloses { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px; margin-bottom: 24px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
    .grid-3 > *, .grid-desgloses > * { min-width: 0; }
    td.valor, th.valor { text-align: right; }
    @media (max-width: 800px) { .grid-3 { grid-template-columns: 1fr; } }
  `,
})
export class IngresosComponent implements OnInit {
  private api = inject(ApiService);

  protected tipos = signal<TipoVehiculo[]>([]);
  protected usuarios = signal<Usuario[]>([]);
  protected reporte = signal<ReporteIngresos | null>(null);
  protected cargando = signal(false);
  protected descargando = signal<'pdf' | 'xlsx' | null>(null);
  protected error = signal('');
  protected rangoActivo = signal<string>('semana');
  protected metodos = METODOS_PAGO;
  protected pesos = pesos;
  protected rapidos = [
    { clave: 'hoy', texto: 'Hoy' },
    { clave: 'semana', texto: 'Últimos 7 días' },
    { clave: 'mes', texto: 'Este mes' },
    { clave: 'mes-anterior', texto: 'Mes anterior' },
  ] as const;

  protected form = inject(FormBuilder).nonNullable.group({
    ...rango('semana'),
    tipo: [null as number | null],
    metodo: ['' as MetodoPago | ''],
    usuario: [null as number | null],
    concepto: ['' as FiltrosReporte['concepto']],
  });

  ngOnInit(): void {
    this.api.tiposVehiculo().subscribe((t) => this.tipos.set(t));
    this.api.usuarios().subscribe((u) => this.usuarios.set(u));
    this.consultar();
  }

  usarRango(clave: (typeof this.rapidos)[number]['clave']): void {
    this.rangoActivo.set(clave);
    this.form.patchValue(rango(clave));
    this.consultar();
  }

  consultar(): void {
    this.cargando.set(true);
    this.error.set('');
    this.api.reporteIngresos(this.form.getRawValue()).subscribe({
      next: (r) => {
        this.reporte.set(r);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.error.set(mensajeError(e));
        this.cargando.set(false);
      },
    });
  }

  /** Cambió una fecha a mano: ya no corresponde a ningún rango rápido. */
  fechaManual(): void {
    this.rangoActivo.set('');
  }

  descargar(formato: 'pdf' | 'xlsx'): void {
    const filtros = this.form.getRawValue();
    this.descargando.set(formato);
    this.api.descargarReporte(filtros, formato).subscribe({
      next: (archivo) => {
        this.descargando.set(null);
        const url = URL.createObjectURL(archivo);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `ingresos_${filtros.desde}_${filtros.hasta}.${formato}`;
        enlace.click();
        URL.revokeObjectURL(url);
      },
      error: async (e: HttpErrorResponse) => {
        this.descargando.set(null);
        // El error llega como Blob porque se pidió un archivo
        const texto = e.error instanceof Blob ? await e.error.text() : '';
        try {
          this.error.set(JSON.parse(texto).detail ?? mensajeError(e));
        } catch {
          this.error.set(mensajeError(e));
        }
      },
    });
  }

  protected promedio(r: ReporteIngresos): number {
    return r.cantidad ? Math.round(r.total / r.cantidad) : 0;
  }
}
