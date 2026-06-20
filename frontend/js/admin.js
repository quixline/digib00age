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

  loadCustomTabs();
  document.getElementById('ctAddBtn').addEventListener('click', addCustomTab);
  document.getElementById('ctBrowseBtn').addEventListener('click', () => openCtPicker('ctPathInput'));
  document.getElementById('ctPickerCloseBtn').addEventListener('click', closeCtPicker);
  document.getElementById('ctPickerSelectBtn').addEventListener('click', selectCtPickerFolder);

  loadHomeStrips();
  document.getElementById('hsAddBtn').addEventListener('click', addHomeStrip);
  document.getElementById('hsBrowseBtn').addEventListener('click', () => openCtPicker('hsFolderInput'));
  document.querySelectorAll('input[name="hsBasis"]').forEach(r => r.addEventListener('change', updateHsBasisRows));
  document.getElementById('hsFieldNameSelect').addEventListener('change', updateHsFieldValueOptions);
  document.getElementById('hsOrderModeSelect').addEventListener('change', updateHsOrderModeRow);

  loadGenreList();
  document.getElementById('genreAddBtn').addEventListener('click', addGenre);
  document.getElementById('genreNameInput').addEventListener('keydown', e => { if (e.key === 'Enter') addGenre(); });

  loadFormatList();
  document.getElementById('formatAddBtn').addEventListener('click', addFormat);
  document.getElementById('formatNameInput').addEventListener('keydown', e => { if (e.key === 'Enter') addFormat(); });
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

// ── Custom Tabs (CUSTOM_TABS_SPEC.md) ───────────────────────────────────────────
const MAX_VISIBLE_CUSTOM_TABS = 4;
let customTabs  = [];
let ctPickerPath = null;
let ctPickerRoots = [];

async function loadCustomTabs() {
  try {
    const r = await fetch(`${API}/admin/custom-tabs`);
    if (!r.ok) throw new Error(r.statusText);
    customTabs = await r.json();
  } catch (_) {
    customTabs = [];
  }
  renderCustomTabs();
}

function renderCustomTabs() {
  const list = document.getElementById('ctTabList');
  list.innerHTML = '';

  if (!customTabs.length) {
    list.innerHTML = '<p class="admin-empty-hint">No custom tabs yet.</p>';
  } else {
    for (const tab of customTabs) {
      list.appendChild(makeCustomTabRow(tab));
    }
  }

  const visibleCount = customTabs.filter(t => t.visible).length;
  const atCap   = visibleCount >= MAX_VISIBLE_CUSTOM_TABS;
  document.getElementById('ctAddBtn').disabled  = atCap;
  document.getElementById('ctCapHint').hidden    = !atCap;
}

function makeCustomTabRow(tab) {
  const row = document.createElement('div');
  row.className = 'ct-tab-row';

  const info = document.createElement('div');
  info.className = 'ct-tab-info';
  const nameLine = document.createElement('div');
  nameLine.className = 'ct-tab-name';
  nameLine.append(document.createTextNode(tab.name));
  if (!tab.visible) {
    const badge = document.createElement('span');
    badge.className = 'ct-hidden-badge';
    badge.textContent = 'Hidden';
    nameLine.appendChild(badge);
  }
  const pathLine = document.createElement('div');
  pathLine.className = 'ct-tab-path';
  pathLine.textContent = tab.folder_path;
  info.append(nameLine, pathLine);

  const toggleBtn = document.createElement('button');
  toggleBtn.className = `ct-visible-toggle${tab.visible ? ' is-visible' : ''}`;
  toggleBtn.textContent = tab.visible ? 'Visible' : 'Hidden';
  toggleBtn.addEventListener('click', () => toggleCustomTabVisible(tab));

  const delBtn = document.createElement('button');
  delBtn.className = 'folder-remove-btn';
  delBtn.textContent = 'Delete';
  delBtn.addEventListener('click', () => deleteCustomTab(tab));

  row.append(info, toggleBtn, delBtn);
  return row;
}

