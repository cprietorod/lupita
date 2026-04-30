# Luppita

Agente de IA para la gestión de apartamentos en arriendo en Colombia. Construido con Python y Google ADK (Agent Development Kit), con Google Sheets como base de datos.

Luppita responde preguntas en lenguaje natural como:
- "¿Qué arrendatarios no han pagado este mes?"
- "¿Hay contratos que vencen en los próximos 3 meses?"
- "¿Cuándo debo pagar el predial?"
- "¿Cuáles son los arreglos pendientes en el apto 101?"

---

## Requisitos previos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado
- Cuenta de Google (para Google Sheets y Google Cloud)
- API Key de Gemini (Google AI Studio)

---

## Instalación

### 1. Clonar e instalar dependencias

```bash
git clone <url-del-repo>
cd luppita_claude
make install
```

---

## Configuración de Google Sheets

### 2. Crear el Spreadsheet

Crea un nuevo Google Spreadsheet y agrégale **6 pestañas** con exactamente estos nombres y encabezados:

#### Pestaña `Apartamentos`
```
apartamento_id | nombre | direccion | ciudad | area_m2 | estrato | matricula_inmobiliaria | valor_catastral | notas
```

#### Pestaña `Contratos`
```
contrato_id | apartamento_id | nombre_arrendatario | cedula | telefono | email | fecha_inicio | fecha_fin | canon_mensual | incremento_anual_pct | dia_pago | deposito | estado | notas
```
- Campo `estado`: `activo` / `vencido` / `terminado`

#### Pestaña `Pagos`
```
pago_id | contrato_id | apartamento_id | periodo | fecha_pago | monto_esperado | monto_pagado | diferencia | metodo_pago | comprobante | estado | notas
```
- Campo `estado`: `pagado` / `pendiente` / `parcial` / `mora`
- Campo `periodo`: formato `YYYY-MM` (ej: `2026-04`)

#### Pestaña `Mantenimiento`
```
mant_id | apartamento_id | fecha_reporte | fecha_resolucion | categoria | descripcion | proveedor | costo | estado | prioridad | notas
```
- Campo `categoria`: `plomeria` / `electrico` / `pintura` / `estructura` / `electrodomestico` / `otro`
- Campo `prioridad`: `baja` / `media` / `alta` / `urgente`
- Campo `estado`: `pendiente` / `en_proceso` / `resuelto`

#### Pestaña `Calendario_Tributario`
```
evento_id | ano_gravable | impuesto | descripcion | fecha_vencimiento | descuento_disponible | aplica_a | estado | monto_pagado | notas
```
- Campo `estado`: `pendiente` / `pagado` / `presentado`
- Campo `aplica_a`: `todos` o el `apartamento_id` específico

#### Pestaña `Config`
```
clave | valor
```
Agrega estas filas con los valores del año en curso:

| clave | valor |
|-------|-------|
| `ipc_2026` | `9.28` |
| `uvt_2026` | `49799` |
| `ciudad_default` | `Bogota` |

> Actualiza el IPC cada enero con el valor certificado por el DANE.

### 3. Poblar el Calendario Tributario

Agrega las fechas clave para el año. Ejemplo para 2026 en Bogotá (persona natural):

| evento_id | ano_gravable | impuesto | descripcion | fecha_vencimiento | descuento_disponible | aplica_a | estado |
|-----------|-------------|----------|-------------|-------------------|----------------------|----------|--------|
| TAX-2026-001 | 2025 | predial | Predial Bogotá - con descuento | 2026-04-17 | 10% descuento pronto pago | todos | pendiente |
| TAX-2026-002 | 2025 | predial | Predial Bogotá - fecha límite | 2026-07-10 | Sin descuento | todos | pendiente |
| TAX-2026-003 | 2025 | renta_natural | Declaración renta personas naturales | 2026-08-12 | N/A | todos | pendiente |
| TAX-2026-004 | 2025 | retefuente | Retefuente enero 2026 | 2026-02-20 | N/A | todos | pendiente |
| TAX-2026-005 | 2025 | retefuente | Retefuente febrero 2026 | 2026-03-20 | N/A | todos | pendiente |
| TAX-2026-006 | 2025 | retefuente | Retefuente marzo 2026 | 2026-04-22 | N/A | todos | pendiente |

