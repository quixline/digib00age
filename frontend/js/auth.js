// ComicVault — auth.js
// Admin/Editor password gate: login popup, logout control, global 401 interception.
// ADMIN_SPEC.md Section 7.1 / 7.2.

let loginPopupReady = null;   // Promise — fragment fetched + chrome wired
let popupShowing = false;

function ensureLoginPopupLoaded() {
  if (loginPopupReady) return loginPopupReady;

  loginPopupReady = fetch('/static/login_popup.html')
    .then((res) => res.text())
    .then((html) => {
      const container = document.createElement('div');
      container.innerHTML = html;
      document.body.appendChild(container.firstElementChild);
      wireLoginChrome();
    });

  return loginPopupReady;
}

function wireLoginChrome() {
  document.getElementById('loginForm').addEventListener('submit', onLoginSubmit);
}

async function onLoginSubmit(e) {
  e.preventDefault();
  const password = document.getElementById('login-password').value;
  const errorBox = document.getElementById('loginError');
  errorBox.hidden = true;
  errorBox.textContent = '';

  const res = await fetch('/api/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });

  if (!res.ok) {
    errorBox.hidden = false;
    errorBox.textContent = res.status === 423
      ? 'Too many failed attempts. Try again in a few minutes.'
      : 'Incorrect password.';
    return;
  }

  // Simplest correct behaviour given the global fetch interception below:
  // reload rather than transparently retrying the request that triggered the popup.
  location.reload();
}

async function showLoginPopup() {
  if (popupShowing) return;
  popupShowing = true;
  await ensureLoginPopupLoaded();
  document.getElementById('loginOverlay').hidden = false;
  document.getElementById('login-password').focus();
}

function hideLoginPopup() {
  popupShowing = false;
  const overlay = document.getElementById('loginOverlay');
  if (overlay) overlay.hidden = true;
}

async function checkAuthStatus() {
  const res = await fetch('/api/admin/auth/status');
  const status = await res.json();

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.hidden = !status.authenticated;

  if (status.protection_enabled && !status.authenticated) {
    showLoginPopup();
  }

  return status;
}

function wireLogoutButton() {
  const logoutBtn = document.getElementById('logoutBtn');
  if (!logoutBtn) return;
  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/admin/logout', { method: 'POST' });
    location.reload();
  });
}

// Global 401 interception — covers apiFetch() in app.js and every raw fetch() call
// site in editor_basic.js / editor_full.js without rewriting each one individually.
(function installFetchInterceptor() {
  const nativeFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await nativeFetch(...args);
    if (response.status === 401) {
      showLoginPopup();
    }
    return response;
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  wireLogoutButton();
  checkAuthStatus();
});