async function toggleCustomTabVisible(tab) {
  try {
    const r = await fetch(`${API}/admin/custom-tabs/${tab.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible: !tab.visible }),
    });
    const d = await r.json();
    if (!r.ok) {
      showToast(d.detail || 'Could not update tab', true);
      return;
    }
    await loadCustomTabs();
  } catch (e) {
    showToast('Could not update tab: ' + e.message, true);
  }
}

async function deleteCustomTab(tab) {
  const ok = confirm(
    `Delete tab "${tab.name}"?\n\n` +
    `This only removes the tab definition — it will not touch any comic files or library data.`
  );
  if (!ok) return;
  try {
    const r = await fetch(`${API}/admin/custom-tabs/${tab.id}`, { method: 'DELETE' });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      showToast(d.detail || 'Delete failed', true);
      return;
    }
    showToast('Tab deleted');
    await loadCustomTabs();
  } catch (e) {
    showToast('Delete failed: ' + e.message, true);
  }
}

async function addCustomTab() {
  const nameInput = document.getElementById('ctNameInput');
  const pathInput = document.getElementById('ctPathInput');
  const name = nameInput.value.trim();
  const folder_path = pathInput.value.trim();
  if (!name || !folder_path) {
    showToast('Name and folder path are both required', true);
    return;
  }
  try {
    const r = await fetch(`${API}/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, folder_path }),
    });
    const d = await r.json();
    if (!r.ok) {
      showToast(d.detail || 'Could not add tab', true);
      return;
    }
    if (d.warning) showToast(d.warning, true);
    else showToast('Tab added');
    nameInput.value = '';
    pathInput.value = '';
    await loadCustomTabs();
  } catch (e) {
    showToast('Could not add tab: ' + e.message, true);
  }
}

// ── Shared folder picker modal — used by both Custom Tabs and Home Strips ──────
let ctPickerTargetInputId = 'ctPathInput';

function openCtPicker(targetInputId) {
  ctPickerTargetInputId = targetInputId || 'ctPathInput';
  document.getElementById('ctPickerOverlay').hidden = false;
  loadCtPickerDir(ctPickerPath);
}

function closeCtPicker() {
  document.getElementById('ctPickerOverlay').hidden = true;
}

async function loadCtPickerDir(path) {
  const url = path ? `${API}/admin/browse?path=${encodeURIComponent(path)}` : `${API}/admin/browse`;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    const data = await r.json();
    ctPickerPath  = data.path;
    ctPickerRoots = data.roots || [];
    renderCtPickerRoots();
    renderCtPickerBreadcrumb(data.path);
    renderCtPickerTree(data.items || []);
  } catch (e) {
    showToast('Could not browse: ' + e.message, true);
  }
}

function renderCtPickerRoots() {
  const wrap = document.getElementById('ctPickerRoots');
  wrap.innerHTML = '';
  if (ctPickerRoots.length <= 1) return;
  for (const root of ctPickerRoots) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-admin-action';
    btn.textContent = root;
    btn.addEventListener('click', () => loadCtPickerDir(root));
    wrap.appendChild(btn);
  }
}

function renderCtPickerBreadcrumb(path) {
  const breadcrumb = document.getElementById('ctPickerBreadcrumb');
  const parts = path.split('\\').filter(Boolean);
  let accumulated = '';
  breadcrumb.innerHTML = '';
  parts.forEach((part, index) => {
    accumulated += (index === 0 ? '' : '\\') + part;
    const isLast = index === parts.length - 1;
    if (isLast) {
      const span = document.createElement('span');
      span.textContent = part;
      breadcrumb.appendChild(span);
    } else {
      const link = document.createElement('a');
      link.href = '#';
      link.textContent = part;
      const target = accumulated;
      link.onclick = (e) => { e.preventDefault(); loadCtPickerDir(target); };
      breadcrumb.appendChild(link);
    }
    if (!isLast) breadcrumb.appendChild(document.createTextNode(' \\ '));
  });
}

function renderCtPickerTree(items) {
  const tree = document.getElementById('ctPickerTree');
  tree.innerHTML = '';

  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'fe-picker-empty';
    empty.textContent = 'No subfolders.';
    tree.appendChild(empty);
    return;
  }

  items.sort((a, b) => a.name.localeCompare(b.name));
  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'fe-picker-item folder';
    const name = document.createElement('span');
    name.className = 'fe-picker-item-name';
    name.textContent = item.name;
    row.appendChild(name);
    row.addEventListener('click', () => loadCtPickerDir(item.path));
    tree.appendChild(row);
  }
}

function selectCtPickerFolder() {
  document.getElementById(ctPickerTargetInputId).value = ctPickerPath || '';
  closeCtPicker();
}

