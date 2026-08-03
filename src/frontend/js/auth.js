// digib00age — auth.js
// Admin/Editor password gate: login popup, logout control, global 401 interception,
// and the deterministic View Only lock (ADMIN_SPEC.md Section 7.1 / 7.2).
//
// The lock is driven solely by checkAuthStatus()'s result — protection_enabled
// && !authenticated — never by whether the login popup happens to be open.
// Cancelling the popup does not unlock anything; only a successful login
// (which reloads the page) or protection being off does.

let loginPopupReady = null;   // Promise — fragment fetched + chrome wired
let popupShowing = false;
let authLocked = false;       // current View Only lock state — read by other page scripts

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
  document.getElementById('loginCancelBtn').addEventListener('click', hideLoginPopup);
}

async function onLoginSubmit(e) {
  e.preventDefault();
  const password = document.getElementById('login-password').value;
  const errorBox = document.getElementById('loginError');
  errorBox.hidden = true;
  errorBox.textContent = '';

  try {
    await apiFetch('/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
      retry: false, // avoid double-submitting a password attempt against the login rate limiter
    });
  } catch (err) {
    errorBox.hidden = false;
    errorBox.textContent = err.status === 423
      ? 'Too many failed attempts. Try again in a few minutes.'
      : err.status
        ? 'Incorrect password.'
        : 'Network error — could not reach the server.';
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
  const passwordInput = document.getElementById('login-password');
  if (passwordInput) passwordInput.value = '';
  const errorBox = document.getElementById('loginError');
  if (errorBox) { errorBox.hidden = true; errorBox.textContent = ''; }
  // Deliberately no lock change here — Cancel dismisses the modal, nothing else.
  // The page stays exactly as locked/unlocked as checkAuthStatus() found it.
}

function ensureViewOnlyBanner() {
  let banner = document.getElementById('viewOnlyBanner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'viewOnlyBanner';
    banner.className = 'view-only-banner';
    banner.hidden = true;
    banner.innerHTML = `
      <span>View Only &mdash; sign in to make changes</span>
      <button type="button" class="btn-admin-action" id="viewOnlyLoginBtn">Login</button>
    `;
    document.body.appendChild(banner);
    document.getElementById('viewOnlyLoginBtn').addEventListener('click', showLoginPopup);
  }
  return banner;
}

const PROTECTED_PATHS = ['/admin', '/editor'];

// Deterministic View Only lock — driven only by auth status, never by popup
// visibility. `main` covers everything in the page's primary content area;
// `[data-auth-gated]` covers the handful of controls (Full Editor's header
// action buttons) that sit outside <main> but still need to be locked.
//
// The DOM lock itself only applies on /admin and /editor — those are the
// pages whose entire content is "the feature behind the gate." Library pages
// (index/series/issue) load auth.js too (for the global 401 interceptor and
// the Login/Logout button) but browsing/reading was never gated, so they keep
// rendering normally; only `authLocked` gets tracked there, for callers like
// editor_basic.js's Basic Editor popup to check before opening.
function applyAuthLock(locked, onProtectedPage) {
  authLocked = locked;
  if (!onProtectedPage) return;

  document.body.classList.toggle('auth-locked', locked);
  const main = document.querySelector('main');
  if (main) main.inert = locked;
  document.querySelectorAll('[data-auth-gated]').forEach((el) => { el.inert = locked; });

  ensureViewOnlyBanner().hidden = !locked;
}

function showNoPasswordSetModal() {
  let overlay = document.getElementById('noPasswordOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'noPasswordOverlay';
    overlay.className = 'editor-overlay';
    overlay.innerHTML = `
      <div class="editor-modal login-modal">
        <div class="editor-modal-header">
          <h2 class="editor-modal-title">Password Protection Not Set Up</h2>
        </div>
        <p class="fe-multixml-hint">
          No admin password has been set, so there's nothing to log in with yet.
          Turn on "Require a password for Admin / Editor" in Advanced Settings and set a
          password first — then Login will work.
        </p>
        <div class="editor-actions">
          <button type="button" class="btn-primary" id="noPasswordOkBtn">OK</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    document.getElementById('noPasswordOkBtn').addEventListener('click', () => {
      overlay.hidden = true;
    });
  }
  overlay.hidden = false;
}

async function checkAuthStatus() {
  const status = await apiFetch('/admin/auth/status');

  const authBtn = document.getElementById('logoutBtn');
  if (authBtn) {
    authBtn.hidden = false;
    authBtn.textContent = status.authenticated ? 'Logout' : 'Login';
    authBtn.dataset.authenticated = String(status.authenticated);
    authBtn.dataset.protectionEnabled = String(status.protection_enabled);
  }

  const locked = status.protection_enabled && !status.authenticated;
  const onProtectedPage = PROTECTED_PATHS.some((p) => window.location.pathname.startsWith(p));
  applyAuthLock(locked, onProtectedPage);

  if (locked && onProtectedPage) {
    showLoginPopup();
  }

  // v2.4 Item 1: Remote Administration off means the Admin cog has no function
  // for a non-local request — but the icon stays in place (just inert) rather
  // than being removed, so the Login/Logout button next to it doesn't shift.
  const settingsBtn = document.querySelector('.settings-btn');
  if (settingsBtn) {
    const disabled = !status.is_local && !status.remote_admin_enabled;
    settingsBtn.classList.toggle('settings-btn--disabled', disabled);
    settingsBtn.dataset.tooltip = disabled
      ? 'Admin access is off for remote sessions'
      : 'Open admin settings';
  }

  return status;
}

function wireLogoutButton() {
  const authBtn = document.getElementById('logoutBtn');
  if (!authBtn) return;
  authBtn.addEventListener('click', async () => {
    if (authBtn.dataset.authenticated === 'true') {
      await apiFetch('/admin/logout', { method: 'POST' });
      location.reload();
    } else if (authBtn.dataset.protectionEnabled === 'false') {
      showNoPasswordSetModal();
    } else {
      showLoginPopup();
    }
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
