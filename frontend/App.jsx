import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'Something went wrong.')
  return data
}

function App() {
  const [user, setUser] = useState(null)
  const [checkingLogin, setCheckingLogin] = useState(true)
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([])
  const [current, setCurrent] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function loadHistory() {
    const items = await request('/api/research')
    setHistory(items)
  }

  useEffect(() => {
    request('/api/auth/me')
      .then(async (account) => {
        setUser(account)
        await loadHistory()
      })
      .catch(() => {})
      .finally(() => setCheckingLogin(false))
  }, [])

  async function submitAccount(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const account = await request(`/api/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setUser(account)
      setPassword('')
      await loadHistory()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function logout() {
    await request('/api/auth/logout', { method: 'POST' })
    setUser(null)
    setCurrent(null)
    setHistory([])
  }

  async function research(event) {
    event.preventDefault()
    if (question.trim().length < 2 || busy) return
    setBusy(true)
    setError('')
    setCurrent(null)
    try {
      const saved = await request('/api/research', {
        method: 'POST',
        body: JSON.stringify({ topic: question.trim() }),
      })
      setCurrent(saved)
      setQuestion('')
      await loadHistory()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function openResearch(id) {
    setError('')
    try {
      setCurrent(await request(`/api/research/${id}`))
    } catch (err) {
      setError(err.message)
    }
  }

  if (checkingLogin) return <main className="simple-page"><p className="muted">Loading…</p></main>

  if (!user) {
    return (
      <main className="simple-page auth-page">
        <section className="auth-card">
          <div className="logo">Research<span>.</span></div>
          <h1>{mode === 'login' ? 'Log in' : 'Create an account'}</h1>
          <p className="muted">Save your research and open it again any time.</p>
          {error && <p className="error-message">{error}</p>}
          <form onSubmit={submitAccount} className="stack-form">
            <label>Email<input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
            <label>Password<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
            {mode === 'register' && <p className="field-hint">Use at least 8 characters.</p>}
            <button className="primary-button" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}</button>
          </form>
          <p className="switch-mode">{mode === 'login' ? 'New here?' : 'Already registered?'}{' '}
            <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
              {mode === 'login' ? 'Create an account' : 'Log in'}
            </button>
          </p>
        </section>
      </main>
    )
  }

  return (
    <main className="simple-page">
      <header className="simple-header">
        <div className="logo">Research<span>.</span></div>
        <div className="account"><span>{user.email}</span><button type="button" onClick={logout}>Log out</button></div>
      </header>

      <section className="main-column">
        <h1>Ask a research question</h1>
        <form className="question-form" onSubmit={research}>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What would you like to know?" maxLength={500} rows={3} />
          <div className="question-footer"><span>{question.length}/500</span><button className="primary-button" disabled={busy || question.trim().length < 2}>{busy ? 'Researching…' : 'Research'}</button></div>
        </form>
        {error && <p className="error-message">{error}</p>}

        {current && (
          <article className="saved-report">
            <div className="report-id">Saved as <strong>#{current.id}</strong></div>
            <h2>{current.topic}</h2>
            <div className="report-body"><ReactMarkdown>{current.report || 'No report was returned.'}</ReactMarkdown></div>
          </article>
        )}

        <section className="history-section">
          <h2>Saved research</h2>
          {history.length === 0 ? <p className="muted">Your saved questions will appear here.</p> : (
            <ul>{history.map((item) => (
              <li key={item.id}>
                <button type="button" className={current?.id === item.id ? 'history-item active' : 'history-item'} onClick={() => openResearch(item.id)}>
                  <span className="history-id">#{item.id}</span><span>{item.topic}</span>
                </button>
              </li>
            ))}</ul>
          )}
        </section>
      </section>
    </main>
  )
}

export default App
