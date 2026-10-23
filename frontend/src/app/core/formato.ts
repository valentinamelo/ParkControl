/** "165" -> "2h 45m" */
export function duracion(minutos: number): string {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

/** "4000" -> "$4.000" */
export function pesos(valor: string | number | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—';
  return '$' + Number(valor).toLocaleString('es-CO', { maximumFractionDigits: 0 });
}
