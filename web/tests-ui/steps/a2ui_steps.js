import { createBdd } from 'playwright-bdd';
import { expect } from '@playwright/test';

const { Given, When, Then } = createBdd();

/**
 * Utility to inject A2UI components and verify they are rendered,
 * with retries to handle React state update lag.
 */
async function robustInject(page, components, expectedSelector) {
  await page.waitForFunction(() => window.A2UI_READY === true);
  
  for (let i = 0; i < 3; i++) {
    await page.evaluate((comps) => {
      window.dispatchEvent(new CustomEvent('test-inject-a2ui', {
        detail: [{
          type: 'updateComponents',
          surfaceId: 'main',
          components: comps
        }]
      }));
    }, components);

    try {
      await page.waitForSelector(expectedSelector, { timeout: 1500 });
      return; // Success
    } catch (e) {
      // Retry
    }
  }
  throw new Error(`Failed to render ${expectedSelector} after injection retries.`);
}

Given('que el agente tiene activado el soporte A2UI', async ({ page }) => {
  // Configuración inicial asumida
});

Given('estoy en la interfaz web de Luppita', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
});

When('el agente envía un componente de tipo {string} con estado {string}', async ({ page }, type, status) => {
  await robustInject(page, [{
    id: 'test-alert',
    type: type,
    properties: {
      title: 'Pago Atrasado Crítico',
      description: 'La unidad 402 tiene 5 días de mora.',
      status: status,
      actions: ['Enviar Recordatorio', 'Ver Detalles']
    }
  }], '.a2ui-alert-card');
});

Then('debería ver una tarjeta con un borde lateral rojo', async ({ page }) => {
  const alertCard = page.locator('.a2ui-alert-card--CRITICO');
  await expect(alertCard).toBeVisible();
  const borderColor = await alertCard.evaluate(el => 
    window.getComputedStyle(el, ':before').backgroundColor
  );
  expect(borderColor).toBe('rgb(239, 68, 68)');
});

Then('el título de la alerta debería ser visible', async ({ page }) => {
  await expect(page.locator('.a2ui-alert-card__title')).toBeVisible();
});

Then('las acciones de la alerta deberían estar disponibles como botones', async ({ page }) => {
  await expect(page.locator('.a2ui-alert-card__actions .a2ui-button')).toHaveCount(2);
});

// MaintenanceCard
When('el agente envía un componente de tipo "MaintenanceCard"', async ({ page }) => {
  await robustInject(page, [{
    id: 'test-maint',
    type: 'MaintenanceCard',
    properties: {
      title: 'Fuga de agua',
      unit: '402',
      status: 'PENDIENTE',
      priority: 'ALTA',
      contractor: 'Plomería Mario',
      aiDiagnosis: 'Posible rotura de tubería tras el muro.'
    }
  }], '.a2ui-maintenance-card');
});

Then('debería ver el estado del ticket y su prioridad', async ({ page }) => {
  await expect(page.locator('.a2ui-badge:has-text("PENDIENTE")')).toBeVisible();
  await expect(page.locator('.a2ui-badge:has-text("ALTA")')).toBeVisible();
});

Then('debería aparecer una sección de "IA Diagnosis" con fondo azulado y texto en cursiva', async ({ page }) => {
  const aiSection = page.locator('.a2ui-maintenance-ai');
  await expect(aiSection).toBeVisible();
  await expect(aiSection).toHaveCSS('font-style', 'italic');
});

Then('el nombre del contratista asignado debería ser visible', async ({ page }) => {
  await expect(page.getByText('Contractor: Plomería Mario')).toBeVisible();
});

// LeaseCard
When('el agente envía un componente de tipo "LeaseCard"', async ({ page }) => {
  await robustInject(page, [{
    id: 'test-lease',
    type: 'LeaseCard',
    properties: {
      tenant: 'Julian Thorne',
      property: 'Apartamento 501',
      rent: '$2.500.000',
      endDate: 'Oct 2026',
      daysRemaining: 180,
      progress: 60
    }
  }], '.a2ui-lease-card');
});

Then('debería ver el nombre del inquilino y la propiedad', async ({ page }) => {
  await expect(page.locator('.a2ui-card__title:has-text("Julian Thorne")')).toBeVisible();
  await expect(page.locator('.a2ui-card__subtitle:has-text("Apartamento 501")')).toBeVisible();
});

Then('debería aparecer una barra de progreso que indica los días restantes', async ({ page }) => {
  await expect(page.locator('.a2ui-lease-progress-bar')).toBeVisible();
  await expect(page.getByText('180 days left')).toBeVisible();
});

Then('el monto de la renta mensual debería ser visible', async ({ page }) => {
  await expect(page.getByText('Rent: $2.500.000')).toBeVisible();
});

// FinancialSnapshot
When('el agente envía un componente de tipo "FinancialSnapshot"', async ({ page }) => {
  await robustInject(page, [{
    id: 'test-finance',
    type: 'FinancialSnapshot',
    properties: {
      collected: 124500,
      outstanding: 12400,
      currency: '$'
    }
  }], '.a2ui-financial-snapshot');
});

Then('debería ver un panel con un degradado profundo', async ({ page }) => {
  const panel = page.locator('.a2ui-financial-snapshot');
  await expect(panel).toBeVisible();
  await expect(panel).toHaveCSS('background-image', /linear-gradient/);
});

Then('las métricas de "Total Recaudado" y "Saldo Pendiente" deberían destacar en blanco y oro', async ({ page }) => {
  await expect(page.locator('.positive:has-text("$124,500")')).toBeVisible();
  const outstanding = page.locator('.highlight:has-text("$12,400")');
  await expect(outstanding).toBeVisible();
  await expect(outstanding).toHaveCSS('color', 'rgb(212, 175, 55)');
});

Then('el botón para generar reporte financiero debería estar presente', async ({ page }) => {
  await expect(page.getByRole('button', { name: 'Generate Financial Report' })).toBeVisible();
});

// TaxEstimate
When('el agente envía un componente de tipo "TaxEstimate"', async ({ page }) => {
  await robustInject(page, [{
    id: 'test-tax',
    type: 'TaxEstimate',
    properties: {
      estimate: '$8,400',
      year: '2026',
      status: 'OK',
      documents: ['Recibo Predial 2025', 'Declaración Renta']
    }
  }], '.a2ui-tax-estimate');
});

Then('debería ver la estimación anual con un gráfico circular de color oro', async ({ page }) => {
  const chart = page.locator('.a2ui-tax-chart-placeholder');
  await expect(chart).toBeVisible();
  await expect(chart).toHaveText('$8,400');
  await expect(chart).toHaveCSS('border-color', /rgb\(212, 175, 55\)/);
});

Then('debería aparecer una lista de documentos en la "Bóveda de Documentos"', async ({ page }) => {
  await expect(page.getByText('Documents Vault')).toBeVisible();
  await expect(page.locator('.a2ui-list li')).toHaveCount(2);
});

Then('debería ver el estado de cumplimiento normativo', async ({ page }) => {
  await expect(page.getByText('Compliance Status')).toBeVisible();
  await expect(page.locator('.a2ui-badge--green:has-text("OK")')).toBeVisible();
});
