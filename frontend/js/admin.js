/* ComicVault — admin.js */

const API = '/api';
let scanPollInterval = null;
let _config = { library_roots: [], scan_exclude: [], library_root: '' };

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadConfig();
  initPagination();

  document.getElementById('backupBtn').addEventListener('click', doBackup);
  document.getElementById('addRootBtn').addEventListener('click', addRoot);
  document.getElementById('addExcludeBtn').addEventListener('click', addExclude);
  document.getElementById('advancedLock').addEventListener('change', toggleAdvanced);
  document.getElementById('saveAdvancedBtn').addEventListener('click', saveAdvanced);

  document.getElementById('newRootInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') addRoot();
  });
  document.getElementById('newExcludeInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') addExclude();
  });
});

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const r = await fetch(`${API}/admin/stats`);
    if (!r.ok) throw new Error(r.statusText);
    const d = await r.json();
    renderStats(d);
    renderScanSection(d.scan_state, d.missing_count);
  } catch (e) {
    document.getElementById('statGrid').innerHTML =
      '<div class="loading-state">Failed to load stats</div>';
    document.getElementById('scanGrid').innerHTML =
      '<div class="loading-state">Failed to load scan info</div>';
  }
}

function renderStats(d) {
  const readPct = d.total_issues > 0
    ? Math.round((d.read_count / d.total_issues) * 100)
    : 0;

  const cards = [
    { label: 'Total Files',  value: d.total_issues.toLocaleString() },
    { label: 'Series',       value: d.series_count.toLocaleString() },
    { label: 'Singles',      value: d.singles_count.toLocaleString() },
    {
      label: '',
      value: d.read_count.toLocaleString(),
      unit: 'Read',
      sub: `${readPct}% of Total`,
    },
    { label: 'In Progress',  value: d.reading_count.toLocaleString() },
  ];

  const grid = document.getElementById('statGrid');
  grid.innerHTML = '';
  for (const c of cards) {
    const card = document.createElement('div');
    card.className = 'stat-card';
    card.innerHTML = `
      <div class="stat-value">${c.value}${c.unit ? `<span class="stat-unit">${c.unit}</span>` : ''}</div>
      ${c.sub ? `<div class="stat-sub">${c.sub}</div>` : ''}
      ${c.label ? `<div class="stat-label">${c.label}</div>` : ''}
    `;
    grid.appendChild(card);
  }
}

// ── Scan section ──────────────────────────────────────────────────────────────
function renderScanSection(scanState, missingCount) {
  const grid = document.getElementById('scanGrid');
  grid.innerHTML = '';

  const lastScan = scanState.finished_at
    ? new Date(scanState.finished_at).toLocaleString()
    : 'Never';

  // Scan Now card — first
  const scanCard = document.createElement('div');
  scanCard.className = 'stat-card scan-now-card';
  scanCard.id = 'scanNowCard';
  scanCard.innerHTML = `
    <button class="btn-primary" id="scanNowBtn">Scan Now</button>
    <div class="scan-progress" id="scanProgress" hidden>
      <div class="scan-bar-wrap"><div class="scan-bar" id="scanBar"></div></div>
      <div class="scan-status-text" id="scanStatusText"></div>
    </div>
    <div class="stat-label" style="margin-top:auto;">Scan library for new and changed files</div>
  `;
  grid.appendChild(scanCard);
  document.getElementById('scanNowBtn').addEventListener('click', doScan);

  if (scanState.running) {
    showScanProgress();
    startScanPoll();
  }

  // Info cards
  const infoCards = [
    { label: 'Last Scan',               value: lastScan },
    { label: 'Files Found',             value: (scanState.total_files    || 0).toLocaleString() },
    { label: 'New Files',               value: (scanState.new_files      || 0).toLocaleString() },
    { label: 'Changed Files',           value: (scanState.updated_files  || 0).toLocaleString() },
  ];

  for (const c of infoCards) {
    const card = document.createElement('div');
    card.className = 'stat-card';
    card.innerHTML = `<div class="stat-label">${c.label}</div><div class="stat-value stat-value--md">${c.value}</div>`;
    grid.appendChild(card);
  }

  // Missing records card — last
  const mc = missingCount || 0;
  const missingCard = document.createElement('div');
  missingCard.className = 'stat-card scan-now-card';
  missingCard.innerHTML = `
    <div class="stat-label">Missing Records</div>
    <div class="stat-value stat-value--md" id="missingCountVal">${mc.toLocaleString()}</div>
    <button class="btn-admin-action" id="cleanupBtn"${mc === 0 ? ' disabled' : ''}>Clean Up</button>
    <div class="scan-status-text" id="cleanupResult"></div>
  `;
  grid.appendChild(missingCard);
  document.getElementById('cleanupBtn').addEventListener('click', doCleanup);
}