> Repite la fila de `retefuente` para cada mes del año ajustando la fecha de vencimiento.

---

## Configuración de Google Cloud (Service Account)

### 4. Crear Service Account

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Activa la **Google Sheets API**: *APIs & Services → Library → busca "Google Sheets API" → Habilitar*
4. Activa la **Google Drive API**: *APIs & Services → Library → busca "Google Drive API" → Habilitar*
5. Ve a *IAM & Admin → Service Accounts → Crear cuenta de servicio*
6. Asígnale cualquier nombre (ej: `luppita-sheets`)
7. En el paso de permisos, no es necesario agregar roles de proyecto
8. Una vez creada, haz clic en la cuenta → *Claves → Agregar clave → Crear clave nueva → JSON*
9. Descarga el archivo JSON y guárdalo en:

```
credentials/service_account.json
```

> El directorio `credentials/` está en `.gitignore`. Nunca lo subas al repositorio.

### 5. Compartir el Spreadsheet con la Service Account

1. Abre el archivo JSON descargado y copia el valor del campo `client_email`
   (tiene la forma `luppita-sheets@tu-proyecto.iam.gserviceaccount.com`)
2. Abre el Google Spreadsheet
3. Haz clic en **Compartir**
4. Pega el email de la service account y otórgale permiso de **Editor**
5. Desactiva la notificación por correo y confirma

---

## Configuración de variables de entorno

### 6. Obtener la API Key de Gemini

1. Ve a [Google AI Studio](https://aistudio.google.com/apikey)
2. Crea una nueva API Key
3. Copia el valor

### 7. Obtener el ID del Spreadsheet

El ID está en la URL del spreadsheet:
```
https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
```

### 8. Crear el archivo `.env`

```bash
make env
```

Edita `.env` con tus valores reales:

```env
GOOGLE_API_KEY=AIzaSy...tu_api_key_de_gemini
SPREADSHEET_ID=tu-spreadsheet-id-aqui
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
```

---

## Ejecutar Luppita

### Interfaz web (recomendado)

```bash
make web
```

Abre el navegador en `http://localhost:8000`, selecciona el agente `luppita` y empieza a chatear.

### Interfaz de línea de comandos

```bash
make cli
```

---

## Comandos Make

| Comando | Descripción |
|---------|-------------|
| `make install` | Instala dependencias con uv |
| `make web` | Lanza Luppita en interfaz web (`localhost:8000`) |
| `make cli` | Lanza Luppita en línea de comandos |
| `make env` | Crea `.env` desde `.env.example` |
| `make lint` | Verifica el código con ruff |
| `make format` | Formatea el código con ruff |
| `make test` | Corre los tests con pytest |
| `make check` | Verifica que las herramientas y Sheets cargan |

---

## Estructura del proyecto

```
luppita_claude/
├── pyproject.toml              # Dependencias (uv)
├── .env                        # Secrets (no se sube al repo)
├── .env.example                # Plantilla de variables de entorno
├── .gitignore
├── luppita/
│   ├── __init__.py             # Expone root_agent para ADK
│   ├── agent.py                # Definición del agente y prompt
│   ├── config.py               # Cliente gspread y variables de entorno
│   ├── sheets.py               # Primitivas de lectura/escritura en Sheets
│   └── tools/
│       ├── contracts.py        # Gestión de contratos (6 herramientas)
│       ├── payments.py         # Pagos de arriendo (6 herramientas)
│       ├── maintenance.py      # Mantenimiento (4 herramientas)
│       ├── taxes.py            # Calendario tributario (4 herramientas)
│       └── alerts.py           # Dashboard y alertas (2 herramientas)
└── credentials/
    └── service_account.json    # Service account de GCP (no se sube al repo)
```

---

## Herramientas disponibles

| Dominio | Herramienta | Descripción |
|---------|-------------|-------------|
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

## Verificar la instalación

```bash
make check
```

---

## Actualización anual

Cada enero actualiza los siguientes valores en la pestaña `Config` del spreadsheet:

- `ipc_YYYY` — IPC certificado por el DANE (usado para calcular incrementos de canon)
- `uvt_YYYY` — Valor de la UVT publicado por la DIAN

Y agrega los nuevos eventos en la pestaña `Calendario_Tributario` con las fechas del nuevo año tributario.
