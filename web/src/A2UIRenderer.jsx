/**
 * Lightweight A2UI v0.9 renderer.
 * Processes an array of A2UI messages (createSurface, updateComponents)
 * and renders components: Card, Table, Text, Heading, Badge, List, Row, Column, Button.
 */

export default function A2UIRenderer({ messages }) {
  if (!messages || !Array.isArray(messages)) return null

  // Extract components from updateComponents messages
  const components = []
  for (const msg of messages) {
    if (msg.type === 'updateComponents' && Array.isArray(msg.components)) {
      components.push(...msg.components)
    }
  }

  if (components.length === 0) return null

  return (
    <div className="a2ui">
      {components.map((comp, i) => (
        <A2UIComponent key={comp.id ?? i} component={comp} />
      ))}
    </div>
  )
}

function A2UIComponent({ component }) {
  if (!component) return null
  const { type, properties = {}, children = [] } = component

  switch (type) {
    case 'Card':    return <Card props={properties} children={children} />
    case 'Table':   return <Table props={properties} />
    case 'Text':    return <p className="a2ui-text">{properties.text ?? properties.content ?? ''}</p>
    case 'Heading': return <h3 className="a2ui-heading">{properties.text ?? properties.title ?? ''}</h3>
    case 'Badge':   return <Badge value={properties.value ?? properties.text ?? ''} />
    case 'List':    return <List props={properties} children={children} />
    case 'Row':     return <Row children={children} />
    case 'Column':  return <Column children={children} />
    case 'Button':  return <button className="a2ui-button">{properties.label ?? properties.text ?? 'Acción'}</button>
    case 'TextField': return <TextField props={properties} />
    case 'AlertCard': return <AlertCard props={properties} />
    case 'MaintenanceCard': return <MaintenanceCard props={properties} />
    case 'LeaseCard': return <LeaseCard props={properties} />
    case 'FinancialSnapshot': return <FinancialSnapshot props={properties} />
    case 'TaxEstimate': return <TaxEstimate props={properties} />
    default:        return null
  }
}

function AlertCard({ props }) {
  const { title, description, status, actions = [] } = props
  return (
    <div className={`a2ui-alert-card a2ui-alert-card--${status}`}>
      <div className="a2ui-alert-card__title">{title}</div>
      <div className="a2ui-alert-card__desc">{description}</div>
      {actions.length > 0 && (
        <div className="a2ui-alert-card__actions">
          {actions.map((act, i) => (
            <button key={i} className="a2ui-button">{act}</button>
          ))}
        </div>
      )}
    </div>
  )
}

function MaintenanceCard({ props }) {
  const { title, unit, status, priority, contractor, aiDiagnosis } = props
  return (
    <div className="a2ui-maintenance-card">
      <div className="a2ui-maintenance-header">
        <span className="a2ui-card__title">{title}</span>
        <Badge value={status} />
      </div>
      <div className="a2ui-maintenance-meta">
        <span>Unit: {unit}</span>
        <span>Priority: <Badge value={priority} /></span>
        {contractor && <span>Contractor: {contractor}</span>}
      </div>
      {aiDiagnosis && (
        <div className="a2ui-maintenance-ai">
          <strong>Luppita AI:</strong> {aiDiagnosis}
        </div>
      )}
    </div>
  )
}

function LeaseCard({ props }) {
  const { tenant, property, rent, endDate, daysRemaining, progress } = props
  return (
    <div className="a2ui-lease-card">
      <div className="a2ui-lease-info">
        <div className="a2ui-card__title">{tenant}</div>
        <div className="a2ui-card__subtitle">{property}</div>
        <div className="a2ui-text">Rent: {rent} • Ends: {endDate}</div>
        <div className="a2ui-lease-progress">
          <div className="a2ui-lease-progress-bar" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="a2ui-card__subtitle" style={{ marginTop: '4px' }}>{daysRemaining} days left</div>
      </div>
    </div>
  )
}

