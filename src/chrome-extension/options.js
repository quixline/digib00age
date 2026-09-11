const STORAGE_KEY = 'extraOrigins';

const listEl = document.getElementById('origin-list');
const formEl = document.getElementById('add-form');
const inputEl = document.getElementById('origin-input');
const statusEl = document.getElementById('status');

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = kind || '';
}

function normalizeOrigin(raw) {
  const withScheme = /^https?:\/\//i.test(raw.trim()) ? raw.trim() : `http://${raw.trim()}`;
  let url;
  try {
    url = new URL(withScheme);
  } catch {
    throw new Error(`"${raw}" isn't a valid address`);
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new Error('Only http:// or https:// addresses are supported');
  }
  return url.origin;
}

async function getOrigins() {
  const { [STORAGE_KEY]: origins } = await chrome.storage.local.get(STORAGE_KEY);
  return origins || [];
}

async function saveOrigins(origins) {
  await chrome.storage.local.set({ [STORAGE_KEY]: origins });
}

async function render() {
  const origins = await getOrigins();
  listEl.innerHTML = '';
  if (!origins.length) {
    const li = document.createElement('li');
    li.style.border = 'none';
    li.style.color = '#888';
    li.textContent = 'No additional addresses configured.';
    listEl.appendChild(li);
    return;
  }
  for (const origin of origins) {
    const li = document.createElement('li');
    const span = document.createElement('span');
    span.textContent = origin;
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = 'Remove';
    removeBtn.addEventListener('click', () => removeOrigin(origin));
    li.appendChild(span);
    li.appendChild(removeBtn);
    listEl.appendChild(li);
  }
}

async function addOrigin(origin) {
  const pattern = `${origin}/*`;

  const granted = await chrome.permissions.request({ origins: [pattern] });
  if (!granted) {
    setStatus(`Permission for ${origin} was not granted — nothing added.`, 'error');
    return;
  }

  try {
    await chrome.scripting.registerContentScripts(contentScriptDefsFor(origin));
  } catch {
    // Already registered from a prior add that didn't get cleanly removed
    // (e.g. permission revoked via chrome://extensions instead of the Remove
    // button here) — clear it and retry once.
    await chrome.scripting.unregisterContentScripts({ ids: contentScriptIdsFor(origin) });
    await chrome.scripting.registerContentScripts(contentScriptDefsFor(origin));
  }

  const origins = await getOrigins();
  if (!origins.includes(origin)) {
    origins.push(origin);
    await saveOrigins(origins);
  }

  setStatus(`Added ${origin}.`, 'ok');
  await render();
}

async function removeOrigin(origin) {
  const pattern = `${origin}/*`;

  await chrome.scripting.unregisterContentScripts({ ids: contentScriptIdsFor(origin) });
  await chrome.permissions.remove({ origins: [pattern] });

  const origins = (await getOrigins()).filter((o) => o !== origin);
  await saveOrigins(origins);

  setStatus(`Removed ${origin}.`, 'ok');
  await render();
}

formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  const raw = inputEl.value;
  if (!raw.trim()) return;

  let origin;
  try {
    origin = normalizeOrigin(raw);
  } catch (err) {
    setStatus(err.message, 'error');
    return;
  }

  if (origin === 'http://localhost:9800') {
    setStatus('localhost:9800 already works out of the box — no need to add it.', 'error');
    return;
  }

  const existing = await getOrigins();
  if (existing.includes(origin)) {
    setStatus(`${origin} is already configured.`, 'error');
    return;
  }

  setStatus('Requesting permission…', '');
  await addOrigin(origin);
  inputEl.value = '';
});

render();
