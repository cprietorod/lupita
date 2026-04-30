# language: es
@ui @a2ui
Característica: Visualización de Componentes A2UI "The Obsidian Concierge"

  Como usuario de Luppita
  Quiero ver interfaces visuales de alta fidelidad en el chat
  Para gestionar mis propiedades de manera eficiente

  Antecedentes:
    Dado que el agente tiene activado el soporte A2UI
    Y estoy en la interfaz web de Luppita

  Escenario: Visualización de Alertas Críticas
    Cuando el agente envía un componente de tipo "AlertCard" con estado "CRITICO"
    Entonces debería ver una tarjeta con un borde lateral rojo
    Y el título de la alerta debería ser visible
    Y las acciones de la alerta deberían estar disponibles como botones

  Escenario: Seguimiento de Mantenimiento con IA
    Cuando el agente envía un componente de tipo "MaintenanceCard"
    Entonces debería ver el estado del ticket y su prioridad
    Y debería aparecer una sección de "IA Diagnosis" con fondo azulado y texto en cursiva
    Y el nombre del contratista asignado debería ser visible

  Escenario: Resumen de Contratos y Arriendos
    Cuando el agente envía un componente de tipo "LeaseCard"
    Entonces debería ver el nombre del inquilino y la propiedad
    Y debería aparecer una barra de progreso que indica los días restantes
    Y el monto de la renta mensual debería ser visible

  Escenario: Snapshot Financiero de Alto Impacto
    Cuando el agente envía un componente de tipo "FinancialSnapshot"
    Entonces debería ver un panel con un degradado profundo
    Y las métricas de "Total Recaudado" y "Saldo Pendiente" deberían destacar en blanco y oro
    Y el botón para generar reporte financiero debería estar presente

  Escenario: Estimación de Impuestos y Cumplimiento
    Cuando el agente envía un componente de tipo "TaxEstimate"
    Entonces debería ver la estimación anual con un gráfico circular de color oro
    Y debería aparecer una lista de documentos en la "Bóveda de Documentos"
    Y debería ver el estado de cumplimiento normativo
