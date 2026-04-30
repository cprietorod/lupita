# Plan de Implementación: Componentes A2UI para "The Obsidian Concierge"

## Background & Motivation
Se generaron en Stitch 5 pantallas funcionales para la aplicación Luppita (Alertas, Contratos, Mantenimiento, Pagos e Impuestos) utilizando el sistema de diseño "The Obsidian Concierge". Este sistema se caracteriza por un modo oscuro (background `#050505`), glassmorphism (fondos `#121212` con `backdrop-filter: blur(16px)`), bordes suaves (rounded-8) y una tipografía editorial con colores de acento índigo (`#4f46e5`) y oro (`#d4af37`). Para reflejar esta alta fidelidad directamente en el chat del agente, el uso de los componentes genéricos actuales (`Card`, `Table`) es insuficiente.

## Scope & Impact
La implementación afectará:
1.  **Frontend (React/CSS)**: Creación de nuevos componentes específicos y estilos globales en `web/src/`.
2.  **Backend (Python)**: Modificación del esquema A2UI en `luppita/ui_schema.py` para instruir al agente sobre los nuevos tipos.
3.  **Chat del Agente**: El agente comenzará a devolver estructuras de datos mucho más ricas para renderizar componentes como estados financieros o donas de impuestos.

## Proposed Solution
El enfoque elegido consiste en **crear nuevos componentes A2UI específicos** tanto en el esquema de backend como en el frontend de React.

### Nuevos Componentes A2UI a crear:
1.  `AlertCard`: Para notificaciones críticas (pagos atrasados, mantenimiento) con acciones contextuales.
2.  `MaintenanceCard`: Para tickets de reparación, incluyendo estado, prioridad, proveedor e IA de diagnóstico.
3.  `LeaseCard`: Para contratos activos, mostrando inquilino, renta mensual y barra de progreso de días restantes.
4.  `FinancialSnapshot`: Un "hero section" glassmórfico para resumir cobros del mes vs. saldos pendientes.
5.  `TaxEstimate`: Un componente visual (tipo dona o similar) para mostrar estimaciones de impuestos y bóveda de documentos.

## Alternatives Considered
-   **A. Reutilizar A2UI Actual**: (Rechazado) Estilar los componentes genéricos actuales. Habría sido más rápido, pero no permitiría la complejidad visual necesaria para elementos como el `FinancialSnapshot` o la barra de progreso en el `LeaseCard` sin hacer un "hack" en el JSON.
-   **B. Crear Nuevos Componentes**: (Elegido) Ofrece fidelidad completa a los diseños de Stitch.

## Implementation Steps

### Fase 1: Sistema de Diseño (CSS)
1.  Añadir variables CSS globales a `web/src/index.css` (colores base, primarios, bordes de cristal, sombras ambientales, blur).
2.  Definir clases utilitarias para `glassmorphism` y la regla "No-Line" requerida por el diseño.

### Fase 2: Desarrollo Frontend (React)
1.  Actualizar `web/src/A2UIRenderer.jsx` (o crear nuevos archivos si es necesario modularizar) para añadir los casos en el `switch(type)`:
    -   `AlertCard`, `MaintenanceCard`, `LeaseCard`, `FinancialSnapshot`, `TaxEstimate`.
2.  Implementar la estructura de HTML y clases CSS para cada uno, imitando fielmente el diseño "Obsidian Concierge" generado en Stitch.

### Fase 3: Actualización del Backend (Python)
1.  Editar `luppita/ui_schema.py` para incluir la documentación en texto claro (`build_a2ui_section`) de los nuevos componentes.
2.  Especificar las propiedades (`properties`) que el agente debe devolver para cada componente (ej. `properties: { "collectedThisMonth": 124500, "outstandingBalance": 12400 }` para `FinancialSnapshot`).

### Fase 4: Integración del Agente
1.  Asegurar que las herramientas en `luppita/tools/` devuelvan la metadata adecuada (fechas, balances, IDs de inquilinos) para que el agente pueda inyectarla al construir el bloque JSON A2UI.

## Verification
1.  Lanzar comandos de chat en el playground probando las diferentes intenciones (ej. "Muestra mis alertas", "Dame el resumen financiero", "Tickets de mantenimiento").
2.  Verificar que el JSON devuelto utilice los nuevos tipos (ej. `type: "FinancialSnapshot"`).
3.  Comprobar visualmente que el renderizado en el navegador web mantenga el estilo oscuro, el efecto blur de cristal y las tipografías deseadas sin errores de UI.

## Migration & Rollback
-   **Rollback**: Si los componentes específicos fallan al renderizar, se puede revertir `ui_schema.py` a la versión anterior que solo incluía `Card`, `Table`, `List`, etc., y restaurar la versión estable de `A2UIRenderer.jsx`.