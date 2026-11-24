import { expect, test } from '@playwright/test';

import { ADMIN, TRABAJADOR, iniciarSesion, liberar, placaAleatoria, registrarEntrada } from './utilidades';

test.describe('Operación del parqueadero (avance 3)', () => {
  test('flujo completo: entrada, tiquete, salida con lector y pago', async ({ page }) => {
    await iniciarSesion(page, TRABAJADOR);
    const placa = placaAleatoria();
    const codigo = await registrarEntrada(page, placa);

    // Tiquete con código de barras listo para imprimir
    const papel = page.locator('.papel');
    await expect(papel.getByText(placa)).toBeVisible();
    await expect(papel.locator('app-codigo-barras svg rect').first()).toBeAttached();

    // Aparece entre los vehículos dentro
    await page.goto('/movimientos');
    await expect(page.getByRole('row', { name: new RegExp(placa) })).toBeVisible();

    // El lector USB escribe el código y envía Enter
    await page.goto('/movimientos/salida');
    const campo = page.getByLabel('Escanea el tiquete o digita el código');
    await expect(campo).toBeFocused();
    await page.keyboard.type(codigo);
    await page.keyboard.press('Enter');
    await expect(page.locator('.datos').getByText(placa)).toBeVisible();

    // Recién entró: sin cobro (dentro de la primera fracción solo si hay gracia) o con cobro y método
    const cobrar = page.getByRole('button', { name: /^(Cobrar .* y dar salida|Dar salida)$/ });
    if ((await cobrar.textContent())?.startsWith('Cobrar')) {
      await page.getByRole('radio', { name: 'Tarjeta' }).click();
    }
    await cobrar.click();
    // Vuelve a Movimientos con el resumen de la salida
    await expect(page).toHaveURL(/\/movimientos$/);
    await expect(page.locator('.exito')).toContainText(placa);
    await expect(page.locator('.exito')).toContainText(codigo);

    // El mismo tiquete ya no se puede cobrar otra vez
    await page.getByRole('link', { name: 'Registrar salida' }).click();
    await expect(campo).toBeFocused();
    await campo.fill(codigo);
    await campo.press('Enter');
    await expect(page.locator('.alerta')).toContainText('ya está cerrado');
  });

  test('el tipo se elige solo según la placa y el código lleva su prefijo', async ({ page }) => {
    await iniciarSesion(page, TRABAJADOR);
    for (const tipo of ['Carro', 'Moto'] as const) {
      await page.goto('/movimientos/entrada');
      await page.getByLabel('Placa').fill(placaAleatoria(tipo));
      const selector = page.getByLabel('Tipo de vehículo');
      await expect(selector.locator('option:checked')).toHaveText(tipo);
      await expect(page.getByText('Elegido por el formato de la placa')).toBeVisible();
      await page.getByRole('button', { name: 'Registrar y generar tiquete' }).click();
      await expect(page).toHaveURL(new RegExp(`/movimientos/tiquete/${tipo[0]}-[A-Z0-9]{8}`));
      await liberar(page, page.url().match(/[CM]-[A-Z0-9]{8}/)![0]);
    }
  });

  test('no se registra dos veces la misma placa', async ({ page }) => {
    await iniciarSesion(page, TRABAJADOR);
    const placa = placaAleatoria('Moto');
    const codigo = await registrarEntrada(page, placa, 'Moto');
    await page.goto('/movimientos/entrada');
    await page.getByLabel('Placa').fill(placa);
    await expect(page.locator('.alerta')).toContainText(codigo);
    await expect(page.getByRole('button', { name: 'Registrar y generar tiquete' })).toBeDisabled();
    await liberar(page, codigo);
  });

  test('tiquete perdido: se busca por placa y se suma la multa', async ({ page }) => {
    await iniciarSesion(page, TRABAJADOR);
    const placa = placaAleatoria();
    await registrarEntrada(page, placa);
    await page.goto('/movimientos/salida');
    const campo = page.getByLabel('Escanea el tiquete o digita el código');
    await campo.fill(placa);
    await campo.press('Enter');
    await expect(page.getByRole('checkbox', { name: /Tiquete perdido/ })).toBeChecked();
    await expect(page.locator('.cuenta')).toContainText('Multa por tiquete perdido');
    await page.getByRole('button', { name: /^Cobrar/ }).click();
    await expect(page).toHaveURL(/\/movimientos$/);
    await expect(page.locator('.exito')).toContainText(placa);
  });

  test('mensualidad: se vende, entra sin cobro y sale en $0', async ({ page }) => {
    await iniciarSesion(page, TRABAJADOR);
    const placa = placaAleatoria();
    await page.goto('/mensualidades');
    await page.getByRole('button', { name: 'Vender mensualidad' }).click();
    const modal = page.getByRole('dialog');
    await modal.getByLabel('Documento').fill(String(Date.now()).slice(-9));
    await modal.getByLabel('Nombre').fill('Cliente de prueba');
    await modal.getByLabel('Placa').fill(placa);
    await modal.getByLabel('Plan').selectOption({ label: 'Mensual carro · $180.000' });
    await modal.getByRole('button', { name: 'Cobrar y vender' }).click();
    await expect(page.locator('.exito')).toContainText(placa);

    const codigo = await registrarEntrada(page, placa);
    await expect(page.locator('.papel')).toContainText('Sí, sin cobro');

    await page.goto(`/movimientos/salida?codigo=${codigo}`);
    await expect(page.getByText('Mensualidad vigente: no se cobra el tiempo.')).toBeVisible();
    await page.getByRole('button', { name: 'Dar salida' }).click();
    await expect(page).toHaveURL(/\/movimientos$/);
    await expect(page.locator('.exito')).toContainText('mensualidad, sin cobro');
  });
});

