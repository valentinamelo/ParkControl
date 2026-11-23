import { expect, test } from '@playwright/test';

import { ADMIN, TRABAJADOR, iniciarSesion } from './utilidades';

test.describe('Login y permisos por rol (RF-01, RF-02, sección 2)', () => {
  test('el administrador entra al dashboard y ve todo el menú', async ({ page }) => {
    await iniciarSesion(page, ADMIN);
    await expect(page).toHaveURL(/dashboard/);
    const menu = page.locator('aside nav');
    for (const opcion of ['Dashboard', 'Movimientos', 'Espacios', 'Vehículos', 'Mensualidades', 'Reportes', 'Configuración']) {
      await expect(menu.getByRole('link', { name: opcion })).toBeVisible();
    }
    await expect(page.getByText('Ingresos de hoy')).toBeVisible();
  });

  test('el trabajador entra a movimientos y no ve lo del administrador', async ({ page }) => {
    await iniciarSesion(page, TRABAJADOR);
    await expect(page).toHaveURL(/movimientos/);
    const menu = page.locator('aside nav');
    await expect(menu.getByRole('link', { name: 'Reportes' })).toHaveCount(0);
    await expect(menu.getByRole('link', { name: 'Configuración' })).toHaveCount(0);

    // Aunque escriba la ruta, el guard lo devuelve a su inicio
    for (const ruta of ['/reportes/ingresos', '/configuracion/usuarios']) {
      await page.goto(ruta);
      await expect(page).toHaveURL(/movimientos/);
    }

    // En el dashboard ve solo su turno
    await page.goto('/dashboard');
    await expect(page.getByText('Ingresos de tu turno')).toBeVisible();
  });

  test('credenciales incorrectas y cierre de sesión', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill(ADMIN.email);
    await page.getByLabel('Contraseña').fill('equivocada');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page.getByText('Correo o contraseña incorrectos.')).toBeVisible();

    await iniciarSesion(page, ADMIN);
    await page.getByRole('button', { name: 'Cerrar sesión' }).click();
    await expect(page).toHaveURL(/login/);
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/);
  });
});
