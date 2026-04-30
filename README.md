# Luppita

Agente de IA para la gestión de apartamentos arrendados en Colombia. Construido con Python, [Google ADK](https://google.github.io/adk-docs/) y Gemini 2.5 Flash, con Google Sheets como base de datos y un frontend React con componentes visuales adaptativos (A2UI).

Luppita responde preguntas en lenguaje natural como:
- "¿Qué arrendatarios no han pagado este mes?"
- "¿Hay contratos que vencen en los próximos 3 meses?"
- "¿Cuándo debo pagar el predial?"
- "¿Cuáles son los arreglos pendientes en el apto 101?"

---

## Arquitectura

```
┌─────────────────────┐     HTTP/SSE      ┌──────────────────────┐
│   Frontend React    │ ────────────────► │  FastAPI + ADK       │
│   (Vite · port 5173)│                   │  (Python · port 8001)│
│   A2UI Renderer     │ ◄──────────────── │  Agente Luppita      │
└─────────────────────┘    JSON + A2UI    └──────────┬───────────┘
                                                     │ google-api-python-client
                                                     ▼
                                          ┌──────────────────────┐
                                          │   Google Sheets      │
                                          │   (base de datos)    │
                                          └──────────────────────┘
```

El agente usa **A2UI** — un protocolo de UI generativa donde el LLM produce bloques JSON que el frontend convierte en componentes visuales (tarjetas, tablas, snapshots financieros, etc.) en lugar de solo texto.

---

## Requisitos previos

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Cuenta de Google Cloud con Vertex AI habilitado
- Google Sheets con la estructura definida abajo

---

## Instalación

```bash
git clone <url-del-repo>
cd luppita_web
make install      # instala dependencias Python con uv
make ui-install   # instala dependencias del frontend
```

---

## Configuración de Google Sheets

### 1. Crear el Spreadsheet

Crea un nuevo Google Spreadsheet con **7 pestañas** con exactamente estos nombres y encabezados:

#### `apartamentos`
```
apartamento_id | nombre | direccion | ciudad | area_m2 | estrato | matricula_inmobiliaria | valor_catastral | notas
```

#### `contratos`
```
contrato_id | apartamento_id | inquilino_id | fecha_inicio | fecha_fin | canon_mensual | dia_pago | deposito | estado | notas
```
- `estado`: `VIGENTE` / `TERMINADO` / `CANCELADO`

#### `inquilinos`
```
inquilino_id | nombre | cedula | telefono | email | notas
```

#### `pagos`
```
pago_id | contrato_id | apartamento_id | periodo | fecha_pago | monto_esperado | monto_pagado | diferencia | metodo_pago | comprobante | estado | notas
```
- `estado`: `PAGADO` / `PENDIENTE` / `PARCIAL` / `MORA`
- `periodo`: formato `YYYY-MM` (ej: `2026-04`)

#### `reparaciones`
```
rep_id | apartamento_id | fecha_reporte | fecha_resolucion | categoria | descripcion | contratista | costo | estado | prioridad | notas
```
- `categoria`: `plomeria` / `electrico` / `pintura` / `estructura` / `electrodomestico` / `otro`
- `prioridad`: `BAJA` / `MEDIA` / `ALTA`
- `estado`: `PENDIENTE` / `EN PROGRESO` / `COMPLETADO`

#### `impuestos`
```
evento_id | ano_gravable | impuesto | descripcion | fecha_vencimiento | descuento_disponible | aplica_a | estado | monto_pagado | notas
```
- `estado`: `PENDIENTE` / `PAGADO` / `PRESENTADO`
- `aplica_a`: `todos` o el `apartamento_id` específico

#### `config`
```
clave | valor
```
Agrega estas filas con los valores del año en curso:

| clave | valor |
|---|---|
| `ipc_2026` | `5.47` |
| `uvt_2026` | `49799` |
| `umbral_alerta_contratos_dias` | `90` |
| `umbral_mora_alta_dias` | `30` |
| `ciudad_default` | `Bogota` |

> Actualiza `ipc_YYYY` cada enero con el valor certificado por el DANE.

### 2. Poblar impuestos

Agrega las fechas clave del año. Ejemplo para 2026 en Bogotá:

| evento_id | impuesto | descripcion | fecha_vencimiento | descuento_disponible | estado |
|---|---|---|---|---|---|
| TAX-2026-001 | predial | Predial Bogotá - descuento pronto pago | 2026-04-17 | 10% | PENDIENTE |
| TAX-2026-002 | predial | Predial Bogotá - fecha límite | 2026-07-10 | Sin descuento | PENDIENTE |
| TAX-2026-003 | renta_natural | Declaración renta personas naturales | 2026-08-12 | N/A | PENDIENTE |

---

## Configuración de Google Cloud

### 3. Habilitar APIs

En [Google Cloud Console](https://console.cloud.google.com/):
1. Habilita **Vertex AI API**
2. Habilita **Google Sheets API**
3. Habilita **Google Drive API**

### 4. Crear Service Account

```bash
make auth GCP_PROJECT=tu-proyecto-id
```

Esto crea la Service Account y descarga la llave en `credentials/luppita-sa.json`.

> Alternativamente, créala manualmente en *IAM & Admin → Service Accounts → Crear → Agregar clave → JSON* y guárdala en `credentials/`.

### 5. Compartir el Spreadsheet

Abre el JSON descargado, copia el campo `client_email` y comparte el spreadsheet con ese email con permiso de **Editor**.

---

## Variables de entorno

```bash
make env   # crea .env desde .env.example
```

Edita `.env` con tus valores:

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=tu-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=credentials/luppita-sa.json
SPREADSHEET_ID=tu-spreadsheet-id-aqui
LUPPITA_OWNER_NAME=Tu Nombre
```

El ID del spreadsheet está en su URL:
```
https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
```

---

## Ejecutar en desarrollo

Levanta el backend y el frontend en terminales separadas:

```bash
# Terminal 1 — API backend
make server

# Terminal 2 — Frontend React
make ui
```

Abre `http://localhost:5173` en el navegador.

### Modo web ADK (alternativo)

```bash
make web   # localhost:8000, interfaz ADK nativa
```

### Modo CLI

```bash
make cli
```

---

## Comandos Make

| Comando | Descripción |
|---|---|
| `make install` | Instala dependencias Python con uv |
| `make ui-install` | Instala dependencias del frontend |
| `make server` | Backend ADK + FastAPI (`localhost:8001`) |
| `make ui` | Frontend React (`localhost:5173`) |
| `make web` | Interfaz web ADK (`localhost:8000`) |
| `make cli` | Luppita en línea de comandos |
| `make test` | Tests unitarios con pytest |
| `make test-ui` | Tests de UI con Playwright + Gherkin |
| `make lint` | Verifica código con ruff |
| `make format` | Formatea código con ruff |
| `make check` | Verifica conexión al agente y a Sheets |
| `make env` | Crea `.env` desde `.env.example` |
| `make auth GCP_PROJECT=...` | Crea Service Account y descarga llave |
| `make ui-prod VITE_API_URL=...` | Frontend apuntando a backend en producción |

---

## Herramientas del agente

| Dominio | Herramienta | Descripción |
|---|---|---|
| Contratos | `get_all_contracts` | Lista contratos por estado |
| Contratos | `get_expiring_contracts` | Contratos que vencen en N días |
| Contratos | `get_contract_by_apartment` | Contrato activo de un apartamento |
| Contratos | `get_tenant_info` | Busca arrendatario por nombre |
| Contratos | `add_contract` | Registra un nuevo contrato |
| Contratos | `update_contract_status` | Actualiza estado de un contrato |
| Pagos | `get_unpaid_this_month` | Aptos sin pago en el mes actual |
| Pagos | `get_payment_history` | Historial de pagos por apartamento |
| Pagos | `get_tenants_in_arrears` | Arrendatarios en mora |
| Pagos | `register_payment` | Registra un pago recibido |
| Pagos | `get_monthly_income_summary` | Resumen esperado vs recibido |
| Pagos | `calculate_rent_increase` | Calcula nuevo canon con IPC |
| Mantenimiento | `get_pending_maintenance` | Lista mantenimientos pendientes |
| Mantenimiento | `log_maintenance` | Registra un arreglo o solicitud |
| Mantenimiento | `resolve_maintenance` | Marca mantenimiento como resuelto |
| Mantenimiento | `get_maintenance_cost_summary` | Costos de mantenimiento por año |
| Impuestos | `get_upcoming_tax_deadlines` | Vencimientos tributarios próximos |
| Impuestos | `get_tax_calendar` | Calendario tributario del año |
| Impuestos | `mark_tax_paid` | Marca un impuesto como pagado |
| Impuestos | `get_predial_info` | Info predial con descuentos |
| Dashboard | `get_full_dashboard` | Resumen ejecutivo de todas las propiedades |
| Dashboard | `get_apartment_status` | Estado completo de un apartamento |

---

## A2UI — Componentes visuales

Cuando el agente detecta que la respuesta se beneficia de una visualización, emite componentes A2UI en lugar de solo texto. El frontend los renderiza automáticamente.

| Componente | Uso |
|---|---|
| `AlertCard` | Notificaciones críticas con semáforo (CRITICO / ALERTA / OK) |
| `FinancialSnapshot` | Resumen financiero mensual con métricas destacadas |
| `LeaseCard` | Estado de contrato con barra de progreso |
| `MaintenanceCard` | Ticket de mantenimiento con diagnóstico IA |
| `TaxEstimate` | Estimación tributaria con estado de cumplimiento |
| `Card` | Tarjeta genérica con semáforo de estado |
| `Table` | Tabla de datos |
| `List` | Lista de ítems |
| `Heading` | Encabezado de sección |

---

## Estructura del proyecto

```
luppita_web/
├── Makefile
├── Dockerfile                     # Imagen backend (Cloud Run)
├── pyproject.toml                 # Dependencias Python (uv)
├── .env.example                   # Plantilla de variables de entorno
├── .gitignore
│
├── luppita/                       # Agente principal
│   ├── agent.py                   # Definición del agente y prompt
│   ├── sheets.py                  # Lectura/escritura en Google Sheets
│   ├── ui_schema.py               # Prompt de A2UI para el agente
│   ├── fast_api_app.py            # App FastAPI (modo prod/Cloud Run)
│   ├── app_utils/
│   │   ├── telemetry.py           # OpenTelemetry + Cloud Trace
│   │   └── typing.py              # Tipos Pydantic compartidos
│   └── tools/
│       ├── contracts.py           # Herramientas de contratos
│       ├── payments.py            # Herramientas de pagos
│       ├── maintenance.py         # Herramientas de mantenimiento
│       ├── taxes.py               # Herramientas tributarias
│       └── alerts.py              # Dashboard y alertas
│
├── web/                           # Frontend React
│   ├── Dockerfile                 # Imagen frontend (nginx, Cloud Run)
│   ├── src/
│   │   ├── App.jsx                # Aplicación principal + chat
│   │   ├── A2UIRenderer.jsx       # Renderer de componentes A2UI
│   │   ├── App.css                # Estilos (tema Obsidian Concierge)
│   │   └── index.css              # Variables CSS y reset
│   ├── tests-ui/
│   │   ├── features/              # Escenarios Gherkin (.feature)
│   │   └── steps/                 # Step definitions (Playwright)
│   └── playwright.config.js
│
├── tests/                         # Tests Python
│   ├── unit/
│   ├── integration/
│   └── eval/                      # Evaluaciones ADK
│
├── conductor/                     # Guías del proyecto
│   ├── product.md
│   ├── tech-stack.md
│   ├── workflow.md
│   └── code_styleguides/
│
└── credentials/                   # Excluido de git
    └── luppita-sa.json
```

---

## Despliegue en Cloud Run

El proyecto incluye Dockerfiles para el backend y el frontend, listos para desplegar en Google Cloud Run.

```bash
# Build y push del backend
gcloud builds submit --tag gcr.io/TU_PROYECTO/luppita-api

# Build y push del frontend
cd web
gcloud builds submit --tag gcr.io/TU_PROYECTO/luppita-web \
  --build-arg VITE_API_URL=https://tu-api-url.run.app
```

Las variables de entorno sensibles (`SPREADSHEET_ID`, `LUPPITA_OWNER_NAME`) se configuran como secrets en Cloud Run — nunca en el Dockerfile ni en el código.

---

## Marco legal incluido

El agente tiene integrado conocimiento de la **Ley 820 de 2003** (arrendamiento residencial en Colombia):
- Responsabilidad de reparaciones (propietario vs. inquilino)
- Límites de depósito (máximo 2 cánones)
- Incremento de canon (máximo IPC del año anterior, una vez por año)
- Preaviso de terminación (3 meses)

Y del **Calendario Tributario colombiano**:
- Predial (Bogotá y Medellín)
- Renta personas naturales (DIAN)
- Retención en la fuente sobre arriendos (3.5% si el arrendatario es persona jurídica)

---

## Actualización anual

Cada enero actualiza en la pestaña `config` del spreadsheet:

- `ipc_YYYY` — IPC certificado por el DANE
- `uvt_YYYY` — Valor de la UVT publicado por la DIAN

Y agrega las nuevas filas de impuestos en la pestaña `impuestos` con las fechas del año tributario entrante.