function FinancialSnapshot({ props }) {
  const { collected, outstanding, currency = '$' } = props
  return (
    <div className="a2ui-financial-snapshot">
      <div className="a2ui-financial-metric">
        <label>Total Collected This Month</label>
        <span className="positive">{currency}{collected.toLocaleString()}</span>
      </div>
      <div className="a2ui-financial-metric">
        <label>Outstanding Balance</label>
        <span className="highlight">{currency}{outstanding.toLocaleString()}</span>
      </div>
      <button className="a2ui-button" style={{ background: 'var(--obsidian-indigo)', borderColor: 'transparent' }}>
        Generate Financial Report
      </button>
    </div>
  )
}

function TaxEstimate({ props }) {
  const { estimate, year, status, documents = [] } = props
  return (
    <div className="a2ui-tax-estimate">
      <div className="a2ui-card__title">Tax Estimate {year}</div>
      <div className="a2ui-tax-chart-placeholder">{estimate}</div>
      <div className="a2ui-column">
        <div className="a2ui-card__subtitle">Compliance Status</div>
        <Badge value={status} />
      </div>
      {documents.length > 0 && (
        <div className="a2ui-column">
          <div className="a2ui-card__subtitle">Documents Vault</div>
          <ul className="a2ui-list">
            {documents.map((doc, i) => (
              <li key={i}>{doc}</li>
            ))}
          </ul>
        </div>
      )}
      <button className="a2ui-button" style={{ border: '1px solid var(--obsidian-gold)', color: 'var(--obsidian-gold)', background: 'transparent' }}>
        Consult with Tax Expert
      </button>
    </div>
  )
}

function Card({ props, children }) {
  const sem = props.semaforo ?? props.status ?? ''
  const semClass = sem === 'CRITICO' ? 'critico' : sem === 'ALERTA' ? 'alerta' : sem === 'OK' ? 'ok' : ''

  return (
    <div className={`a2ui-card ${semClass ? `a2ui-card--${semClass}` : ''}`}>
      {(props.title || sem) && (
        <div className="a2ui-card__header">
          {props.title && <span className="a2ui-card__title">{props.title}</span>}
          {sem && <Badge value={sem} />}
        </div>
      )}
      {props.subtitle && <p className="a2ui-card__subtitle">{props.subtitle}</p>}
      {props.description && <p className="a2ui-card__body">{props.description}</p>}
      {children.map((c, i) => <A2UIComponent key={c.id ?? i} component={c} />)}
    </div>
  )
}

function Table({ props }) {
  const { columns = [], rows = [] } = props
  if (!rows.length) return null

  const cols = columns.length
    ? columns
    : Object.keys(rows[0]).map(k => ({ key: k, label: k }))

  return (
    <div className="a2ui-table-wrap">
      <table className="a2ui-table">
        <thead>
          <tr>{cols.map(c => <th key={c.key ?? c}>{c.label ?? c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map(c => {
                const key = c.key ?? c
                const val = row[key] ?? ''
                return <td key={key}>{val}</td>
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Badge({ value }) {
  const v = String(value)
  const color =
    ['CRITICO', 'ALTA', 'VENCIDO'].includes(v) ? 'red' :
    ['ALERTA', 'MEDIA', 'PARCIAL', 'PENDIENTE'].includes(v) ? 'yellow' :
    ['OK', 'PAGADO', 'BAJA', 'VIGENTE'].includes(v) ? 'green' : 'gray'
  return <span className={`a2ui-badge a2ui-badge--${color}`}>{v}</span>
}

function List({ props, children }) {
  const items = Array.isArray(props.items) ? props.items : []
  return (
    <ul className="a2ui-list">
      {items.map((item, i) => (
        <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
      ))}
      {children.map((c, i) => (
        <li key={`c${i}`}><A2UIComponent component={c} /></li>
      ))}
    </ul>
  )
}

function Row({ children }) {
  return (
    <div className="a2ui-row">
      {children.map((c, i) => <A2UIComponent key={c.id ?? i} component={c} />)}
    </div>
  )
}

function Column({ children }) {
  return (
    <div className="a2ui-column">
      {children.map((c, i) => <A2UIComponent key={c.id ?? i} component={c} />)}
    </div>
  )
}

function TextField({ props }) {
  return (
    <div className="a2ui-field">
      {props.label && <label>{props.label}</label>}
      <input
        type="text"
        placeholder={props.placeholder ?? ''}
        defaultValue={props.value ?? ''}
        readOnly
      />
    </div>
  )
}
