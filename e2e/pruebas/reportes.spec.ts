import { expect, test } from '@playwright/test';

import { ADMIN, iniciarSesion } from './utilidades';

test.describe('Dashboard y reportes (avance 4)', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, ADMIN);
  });

  test('dashboard con ocupación e ingresos reales', async ({ page }) => {
    await expect(page.getByText('Espacios totales')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Ocupación por tipo' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Ingresos de la semana' })).toBeVisible();
    await expect(page.getByRole('meter', { name: 'Ocupación de Carro' })).toBeVisible();
  });

  test('reporte de ingresos con filtros', async ({ page }) => {
    await page.goto('/reportes/ingresos');
    await expect(page.getByText('Total recaudado')).toBeVisible();
    await page.getByRole('button', { name: 'Este mes' }).click();
    await page.getByLabel('Concepto').selectOption({ label: 'Mensualidades' });
    const respuesta = page.waitForResponse((r) => r.url().includes('concepto=MENSUALIDAD'));
    await page.getByRole('button', { name: 'Consultar' }).click();
    await respuesta;
    // Con el filtro de mensualidades todo el detalle es de ese concepto
    const filas = page.locator('table tbody tr');
    await expect(filas.first()).toBeVisible();
    for (const fila of await filas.all()) {
      const texto = await fila.innerText();
      if (!texto.includes('No hay pagos')) expect(texto).toContain('Mensualidad');
    }
  });

  test('exporta el reporte a PDF y Excel', async ({ page }) => {
    await page.goto('/reportes/ingresos');
    await expect(page.getByText('Total recaudado')).toBeVisible();
    for (const [boton, extension] of [['PDF', 'pdf'], ['Excel', 'xlsx']] as const) {
      const descarga = page.waitForEvent('download');
      await page.getByRole('button', { name: boton, exact: true }).click();
      const archivo = await descarga;
      expect(archivo.suggestedFilename()).toMatch(new RegExp(`^ingresos_\\d{4}-\\d{2}-\\d{2}_\\d{4}-\\d{2}-\\d{2}\\.${extension}$`));
    }
  });
});

test.describe('Diseño responsive (computador y tablet)', () => {
  for (const [nombre, ancho] of [['tablet', 768], ['celular', 400]] as const) {
    test(`ninguna pantalla se desborda a lo ancho en ${nombre}`, async ({ page }) => {
      await page.setViewportSize({ width: ancho, height: 1000 });
      await iniciarSesion(page, ADMIN);
      for (const ruta of ['/dashboard', '/movimientos', '/movimientos/entrada', '/movimientos/salida', '/espacios',
        '/vehiculos', '/mensualidades', '/reportes/ingresos', '/reportes/bitacora', '/configuracion/tarifas']) {
        await page.goto(ruta);
        await page.waitForLoadState('networkidle');
        const desborde = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        expect(desborde, `${ruta} se desborda ${desborde}px`).toBeLessThanOrEqual(1);
      }
    });
  }
});
