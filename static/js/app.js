// TechNova World Dashboard — Shared JS Utilities

function toast(msg, isError = false) {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    el.className = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => el.classList.remove('show'), 3200);
}

async function apiPost(url, body) {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    const data = await r.json();
    if (!r.ok || data.ok === false) {
      toast(data.error || `Request failed (${r.status})`, true);
    }
    return data;
  } catch (e) {
    toast('Network error: ' + e.message, true);
    return { ok: false, error: e.message };
  }
}

async function apiGet(url) {
  try {
    const r = await fetch(url);
    const data = await r.json();
    if (!r.ok || data.ok === false) {
      toast(data.error || `Request failed (${r.status})`, true);
    }
    return data;
  } catch (e) {
    toast('Network error: ' + e.message, true);
    return { ok: false, error: e.message };
  }
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => toast('✅ Copied to clipboard!'));
}

function scoreColor(score) {
  if (score >= 80) return 'var(--green)';
  if (score >= 60) return 'var(--amber)';
  return 'var(--rose)';
}

function scoreRing(score, grade) {
  const color = scoreColor(score);
  return `<div class="score-ring" style="border-color:${color};color:${color}">${score}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Poll connection status on every page load (lightweight, cached check)
async function loadStatusChip() {
  const chip = document.getElementById('status-chip');
  if (!chip) return;
  const data = await apiGet('/api/status');
  if (!data.ok && data.error) return;

  const gem = data.gemini_configured;
  const li = data.linkedin_configured;
  let dotClass = 'dot';
  let label = 'Checking...';

  if (gem && li) { dotClass = 'dot'; label = 'AI + LinkedIn Ready'; }
  else if (gem) { dotClass = 'dot warn'; label = 'AI Ready, LinkedIn not set'; }
  else { dotClass = 'dot bad'; label = 'Setup needed'; }

  chip.innerHTML = `<span class="${dotClass}"></span> ${label}`;
}

document.addEventListener('DOMContentLoaded', loadStatusChip);
