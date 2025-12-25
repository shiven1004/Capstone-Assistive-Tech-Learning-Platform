const messagesEl = document.getElementById('messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const clearBtn = document.getElementById('clear-btn');

const resultsEl = document.getElementById('results');
const searchForm = document.getElementById('search-form');
const gradeEl = document.getElementById('grade');
const subjectEl = document.getElementById('subject');

let chatHistory = [];

function addMessage(role, content, audioUrl=null) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const name = role === 'user' ? 'You' : '🤖 Assistant';
  div.innerHTML = `<strong>${name}:</strong> <div>${escapeHtml(content)}</div>`;
  if (audioUrl) {
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = audioUrl;
    audio.className = 'audio';
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
    addMessage('bot', botText, data.audio);
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
  resultsEl.innerHTML = '<div class="message bot">Searching…</div>';
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
    resultsEl.innerHTML = '<div class="message bot">No resources found. Try another search!</div>';
    return;
  }
  const emojiMap = { English: '📖', Maths: '🔢', Science: '🔬' };
  let html = `<div class="resource"><div class="title">${emojiMap[data.subject] || '📚'} ${data.subject}</div><div class="meta"><strong>Grade:</strong> ${data.grade} • <strong>Topic:</strong> ${data.topic}</div></div>`;
  data.links.forEach((link, idx) => {
    const t = link.title || 'Resource';
    const url = link.url || '#';
    const type = (link.type || 'other').toUpperCase();
    html += `<div class="resource"><div class="title">${idx+1}. ${type}: ${escapeHtml(t)}</div><a href="${url}" target="_blank">Open Link</a>`;
    if (link.why_short) {
      html += `<div class="meta">${escapeHtml(link.why_short)}</div>`;
    }
    html += `</div>`;
  });
  resultsEl.innerHTML = html;
}
