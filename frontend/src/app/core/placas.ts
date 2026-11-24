/** "abc-123" -> "ABC123" */
export function normalizarPlaca(texto: string): string {
  return texto.toUpperCase().replace(/[\s-]/g, '');
}

/**
 * Tipo de vehículo según el formato de la placa colombiana:
 * carro ABC123 (3 letras y 3 números), moto ABC12D (3 letras, 2 números y 1 letra).
 * Otras placas (diplomáticas, antiguas, de remolque) devuelven null y el tipo se elige a mano.
 */
export function tipoPorPlaca(placa: string): 'Carro' | 'Moto' | null {
  const p = normalizarPlaca(placa);
  if (/^[A-Z]{3}\d{3}$/.test(p)) return 'Carro';
  if (/^[A-Z]{3}\d{2}[A-Z]$/.test(p)) return 'Moto';
  return null;
}