test.describe('Administración (avances 2 y 4)', () => {
  test('el administrador anula un tiquete con motivo y queda en la bitácora', async ({ page }) => {
    await iniciarSesion(page, ADMIN);
    const placa = placaAleatoria();
    const codigo = await registrarEntrada(page, placa);

    await page.getByRole('button', { name: 'Anular' }).click();
    const modal = page.getByRole('dialog');
    const anular = modal.getByRole('button', { name: 'Anular tiquete' });
    await expect(anular).toBeDisabled(); // sin motivo no se puede
    await modal.getByLabel('Motivo (obligatorio)').fill('Prueba e2e: placa equivocada');
    await anular.click();
    await expect(page.locator('.exito', { hasText: 'anulado' })).toContainText('quedó libre');
    await expect(page.locator('.alerta')).toContainText('Prueba e2e: placa equivocada');

    await page.goto('/reportes/bitacora');
    await page.getByLabel('Detalle contiene').fill(codigo);
    const respuesta = page.waitForResponse((r) => r.url().includes(`q=${codigo}`));
    await page.getByRole('button', { name: 'Buscar' }).click();
    await respuesta;
    await expect(page.getByRole('heading', { name: /Registros \(2\)/ })).toBeVisible(); // la entrada y la anulación
    await expect(page.getByRole('row', { name: /Anular tiquete/ })).toContainText('placa equivocada');
  });

  test('configura la pernoctación de la tarifa de carro', async ({ page }) => {
    await iniciarSesion(page, ADMIN);
    await page.goto('/configuracion/tarifas');
    await page.getByRole('row', { name: /Carro/ }).getByRole('button', { name: 'Cambiar' }).click();
    const modal = page.getByRole('dialog');
    await modal.getByLabel('Pernoctación ($ por noche, opcional)').fill('15000');
    await modal.getByRole('button', { name: 'Guardar tarifa' }).click();
    await expect(page.getByRole('row', { name: /Carro/ }).first()).toContainText('$15.000 / noche');
  });

  test('configura una primera hora con valor distinto y luego la quita', async ({ page }) => {
    await iniciarSesion(page, ADMIN);
    await page.goto('/configuracion/tarifas');
    const filaMoto = page.getByRole('row', { name: /Moto/ }).first();
    const cambiar = async (primeraHora: string) => {
      await filaMoto.getByRole('button', { name: 'Cambiar' }).click();
      const modal = page.getByRole('dialog');
      await modal.getByLabel('Valor primera hora ($, opcional)').fill(primeraHora);
      await modal.locator('#valor').fill('2000');
      await modal.getByRole('button', { name: 'Guardar tarifa' }).click();
      await expect(modal).toBeHidden();
    };
    await cambiar('3000');
    await expect(filaMoto).toContainText('$3.000 primera hora, luego $2.000 / 60 min');
    await cambiar(''); // se deja como estaba para las demás pruebas
    await expect(filaMoto).not.toContainText('primera hora');
  });

  test('crea espacios en lote en una zona nueva', async ({ page }) => {
    await iniciarSesion(page, ADMIN);
    await page.goto('/espacios');
    const zona = 'Z' + Math.floor(Math.random() * 900 + 100);
    await page.getByRole('button', { name: 'Agregar espacios' }).click();
    const modal = page.getByRole('dialog');
    await modal.getByLabel('Zona', { exact: true }).fill(zona);
    await modal.getByLabel('Cantidad').fill('3');
    await modal.getByLabel('Tipo de vehículo de la zona nueva').selectOption({ label: 'Moto' });
    await modal.getByRole('button', { name: 'Crear espacios' }).click();
    await expect(page.locator('.exito')).toContainText(`${zona}-01 a ${zona}-03`);
    await expect(page.getByRole('heading', { name: new RegExp(`Zona ${zona}`) })).toBeVisible();
  });

  test('desactiva, activa y elimina una zona libre; una zona con vehículos no se elimina', async ({ page }) => {
    await iniciarSesion(page, ADMIN);
    page.on('dialog', (d) => d.accept()); // confirmaciones
    await page.goto('/espacios');
    const zona = 'Y' + Math.floor(Math.random() * 900 + 100);
    await page.getByRole('button', { name: 'Agregar espacios' }).click();
    const modal = page.getByRole('dialog');
    await modal.getByLabel('Zona', { exact: true }).fill(zona);
    await modal.getByLabel('Cantidad').fill('2');
    await modal.getByRole('button', { name: 'Crear espacios' }).click();
    const titulo = page.getByRole('heading', { name: new RegExp(`Zona ${zona}`) });
    await expect(titulo).toBeVisible();

    await page.getByRole('button', { name: `Desactivar zona ${zona}` }).click();
    await expect(page.locator('.exito')).toContainText(`Zona ${zona} desactivada`);
    await expect(titulo).toContainText('Inactiva');

    await page.getByRole('button', { name: `Activar zona ${zona}` }).click();
    await expect(page.locator('.exito')).toContainText(`Zona ${zona} activada`);
    await expect(titulo).not.toContainText('Inactiva');

    await page.getByRole('button', { name: `Eliminar zona ${zona}` }).click();
    await expect(page.locator('.exito')).toContainText(`Zona ${zona} eliminada`);
    await expect(titulo).toBeHidden();

    // La zona A siempre tiene un vehículo dentro en los datos iniciales (ABC123 en A-02)
    await expect(page.getByRole('button', { name: 'Eliminar zona A', exact: true })).toBeDisabled();
  });
});