// ── Home Page Strips (HOME_STRIPS_SPEC.md) ──────────────────────────────────────
const MAX_NON_DEFAULT_HOME_STRIPS = 5;
const HS_FIELD_LABELS = {
  genre: 'Genre', publisher: 'Publisher', writer: 'Writer', artist: 'Artist',
  format: 'Format', decade: 'Decade', year: 'Year', rating: 'Rating', bw: 'Black & White',
};
const HS_FIELD_ENDPOINTS = {
  genre:     { url: '/browse/genres',     key: 'genre' },
  publisher: { url: '/browse/publishers', key: 'publisher' },
  writer:    { url: '/browse/writers',    key: 'writer' },
  artist:    { url: '/browse/artists',    key: 'artist' },
  format:    { url: '/browse/formats',    key: 'format' },
  decade:    { url: '/browse/decades',    key: 'decade' },
  year:      { url: '/browse/years',      key: 'year' },
  rating:    { url: '/browse/ratings',    key: 'rating' },
};
let homeStrips = [];

async function loadHomeStrips() {
  try {
    const r = await fetch(`${API}/admin/home-strips`);
    if (!r.ok) throw new Error(r.statusText);
    homeStrips = await r.json();
  } catch (_) {
    homeStrips = [];
  }
  renderHomeStrips();
}

function renderHomeStrips() {
  const list = document.getElementById('hsStripList');
  list.innerHTML = '';

  homeStrips.forEach((strip, index) => {
    list.appendChild(makeHomeStripRow(strip, index === 0, index === homeStrips.length - 1));
  });

  const nonDefaultCount = homeStrips.filter(s => !s.is_default).length;
  const atCap = nonDefaultCount >= MAX_NON_DEFAULT_HOME_STRIPS;
  document.getElementById('hsAddBtn').disabled = atCap;
  document.getElementById('hsCapHint').hidden = !atCap;
}

function hsBasisSummary(strip) {
  if (strip.basis_type === 'builtin') return strip.name === 'Continue Reading' ? 'pinned first when active' : 'default';
  if (strip.basis_type === 'field') return `${HS_FIELD_LABELS[strip.field_name] || strip.field_name}: ${strip.field_value}`;
  return strip.folder_path;
}

function makeHomeStripRow(strip, isFirst, isLast) {
  const row = document.createElement('div');
  row.className = 'ct-tab-row';

  const arrows = document.createElement('div');
  arrows.className = 'hs-reorder-arrows';
  const upBtn = document.createElement('button');
  upBtn.type = 'button';
  upBtn.className = 'hs-arrow-btn';
  upBtn.textContent = '▲';
  upBtn.disabled = isFirst;
  upBtn.addEventListener('click', () => moveHomeStrip(strip, -1));
  const downBtn = document.createElement('button');
  downBtn.type = 'button';
  downBtn.className = 'hs-arrow-btn';
  downBtn.textContent = '▼';
  downBtn.disabled = isLast;
  downBtn.addEventListener('click', () => moveHomeStrip(strip, 1));
  arrows.append(upBtn, downBtn);

  const info = document.createElement('div');
  info.className = 'ct-tab-info';
  const nameLine = document.createElement('div');
  nameLine.className = 'ct-tab-name';
  nameLine.append(document.createTextNode(strip.name));
  if (strip.is_default) {
    const badge = document.createElement('span');
    badge.className = 'ct-hidden-badge';
    badge.textContent = 'Default';
    nameLine.appendChild(badge);
  } else if (!strip.visible) {
    const badge = document.createElement('span');
    badge.className = 'ct-hidden-badge';
    badge.textContent = 'Hidden';
    nameLine.appendChild(badge);
  }
  const summaryLine = document.createElement('div');
  summaryLine.className = 'ct-tab-path';
  summaryLine.textContent = hsBasisSummary(strip);
  info.append(nameLine, summaryLine);

  row.append(arrows, info);

  if (!strip.is_default) {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = `ct-visible-toggle${strip.visible ? ' is-visible' : ''}`;
    toggleBtn.textContent = strip.visible ? 'Visible' : 'Hidden';
    toggleBtn.addEventListener('click', () => toggleHomeStripVisible(strip));

    const delBtn = document.createElement('button');
    delBtn.className = 'folder-remove-btn';
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', () => deleteHomeStrip(strip));

    row.append(toggleBtn, delBtn);
  }

  return row;
}

