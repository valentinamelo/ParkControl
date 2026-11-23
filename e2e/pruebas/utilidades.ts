import { Page, expect } from '@playwright/test';

export const ADMIN = { email: 'admin@parkcontrol.com', clave: 'Admin123*' };
export const TRABAJADOR = { email: 'trabajador@parkcontrol.com', clave: 'Trabajador123*' };

/** Placa aleatoria (tres letras y tres números) para que las pruebas no choquen entre corridas. */
export function placaAleatoria(): string {
  const letras = Array.from({ length: 3 }, () => String.fromCharCode(65 + Math.floor(Math.random() * 26))).join('');
  return letras + String(Math.floor(Math.random() * 900) + 100);
}

export async function iniciarSesion(page: Page, usuario: { email: string; clave: string }): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill(usuario.email);
  await page.getByLabel('Contraseña').fill(usuario.clave);
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await expect(page).not.toHaveURL(/login/);
}

/** Registra la entrada de un vehículo nuevo y devuelve el código del tiquete. */
export async function registrarEntrada(page: Page, placa: string, tipo = 'Carro'): Promise<string> {
  await page.goto('/movimientos/entrada');
  const campo = page.getByLabel('Placa');
  await expect(campo).toBeVisible();
  await campo.fill(placa);
  const tipoNuevo = page.getByLabel('Tipo de vehículo');
  const espacio = page.locator('.espacio.elegido');
  // Un vehículo nuevo pide el tipo; uno registrado o con mensualidad, no
  await expect(tipoNuevo.or(espacio).first()).toBeVisible();
  if (await tipoNuevo.isVisible()) await tipoNuevo.selectOption({ label: tipo });
  await expect(espacio).toBeVisible();
  await page.getByRole('button', { name: 'Registrar y generar tiquete' }).click();
  await expect(page).toHaveURL(/\/movimientos\/tiquete\/PC-\d{6}/);
  return page.url().match(/PC-\d{6}/)![0];
}
