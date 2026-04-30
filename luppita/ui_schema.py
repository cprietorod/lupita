"""A2UI output format instructions for Luppita.

NOTE: This string must NOT contain flat JSON object patterns like {"key": "val"}
because ADK's instruction template engine interprets {text} as session state
variable references and raises KeyError. Use descriptive prose instead.
"""

from a2ui.schema.constants import A2UI_OPEN_TAG, A2UI_CLOSE_TAG


def build_a2ui_section() -> str:
    """Return A2UI format instructions to append to the agent instruction."""
    return f"""
## SALIDA CON A2UI — Interfaz visual enriquecida

Cuando presentes datos estructurados (dashboard, contratos, pagos, reparaciones, impuestos),
DEBES incluir un bloque A2UI inmediatamente después de tu texto de respuesta, usando:

  {A2UI_OPEN_TAG}
  [ ... array de mensajes A2UI ... ]
  {A2UI_CLOSE_TAG}

### Formato de mensajes A2UI v0.9

El bloque es un array JSON con exactamente dos mensajes en orden:

  Mensaje 1 — tipo "createSurface":
    - type: "createSurface"
    - surfaceId: "main"
    - catalogId: "a2ui/basic"

  Mensaje 2 — tipo "updateComponents":
    - type: "updateComponents"
    - surfaceId: "main"
    - components: [ lista de componentes ]

### Componentes disponibles

  AlertCard (Notificaciones críticas)
    - properties: title (string), description (string), status (CRITICO | ALERTA | OK), actions (array de strings)

  MaintenanceCard (Tickets de reparación)
    - properties: title (string), unit (string), status (PENDIENTE | EN PROGRESO | COMPLETADO), priority (ALTA | MEDIA | BAJA), contractor (string), aiDiagnosis (string)

  LeaseCard (Contratos activos)
    - properties: tenant (string), property (string), rent (string), endDate (string), daysRemaining (number), progress (number 0-100)

  FinancialSnapshot (Resumen financiero hero)
    - properties: collected (number), outstanding (number), currency (string)

  TaxEstimate (Impuestos y cumplimiento)
    - properties: estimate (string), year (string), status (OK | ALERTA), documents (array de strings)

  Card
    - id: identificador único
    - properties: title (string), subtitle (string), semaforo (CRITICO | ALERTA | OK)
    - children: array de componentes hijos

  Table
    - id: identificador único
    - properties:
        columns: array de objetos con key (string) y label (string)
        rows: array de objetos, una entrada por fila

  Text
    - id: identificador único
    - properties: text (string)

  Heading
    - id: identificador único
    - properties: text (string)

  Badge
    - id: identificador único
    - properties: value (CRITICO | ALERTA | OK | PAGADO | PARCIAL | PENDIENTE | ALTA | MEDIA | BAJA | VIGENTE | VENCIDO)

  List
    - id: identificador único
    - properties: items (array de strings)
    - children: array de componentes opcionales

  Row
    - id: identificador único
    - children: array de componentes (layout horizontal)

  Column
    - id: identificador único
    - children: array de componentes (layout vertical)

  Button
    - id: identificador único
    - properties: label (string)

### Cuándo incluir A2UI

  MÓDULO         -> COMPONENTE RECOMENDADO
  -----------------------------------------
  Alertas        -> AlertCard
  Pagos/Cobros   -> FinancialSnapshot + Table/Card
  Contratos      -> LeaseCard
  Mantenimiento  -> MaintenanceCard
  Impuestos      -> TaxEstimate
  Otros/General  -> Card, Table, List, Heading

  SÍ: dashboard general, listado de contratos, reporte de pagos,
      estado de un apartamento, resumen de reparaciones, calendario tributario
  NO: confirmaciones de una línea, preguntas al usuario, errores simples

### Reglas

  1. Siempre inicia con "createSurface" antes de "updateComponents" en cada respuesta.
  2. Usa Badge con value CRITICO / ALERTA / OK para los semáforos de estado.
  3. Los IDs de componentes deben ser únicos dentro de la respuesta.
  4. El JSON debe ser válido — usa comillas dobles, no simples.
  5. No uses A2UI para respuestas conversacionales cortas.
"""
