import { useState, useEffect, useRef } from 'react'
import A2UIRenderer from './A2UIRenderer'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8001'
const APP_NAME = 'luppita'
const USER_ID = import.meta.env.VITE_USER_ID || 'user'
const A2UI_OPEN = '<a2ui-json>'
const A2UI_CLOSE = '</a2ui-json>'

/** Split LLM text into {text, a2uiJson} — a2uiJson is parsed array or null */
function parseA2UI(raw) {
  const openIdx = raw.indexOf(A2UI_OPEN)
  const closeIdx = raw.indexOf(A2UI_CLOSE)
  if (openIdx === -1 || closeIdx === -1 || closeIdx < openIdx) {
    return { text: raw.trim(), a2uiJson: null }
  }
  // Strip markdown table lines — they'll be shown via the A2UI widget
  const text = raw
    .slice(0, openIdx)
    .split('\n')
    .filter(line => !line.trim().startsWith('|'))
    .join('\n')
    .trim()
  const jsonStr = raw.slice(openIdx + A2UI_OPEN.length, closeIdx).trim()
  try {
    return { text, a2uiJson: JSON.parse(jsonStr) }
  } catch {
    return { text: raw.trim(), a2uiJson: null }
  }
}

/** From ADK events array, return the final assistant text (last text event, no functionCall) */
function extractFinalText(events) {
  let finalText = ''
  for (const event of events) {
    if (event.author !== APP_NAME) continue
    const parts = event.content?.parts ?? []
    const hasFunctionCall = parts.some(p => p.functionCall || p.function_call)
    if (hasFunctionCall) continue
    const text = parts.filter(p => p.text).map(p => p.text).join('')
    if (text) finalText = text
  }
  return finalText
}

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  // Create session on mount
  useEffect(() => {
    fetch(`${API}/apps/${APP_NAME}/users/${USER_ID}/sessions`, { method: 'POST' })
      .then(r => r.json())
      .then(data => setSessionId(data.id))
      .catch(() => setError('No se pudo conectar con el servidor. Inicia con: make server'))
  }, [])

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    }
  }, [input])

  const sendMessage = async () => {
    if (!input.trim() || !sessionId || loading) return

    const userText = input.trim()
    setInput('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { role: 'user', text: userText, a2uiJson: null },
    ])

    try {
      const res = await fetch(`${API}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_name: APP_NAME,
          user_id: USER_ID,
          session_id: sessionId,
          new_message: { role: 'user', parts: [{ text: userText }] },
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const events = await res.json()
      const rawText = extractFinalText(events)
      const { text, a2uiJson } = parseA2UI(rawText)

      setMessages(prev => [
        ...prev,
        { role: 'assistant', text, a2uiJson },
      ])
    } catch (e) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: `Error: ${e.message}`, a2uiJson: null },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Support for UI Tests injection
  useEffect(() => {
    const handler = (e) => {
      if (e.detail) {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', text: `Test Injection ${Date.now()}`, a2uiJson: e.detail },
        ])
      }
    }
    window.addEventListener('test-inject-a2ui', handler)
    window.A2UI_READY = true
    return () => {
      window.removeEventListener('test-inject-a2ui', handler)
    }
  }, [])

  return (
    <div className="app">
      <header className="header">
        <div className="logo">L</div>
        <div>
          <h1>Luppita</h1>
          <p>Gestión de arriendos · Portafolio Cerezos</p>
        </div>
        <div className={`status ${sessionId ? 'status--ok' : 'status--err'}`}>
          {sessionId ? 'Conectado' : 'Sin conexión'}
        </div>
      </header>

      {error && <div className="banner-error">{error}</div>}

      <main className="messages">
        {messages.length === 0 && !loading && (
          <div className="empty">
            <div className="empty-logo">L</div>
            <p>Hola, soy Luppita</p>
            <p className="empty-sub">Tu asistente de gestión de propiedades en Colombia.</p>
            <div className="suggestions">
              {['Ver dashboard', 'Contratos por vencer', '¿Quién está en mora?', 'Impuestos próximos'].map(s => (
                <button key={s} className="suggestion" onClick={() => { setInput(s); textareaRef.current?.focus() }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`msg msg--${msg.role}`}>
            {msg.role === 'assistant' && <div className="msg-avatar">L</div>}
            <div className="msg-body">
              {msg.text && !msg.a2uiJson && <div className="msg-text">{msg.text}</div>}
              {msg.a2uiJson && <A2UIRenderer messages={msg.a2uiJson} />}
            </div>
          </div>
        ))}

        {loading && (
          <div className="msg msg--assistant">
            <div className="msg-avatar">L</div>
            <div className="msg-body">
              <div className="typing"><span /><span /><span /></div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Escribe un mensaje… (Enter para enviar)"
          disabled={!sessionId || loading}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={!sessionId || loading || !input.trim()}
          aria-label="Enviar"
        >
          ↑
        </button>
      </footer>
    </div>
  )
}