async function moveHomeStrip(strip, direction) {
  const index = homeStrips.findIndex(s => s.id === strip.id);
  const swapIndex = index + direction;
  if (swapIndex < 0 || swapIndex >= homeStrips.length) return;

  const other = homeStrips[swapIndex];
  const payload = [
    { id: strip.id, position: other.position },
    { id: other.id, position: strip.position },
  ];
  try {
    const r = await fetch(`${API}/admin/home-strips/reorder`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      showToast(d.detail || 'Reorder failed', true);
      return;
    }
    await loadHomeStrips();
  } catch (e) {
    showToast('Reorder failed: ' + e.message, true);
  }
}

async function toggleHomeStripVisible(strip) {
  try {
    const r = await fetch(`${API}/admin/home-strips/${strip.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible: !strip.visible }),
    });
    const d = await r.json();
    if (!r.ok) {
      showToast(d.detail || 'Could not update strip', true);
      return;
    }
    await loadHomeStrips();
  } catch (e) {
    showToast('Could not update strip: ' + e.message, true);
  }
}

async function deleteHomeStrip(strip) {
  const ok = confirm(
    `Delete strip "${strip.name}"?\n\n` +
    `This only removes the strip definition — it will not touch any comic files or library data.`
  );
  if (!ok) return;
  try {
    const r = await fetch(`${API}/admin/home-strips/${strip.id}`, { method: 'DELETE' });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      showToast(d.detail || 'Delete failed', true);
      return;
    }
    showToast('Strip deleted');
    await loadHomeStrips();
  } catch (e) {
    showToast('Delete failed: ' + e.message, true);
  }
}

function hsBasisType() {
  const checked = document.querySelector('input[name="hsBasis"]:checked');
  return checked ? checked.value : 'field';
}

function updateHsBasisRows() {
  const basis = hsBasisType();
  document.getElementById('hsFieldRow').hidden = basis !== 'field';
  document.getElementById('hsFolderRow').hidden = basis !== 'folder';
}

async function updateHsFieldValueOptions() {
  const fieldName = document.getElementById('hsFieldNameSelect').value;
  const valueSelect = document.getElementById('hsFieldValueSelect');
  valueSelect.innerHTML = '<option value="">Value…</option>';
  if (!fieldName) return;

  if (fieldName === 'bw') {
    valueSelect.add(new Option('Yes', 'yes'));
    valueSelect.add(new Option('No', 'no'));
    return;
  }

  const endpoint = HS_FIELD_ENDPOINTS[fieldName];
  if (!endpoint) return;
  try {
    const r = await fetch(`${API}${endpoint.url}`);
    const rows = await r.json();
    for (const row of rows) {
      const val = String(row[endpoint.key]);
      valueSelect.add(new Option(val, val));
    }
  } catch (_) {
    // Leave the placeholder-only dropdown — add will fail validation server-side if used.
  }
}

function updateHsOrderModeRow() {
  document.getElementById('hsSortFieldSelect').hidden = document.getElementById('hsOrderModeSelect').value !== 'fixed';
}

async function addHomeStrip() {
  const nameInput = document.getElementById('hsNameInput');
  const name = nameInput.value.trim();
  if (!name) {
    showToast('Strip name is required', true);
    return;
  }

  const basisType = hsBasisType();
  const orderMode = document.getElementById('hsOrderModeSelect').value;
  const payload = { name, basis_type: basisType, order_mode: orderMode };

  if (basisType === 'field') {
    payload.field_name = document.getElementById('hsFieldNameSelect').value;
    payload.field_value = document.getElementById('hsFieldValueSelect').value;
    if (!payload.field_name || !payload.field_value) {
      showToast('Pick a field and a value', true);
      return;
    }
  } else {
    payload.folder_path = document.getElementById('hsFolderInput').value.trim();
    if (!payload.folder_path) {
      showToast('Folder path is required', true);
      return;
    }
  }
  if (orderMode === 'fixed') {
    payload.sort_field = document.getElementById('hsSortFieldSelect').value;
  }

  try {
    const r = await fetch(`${API}/admin/home-strips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const d = await r.json();
    if (!r.ok) {
      showToast(d.detail || 'Could not add strip', true);
      return;
    }
    if (d.warning) showToast(d.warning, true);
    else showToast('Strip added');
    nameInput.value = '';
    document.getElementById('hsFolderInput').value = '';
    document.getElementById('hsFieldNameSelect').value = '';
    document.getElementById('hsFieldValueSelect').innerHTML = '<option value="">Value…</option>';
    await loadHomeStrips();
  } catch (e) {
    showToast('Could not add strip: ' + e.message, true);
  }
}

// ── Genre / Format editable lists (comicvault-changes.md Tier 4 Item 1) ───────
// Same shape for both kinds — 'genres' uses /api/browse/genres + 'genre' as the
// count-row key, 'formats' uses /api/browse/formats + 'format'.

async function loadEditableValueList(kind) {
  const countKey = kind === 'genres' ? 'genre' : 'format';
  let names = [];
  let counts = {};
  try {
    names = await fetch(`${API}/editor/${kind}`).then(r => r.json());
  } catch (_) {
    names = [];
  }
  try {
    const rows = await fetch(`${API}/browse/${kind}`).then(r => r.json());
    for (const row of rows) counts[row[countKey]] = row.issue_count;
  } catch (_) {
    counts = {};
  }
  return names.map(name => ({ name, count: counts[name] || 0 }));
}

function renderEditableValueList(containerId, items, kind) {
  const list = document.getElementById(containerId);
  list.innerHTML = '';

  if (!items.length) {
    list.innerHTML = '<p class="admin-empty-hint">No values yet.</p>';
    return;
  }

  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'ct-tab-row';

    const info = document.createElement('div');
    info.className = 'ct-tab-info';
    const nameLine = document.createElement('div');
    nameLine.className = 'ct-tab-name';
    nameLine.append(document.createTextNode(item.name));
    const badge = document.createElement('span');
    badge.className = 'ct-hidden-badge';
    badge.textContent = item.count === 1 ? '1 issue' : `${item.count} issues`;
    nameLine.appendChild(badge);
    info.appendChild(nameLine);

    const delBtn = document.createElement('button');
    delBtn.className = 'folder-remove-btn';
    delBtn.textContent = 'Delete';
    delBtn.disabled = items.length <= 1;
    delBtn.title = items.length <= 1 ? 'At least one value must remain' : '';
    delBtn.addEventListener('click', () => deleteEditableValue(kind, item.name, item.count));

    row.append(info, delBtn);
    list.appendChild(row);
  }
}

