const messagesEl = document.getElementById('messages')
const inputEl = document.getElementById('input')
const sendBtn = document.getElementById('send')
const themeToggle = document.getElementById('themeToggle')
const resForm = document.getElementById('resForm')
const resGrade = document.getElementById('resGrade')
const resSubject = document.getElementById('resSubject')
const resResults = document.getElementById('resResults')

let loading = false

function setTheme(theme) {
  document.body.dataset.theme = theme
  localStorage.setItem('chat_theme', theme)
  themeToggle.textContent = theme === 'dark' ? '☀️ Light' : '🌙 Dark'
}

function initTheme() {
  const saved = localStorage.getItem('chat_theme')
  if (saved === 'dark' || saved === 'light') {
    setTheme(saved)
    return
  }
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  setTheme(prefersDark ? 'dark' : 'light')
}

themeToggle.addEventListener('click', () => {
  const next = document.body.dataset.theme === 'dark' ? 'light' : 'dark'
  setTheme(next)
})

initTheme()

function formatText(text) {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  const withInline = escaped
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')

  return withInline
    .split(/\n\n+/)
    .map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`)
    .join('')
}

function addMessage(role, text, emotion = null, audioUrl = null) {
  const wrapper = document.createElement('div')
  wrapper.className = `msg ${role}`

  const bubble = document.createElement('div')
  bubble.className = 'bubble'

  const who = document.createElement('div')
  who.style.fontWeight = 600
  who.textContent = role === 'user' ? 'You' : 'Assistant'

  const body = document.createElement('div')
  body.innerHTML = formatText(text)

  bubble.appendChild(who)
  bubble.appendChild(body)

  if (role === 'assistant' && emotion) {
    const meta = document.createElement('div')
    meta.className = 'meta'
    const conf = Math.round((emotion.confidence || 0) * 100)
    meta.textContent = `🧠 Detected: ${String(emotion.primary_emotion || 'neutral').toUpperCase()} (${conf}%) — ${String(emotion.educational_context || 'general')}`
    bubble.appendChild(meta)
  }

  if (role === 'assistant' && audioUrl) {
    const audio = document.createElement('audio')
    audio.className = 'audio'
    audio.controls = true
    audio.src = audioUrl
    bubble.appendChild(audio)
  }

  wrapper.appendChild(bubble)
  messagesEl.appendChild(wrapper)
  messagesEl.scrollTop = messagesEl.scrollHeight
}

async function send() {
  if (loading) return
  const text = inputEl.value.trim()
  if (!text) return

  loading = true
  sendBtn.disabled = true

  addMessage('user', text)
  inputEl.value = ''

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    addMessage('assistant', data.reply, data.emotion_analysis, data.audio_url || null)
  } catch (e) {
    addMessage('assistant', 'Sorry, something went wrong. Please try again.')
  } finally {
    loading = false
    sendBtn.disabled = false
  }
}

sendBtn.addEventListener('click', send)
inputEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') send() })

function escapeHtml(str) {
  return String(str || '').replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','\'':'&#39;','"':'&quot;'}[c]))
}

function renderResources(data) {
  if (!data || !data.links || data.links.length === 0) {
    resResults.innerHTML = '<div class="meta">No resources found. Try another selection.</div>'
    return
  }
  const emojiMap = { English: '📖', Maths: '🔢', Science: '🔬' }
  let html = `<div class="bubble" style="background: var(--panel-bg);">`
  html += `<div style="font-weight:600;margin-bottom:6px;">${emojiMap[data.subject] || '📚'} ${escapeHtml(data.subject)}</div>`
  html += `<div class="meta">Grade: ${escapeHtml(data.grade)} • Topic: ${escapeHtml(data.topic)}</div>`
  data.links.forEach(link => {
    const t = link.title || 'Resource'
    const url = link.url || '#'
    const type = (link.type || 'OTHER').toUpperCase()
    const typeEmoji = { VIDEO: '🎬', GAME: '🎮', WORKSHEET: '📄', NOTES: '📚', PRACTICE: '✏️' }
    const emoji = typeEmoji[type] || '📌'
    html += `<div style="border-left:4px solid var(--accent);padding:8px;margin:10px 0;background:rgba(0,102,255,.05);border-radius:4px;">`
    html += `<div style="font-weight:600;margin-bottom:4px;">${emoji} ${escapeHtml(t)}</div>`
    if (link.why_short) html += `<div class="meta" style="margin-bottom:6px;">${escapeHtml(link.why_short)}</div>`
    html += `<a href="${url}" target="_blank" class="ghost-btn">Open Link →</a>`
    html += `</div>`
  })
  html += `</div>`
  resResults.innerHTML = html
}

if (resForm) {
  resForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    resResults.innerHTML = '<div class="meta">Searching…</div>'
    try {
      const r = await fetch('/resources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grade: resGrade.value, subject: resSubject.value })
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const data = await r.json()
      renderResources(data)
    } catch (e) {
      resResults.innerHTML = '<div class="meta">Error fetching resources. Please try again.</div>'
    }
  })
}
