const messagesEl = document.getElementById('messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const clearBtn = document.getElementById('clear-btn');
const themeToggle = document.getElementById('theme-toggle');

const resultsEl = document.getElementById('results');
const searchForm = document.getElementById('search-form');
const gradeEl = document.getElementById('grade');
const subjectEl = document.getElementById('subject');

let chatHistory = [];

// Theme handling
function applyTheme(theme) {
  const body = document.body;
  body.classList.remove('theme-dark', 'theme-light');
  const t = theme === 'light' ? 'theme-light' : 'theme-dark';
  body.classList.add(t);
  if (themeToggle) {
    themeToggle.textContent = theme === 'light' ? '☀️ Light' : '🌙 Dark';
  }
}

function initTheme() {
  const saved = localStorage.getItem('lp-theme');
  const theme = saved === 'light' ? 'light' : 'dark';
  applyTheme(theme);
}

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const isLight = document.body.classList.contains('theme-light');
    const next = isLight ? 'dark' : 'light';
    localStorage.setItem('lp-theme', next);
    applyTheme(next);
  });
}

initTheme();

function addMessage(role, content, audioUrl = null) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const name = role === 'user' ? 'You' : '🤖 Assistant';
  div.innerHTML = `<strong>${name}:</strong> <div>${escapeHtml(content)}</div>`;
  if (role === 'bot' && audioUrl) {
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.style.display = 'block';
    audio.style.marginTop = '8px';
    audio.src = audioUrl;
    div.appendChild(audio);
  }
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','\'':'&#39;','"':'&quot;'}[c]));
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  addMessage('user', text);
  chatHistory.push({ role: 'user', content: text });
  chatInput.value = '';

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: chatHistory }),
    });
    const data = await resp.json();
    const botText = data.text || 'I could not generate a response.';
    addMessage('bot', botText, data.audio || null);
    chatHistory.push({ role: 'assistant', content: botText });
  } catch (err) {
    addMessage('bot', 'Error responding. Please try again later.');
    console.error(err);
  }
});

clearBtn.addEventListener('click', () => {
  messagesEl.innerHTML = '';
  chatHistory = [];
});

searchForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  resultsEl.innerHTML = '<div class="message bot">Loading curated resources…</div>';
  try {
    const resp = await fetch('/api/resources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ grade: gradeEl.value, subject: subjectEl.value }),
    });
    const data = await resp.json();
    renderResults(data);
  } catch (err) {
    resultsEl.innerHTML = '<div class="message bot">Error fetching resources.</div>';
    console.error(err);
  }
});

function renderResults(data) {
  if (!data || !data.links || data.links.length === 0) {
    resultsEl.innerHTML = '<div style="padding: 15px; text-align: center; color: #999;">No resources found. Try another search!</div>';
    return;
  }
  const emojiMap = { English: '📖', Maths: '🔢', Science: '🔬' };
  let html = `<div style="margin-top: 20px;">`;
  html += `<div class="resource-item">`;
  html += `<div style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">${emojiMap[data.subject] || '📚'} <strong>${escapeHtml(data.subject)}</strong></div>`;
  html += `<div class="small text-muted"><strong>Grade:</strong> ${escapeHtml(data.grade)} &nbsp;•&nbsp; <strong>Topic:</strong> ${escapeHtml(data.topic)}</div>`;
  html += `</div>`;
  data.links.forEach((link, idx) => {
    const t = link.title || 'Resource';
    const url = link.url || '#';
    const type = (link.type || 'OTHER').toUpperCase();
    const typeEmoji = { 'VIDEO': '🎬', 'GAME': '🎮', 'WORKSHEET': '📄', 'NOTES': '📚', 'PRACTICE': '✏️' };
    const emoji = typeEmoji[type] || '📌';
    html += `<div class="resource-item">`;
    html += `<div style="font-weight: 600; margin-bottom: 6px; font-size: 14px;">${emoji} ${escapeHtml(t)}</div>`;
    if (link.why_short) {
      html += `<div class="small text-muted" style="margin-bottom: 6px;">${escapeHtml(link.why_short)}</div>`;
    }
    html += `<a href="${url}" target="_blank" class="btn btn-outline" style="font-size:12px; padding:6px 10px;">Open Link →</a>`;
    html += `</div>`;
  });
  html += `</div>`;
  resultsEl.innerHTML = html;
}