async function loadGenreList() {
  renderEditableValueList('genreList', await loadEditableValueList('genres'), 'genres');
}

async function loadFormatList() {
  renderEditableValueList('formatList', await loadEditableValueList('formats'), 'formats');
}

async function deleteEditableValue(kind, name, count) {
  const label = kind === 'genres' ? 'genre' : 'format';
  if (count > 0) {
    const ok = confirm(
      `"${name}" is used by ${count} issue${count === 1 ? '' : 's'} — remove it from the ${label} list anyway?\n\n` +
      `Existing issues keep their current value; this only removes "${name}" from future selection.`
    );
    if (!ok) return;
  }
  try {
    const r = await fetch(`${API}/editor/${kind}/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) {
      showToast(d.detail || 'Delete failed', true);
      return;
    }
    showToast(`${label[0].toUpperCase()}${label.slice(1)} removed`);
    await (kind === 'genres' ? loadGenreList() : loadFormatList());
  } catch (e) {
    showToast('Delete failed: ' + e.message, true);
  }
}

async function addEditableValue(kind, inputId) {
  const input = document.getElementById(inputId);
  const name = input.value.trim();
  const label = kind === 'genres' ? 'Genre' : 'Format';
  if (!name) {
    showToast(`${label} name is required`, true);
    return;
  }
  try {
    const r = await fetch(`${API}/editor/${kind}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) {
      showToast(d.detail || `Could not add ${label.toLowerCase()}`, true);
      return;
    }
    showToast(`${label} added`);
    input.value = '';
    await (kind === 'genres' ? loadGenreList() : loadFormatList());
  } catch (e) {
    showToast(`Could not add ${label.toLowerCase()}: ` + e.message, true);
  }
}

function addGenre() { addEditableValue('genres', 'genreNameInput'); }
function addFormat() { addEditableValue('formats', 'formatNameInput'); }

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
