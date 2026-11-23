import { defineConfig, devices } from '@playwright/test';

/**
 * Las pruebas corren contra la app ya levantada (por defecto el stack de Docker en el puerto 8080):
 *
 *   docker compose up -d --build
 *   cd e2e && npm install && npx playwright install chromium && npm test
 *
 * Para otra URL: PARKCONTROL_URL=https://parkcontrol.onrender.com npm test
 */
export default defineConfig({
  testDir: './pruebas',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.PARKCONTROL_URL ?? 'http://localhost:8080',
    locale: 'es-CO',
    timezoneId: 'America/Bogota',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'escritorio',
      use: {
        ...devices['Desktop Chrome'],
        // Permite usar un Chrome/Brave ya instalado en lugar del que descarga Playwright
        launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
      },
    },
  ],
});
