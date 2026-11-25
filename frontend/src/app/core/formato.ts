/** "165" -> "2h 45m" */
export function duracion(minutos: number): string {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

/** 9910 -> "2h 45m 10s", 303 -> "5m 3s", 40 -> "40s" */
export function tiempo(segundos: number): string {
  const h = Math.floor(segundos / 3600);
  const m = Math.floor((segundos % 3600) / 60);
  const s = segundos % 60;
  if (h) return `${h}h ${m}m ${s}s`;
  return m ? `${m}m ${s}s` : `${s}s`;
}

/** "4000" -> "$4.000" */
export function pesos(valor: string | number | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—';
  return '$' + Number(valor).toLocaleString('es-CO', { maximumFractionDigits: 0 });
}