function showScanProgress() {
  const btn = document.getElementById('scanNowBtn');
  const prog = document.getElementById('scanProgress');
  if (btn) { btn.disabled = true; btn.textContent = 'Scanning…'; }
  if (prog) prog.hidden = false;
}

async function doScan() {
  showScanProgress();
  try {
    const r = await fetch(`${API}/scan`, { method: 'POST' });
    const d = await r.json();
    if (d.running) startScanPoll();
  } catch (e) {
    const btn = document.getElementById('scanNowBtn');
    if (btn) { btn.disabled = false; btn.textContent = 'Scan Now'; }
    showToast('Failed to start scan: ' + e.message, true);
  }
}

async function doCleanup() {
  const btn     = document.getElementById('cleanupBtn');
  const countEl = document.getElementById('missingCountVal');
  const result  = document.getElementById('cleanupResult');
  btn.disabled = true;
  btn.textContent = 'Cleaning…';
  try {
    const r = await fetch(`${API}/admin/cleanup-missing`, { method: 'POST' });
    const d = await r.json();
    if (r.ok) {
      if (countEl) countEl.textContent = '0';
      if (result)  result.textContent = `${d.removed} record${d.removed !== 1 ? 's' : ''} removed`;
      showToast(`Removed ${d.removed} missing record${d.removed !== 1 ? 's' : ''}`);
    } else {
      btn.disabled = false;
      btn.textContent = 'Clean Up';
      showToast('Cleanup failed', true);
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = 'Clean Up';
    showToast('Cleanup failed: ' + e.message, true);
  }
}

function startScanPoll() {
  if (scanPollInterval) return;
  scanPollInterval = setInterval(pollScanStatus, 1000);
}

function stopScanPoll() {
  clearInterval(scanPollInterval);
  scanPollInterval = null;
}

async function pollScanStatus() {
  try {
    const r = await fetch(`${API}/scan/status`);
    const d = await r.json();
    updateScanUI(d);
    if (!d.running) {
      stopScanPoll();
      loadStats();
    }
  } catch (_) {}
}

function updateScanUI(state) {
  const btn    = document.getElementById('scanNowBtn');
  const prog   = document.getElementById('scanProgress');
  const barEl  = document.getElementById('scanBar');
  const textEl = document.getElementById('scanStatusText');

  if (!btn) return;

  if (state.running) {
    btn.disabled = true;
    btn.textContent = 'Scanning…';
    if (prog) prog.hidden = false;

    const pct = state.total_files > 0
      ? Math.round((state.processed_files / state.total_files) * 100)
      : 0;
    if (barEl) barEl.style.width = `${pct}%`;
    if (textEl) textEl.textContent = `${state.processed_files} / ${state.total_files}`;
  } else {
    btn.disabled = false;
    btn.textContent = 'Scan Now';
    if (barEl) barEl.style.width = '100%';
    if (textEl && state.finished_at) {
      textEl.textContent =
        `Done — ${state.new_files} new, ${state.updated_files} updated, ${state.missing_files} missing`;
    }
    if (state.error && textEl) {
      textEl.textContent = 'Error: ' + state.error;
    }
  }
}

// ── Backup ─────────────────────────────────────────────────────────────────────
async function doBackup() {
  const btn = document.getElementById('backupBtn');
  btn.disabled = true;
  btn.textContent = 'Backing up…';
  try {
    const r = await fetch(`${API}/admin/backup`, { method: 'POST' });
    const d = await r.json();
    if (r.ok) {
      showToast('Backup saved: ' + d.backup_file);
    } else {
      showToast('Backup failed: ' + (d.detail || 'Unknown error'), true);
    }
  } catch (e) {
    showToast('Backup failed: ' + e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Backup Database';
  }
}

// ── Config / Folders ──────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const r = await fetch(`${API}/admin/config`);
    if (!r.ok) throw new Error(r.statusText);
    _config = await r.json();
  } catch (_) {
    _config = { library_roots: [], scan_exclude: [], library_root: '' };
  }
  renderRoots();
  renderExcludes();
  renderAdvancedFields();
}

