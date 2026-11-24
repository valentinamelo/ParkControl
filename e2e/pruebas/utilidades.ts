import { Page, expect } from '@playwright/test';

export const ADMIN = { email: 'admin@parkcontrol.com', clave: 'Admin123*' };
export const TRABAJADOR = { email: 'trabajador@parkcontrol.com', clave: 'Trabajador123*' };

function letras(n: number): string {
  return Array.from({ length: n }, () => String.fromCharCode(65 + Math.floor(Math.random() * 26))).join('');
}

/** Placa aleatoria para que las pruebas no choquen entre corridas: carro ABC123, moto ABC12D. */
export function placaAleatoria(tipo: 'Carro' | 'Moto' = 'Carro'): string {
  return tipo === 'Carro'
    ? letras(3) + String(Math.floor(Math.random() * 900) + 100)
    : letras(3) + String(Math.floor(Math.random() * 90) + 10) + letras(1);
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
  await expect(page).toHaveURL(/\/movimientos\/tiquete\/[CM]-[A-Z0-9]{8}\b/);
  return page.url().match(/[CM]-[A-Z0-9]{8}/)![0];
}

/** Da salida por la API a un vehículo que una prueba dejó dentro, para no ir llenando los espacios. */
export async function liberar(page: Page, codigo: string): Promise<void> {
  const token = await page.evaluate(() => localStorage.getItem('pc_access'));
  const respuesta = await page.request.post(`/api/tiquetes/${codigo}/salida/`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { metodo: 'EFECTIVO' },
  });
  expect(respuesta.ok()).toBeTruthy();
}
