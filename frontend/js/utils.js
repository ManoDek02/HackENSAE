'use strict';

/* ── Base URL API ────────────────────────────────────────── */
const API_BASE = '';   // Même origine — FastAPI sert frontend + API

/* ── Requêtes HTTP ───────────────────────────────────────── */
async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`/api${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`);
  return data;
}

/* ── Auth ────────────────────────────────────────────────── */
const Auth = {
  getToken()   { return localStorage.getItem('token'); },
  getUser()    { const u = localStorage.getItem('user'); return u ? JSON.parse(u) : null; },
  isLoggedIn() { return !!this.getToken(); },
  getRole()    { const u = this.getUser(); return u?.role || null; },
  save(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  requireLogin(redirect = '/pages/login.html') {
    if (!this.isLoggedIn()) { window.location.href = redirect; return false; }
    return true;
  },
  requireRole(role, redirect = '/index.html') {
    if (this.getRole() !== role) { window.location.href = redirect; return false; }
    return true;
  }
};

/* ── Navbar dynamique ────────────────────────────────────── */
function initNavbar() {
  const navLinks = document.querySelector('.navbar__links');
  const navActions = document.querySelector('.navbar__actions');
  if (!navLinks || !navActions) return;

  const user = Auth.getUser();
  const isOrg = user?.role === 'organisateur' || user?.role === 'admin';

  // Reconstruire les liens selon le rôle
  if (isOrg) {
    navLinks.innerHTML = `
      <a href="/index.html" class="navbar__link">Hackathons</a>
      <a href="/pages/dashboard-organisateur.html" class="navbar__link">Organisation</a>
    `;
  } else {
    navLinks.innerHTML = `
      <a href="/index.html" class="navbar__link">Hackathons</a>
      <a href="/pages/mon-espace.html" class="navbar__link">Mon espace</a>
      <a href="/pages/resultats.html" class="navbar__link">Résultats</a>
    `;
  }

  // Marquer le lien actif
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  navLinks.querySelectorAll('.navbar__link').forEach(l => {
    const linkPage = l.getAttribute('href').split('/').pop();
    l.classList.toggle('active', linkPage === currentPage);
  });

  // Boutons de droite
  if (Auth.isLoggedIn() && user) {
    const initials = ((user.prenom?.[0] || '') + (user.nom?.[0] || '')).toUpperCase() || 'U';
    navActions.innerHTML = `
      <span style="font-size:0.8125rem;color:var(--blue-200);">${user.prenom || user.email}</span>
      <div style="width:32px;height:32px;border-radius:50%;background:var(--blue-400);
        color:var(--white);display:flex;align-items:center;justify-content:center;
        font-size:0.75rem;font-weight:500;cursor:pointer;"
        onclick="Auth.clear();window.location.href='/index.html';"
        title="Se déconnecter">${initials}</div>
    `;
  } else {
    navActions.innerHTML = `
      <a href="/pages/login.html" class="btn btn-ghost btn-sm">Se connecter</a>
      <a href="/pages/login.html" class="btn btn-nav btn-sm">S'inscrire</a>
    `;
  }
}

/* ── Toast ───────────────────────────────────────────────── */
let _toastContainer;
function toast(message, type = 'info', duration = 4000) {
  if (!_toastContainer) {
    _toastContainer = document.createElement('div');
    _toastContainer.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;';
    document.body.appendChild(_toastContainer);
  }
  const colors = {
    info:    'background:#042C53;border-color:#185FA5;',
    success: 'background:#065F46;border-color:#059669;',
    warning: 'background:#92400E;border-color:#D97706;',
    error:   'background:#991B1B;border-color:#DC2626;',
  };
  const el = document.createElement('div');
  el.style.cssText = `${colors[type]||colors.info}color:#fff;border:1px solid;padding:12px 18px;border-radius:10px;font-size:0.875rem;max-width:320px;pointer-events:auto;opacity:0;transform:translateY(8px);transition:opacity 0.2s ease,transform 0.2s ease;`;
  el.textContent = message;
  _toastContainer.appendChild(el);
  requestAnimationFrame(() => { el.style.opacity='1'; el.style.transform='translateY(0)'; });
  setTimeout(() => {
    el.style.opacity='0'; el.style.transform='translateY(8px)';
    el.addEventListener('transitionend', () => el.remove());
  }, duration);
}

/* ── Badges statut ───────────────────────────────────────── */
const STATUS_LABELS = {
  a_venir:      { label: 'À venir',               cls: 'badge-gray'  },
  inscriptions: { label: 'Inscriptions ouvertes',  cls: 'badge-green' },
  en_cours:     { label: 'En cours',               cls: 'badge-blue'  },
  soumission:   { label: 'Soumissions ouvertes',   cls: 'badge-amber' },
  evaluation:   { label: 'Évaluation jury',         cls: 'badge-blue'  },
  termine:      { label: 'Terminé',                cls: 'badge-gray'  },
};
function statusBadge(status) {
  const s = STATUS_LABELS[status] || { label: status, cls: 'badge-gray' };
  return `<span class="badge ${s.cls}">${s.label}</span>`;
}

/* ── Dates ───────────────────────────────────────────────── */
function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
}
function daysUntil(iso) {
  return Math.ceil((new Date(iso) - new Date()) / 86400000);
}

/* ── Progress bar ────────────────────────────────────────── */
function progressBar(pct, cls = '') {
  const p = Math.min(100, Math.max(0, Math.round(pct)));
  return `<div class="progress"><div class="progress__bar ${cls}" style="width:${p}%"></div></div>`;
}

/* ── Render carte hackathon ──────────────────────────────── */
function renderHackathonCard(h) {
  const isDataj = h.type === 'datajournalisme';
  const headerStyle = isDataj ? 'background:#085041' : 'background:var(--blue-900)';
  const days = h.date_fin_inscriptions ? daysUntil(h.date_fin_inscriptions) : null;
  const daysLabel = days !== null && days >= 0
    ? `<span class="text-xs" style="color:${days<=3?'var(--warning-mid)':'var(--blue-300)'};">${days}j restants</span>` : '';
  const pct = Math.round((h.phase_actuelle / h.phases_total) * 100);
  const nb = h.nb_equipes_inscrites || 0;
  return `
    <article class="card">
      <div class="card__header" style="${headerStyle}">
        <div class="card__header-badge">${statusBadge(h.statut)}</div>
        <h3>${h.titre}</h3><p>${h.organisateur}</p>
      </div>
      <div class="card__body">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-muted">Équipes de 1 à ${h.taille_equipe_max} membres</span>${daysLabel}
        </div>
        ${progressBar(pct)}
        <p class="text-xs text-muted mt-2">Phase ${h.phase_actuelle} sur ${h.phases_total} — ${h.phase_label}</p>
        <div class="flex gap-2 mt-4" style="flex-wrap:wrap;">${(h.domaines||[]).slice(0,3).map(d=>`<span class="tag">${d}</span>`).join('')}</div>
      </div>
      <div class="card__footer">
        <span class="text-xs text-muted">${nb} équipe${nb!==1?'s':''} inscrite${nb!==1?'s':''}</span>
        <a href="pages/hackathon-detail.html?id=${h.id}" class="btn btn-primary btn-sm">Voir & s'inscrire</a>
      </div>
    </article>`;
}

document.addEventListener('DOMContentLoaded', initNavbar);