function renderRoots() {
  const list = document.getElementById('rootList');
  list.innerHTML = '';
  if (_config.library_roots.length === 0) {
    list.innerHTML = '<p class="admin-empty-hint">No scan roots configured.</p>';
    return;
  }
  for (const root of _config.library_roots) {
    list.appendChild(makeFolderRow(root, () => removeRoot(root)));
  }
}

function renderExcludes() {
  const list = document.getElementById('excludeList');
  list.innerHTML = '';
  if (_config.scan_exclude.length === 0) {
    list.innerHTML = '<p class="admin-empty-hint">No exclusions.</p>';
    return;
  }
  for (const ex of _config.scan_exclude) {
    list.appendChild(makeFolderRow(ex, () => removeExclude(ex)));
  }
}

function makeFolderRow(path, onRemove) {
  const row  = document.createElement('div');
  row.className = 'folder-row';
  const span = document.createElement('span');
  span.className = 'folder-path';
  span.textContent = path;
  const btn  = document.createElement('button');
  btn.className = 'folder-remove-btn';
  btn.textContent = 'Remove';
  btn.addEventListener('click', onRemove);
  row.append(span, btn);
  return row;
}

async function patchConfig(patch) {
  try {
    const r = await fetch(`${API}/admin/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    if (!r.ok) throw new Error(await r.text());
    showToast('Saved');
  } catch (e) {
    showToast('Save failed: ' + e.message, true);
  }
}

function addRoot() {
  const input = document.getElementById('newRootInput');
  const val   = input.value.trim();
  if (!val || _config.library_roots.includes(val)) { input.value = ''; return; }
  _config.library_roots = [..._config.library_roots, val];
  renderRoots();
  patchConfig({ library_roots: _config.library_roots });
  input.value = '';
}

function removeRoot(path) {
  _config.library_roots = _config.library_roots.filter(r => r !== path);
  renderRoots();
  patchConfig({ library_roots: _config.library_roots });
}

function addExclude() {
  const input = document.getElementById('newExcludeInput');
  const val   = input.value.trim();
  if (!val || _config.scan_exclude.includes(val)) { input.value = ''; return; }
  _config.scan_exclude = [..._config.scan_exclude, val];
  renderExcludes();
  patchConfig({ scan_exclude: _config.scan_exclude });
  input.value = '';
}

function removeExclude(ex) {
  _config.scan_exclude = _config.scan_exclude.filter(e => e !== ex);
  renderExcludes();
  patchConfig({ scan_exclude: _config.scan_exclude });
}

// ── Pagination ────────────────────────────────────────────────────────────────
function initPagination() {
  const sel   = document.getElementById('pageSizeSelect');
  const saved = localStorage.getItem('cv_page_size') || '50';
  sel.value   = saved;
  sel.addEventListener('change', () => {
    localStorage.setItem('cv_page_size', sel.value);
    showToast(`Page size set to ${sel.value}`);
  });
}

// ── Advanced settings ─────────────────────────────────────────────────────────
function renderAdvancedFields() {
  const input = document.getElementById('readerLocationInput');
  if (input) input.value = _config.library_root || '';
}

function toggleAdvanced() {
  const locked  = !document.getElementById('advancedLock').checked;
  const fields  = document.getElementById('advancedFields');
  fields.disabled = locked;
}

async function saveAdvanced() {
  const val = document.getElementById('readerLocationInput').value.trim();
  await patchConfig({ library_root: val });
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, isError = false) {
  let toast = document.getElementById('adminToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'adminToast';
    toast.className = 'admin-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.toggle('admin-toast--error', isError);
  toast.classList.add('admin-toast--show');
  setTimeout(() => toast.classList.remove('admin-toast--show'), 3500);
}
