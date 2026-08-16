/* digib00age — admin.js */

let scanPollInterval = null;
let _config = { library_roots: [], scan_exclude: [], library_root: '' };

// ── Back link (Tier 1 back-button fix) ──────────────────────────────────────────
// Same pattern as app.js's issue/series back links (duplicated, not shared —
// admin.html doesn't load app.js). Navigation uses the real browser
// history.back() rather than reconstructing a guessed destination, so it's
// automatically correct for every entry point into Admin (Home's gear icon,
// Guide's separate one, anything added later) with no per-entry-point wiring.
// Label is always literal "Back" — it previously showed the guessed source
// surface name, which is what app.js's equivalents still did until this fix.
function initAdminBackLink() {
  const backLink = document.getElementById('adminBackLink');
  if (!backLink) return;

  backLink.addEventListener('click', (e) => {
    if (window.history.length > 1) {
      e.preventDefault();
      window.history.back();
    }
    // else: no prior page in this tab's history (bookmark/direct nav/fresh tab) —
    // let the default href="/" proceed, same as a real back button would have
    // nothing useful to do either.
  });
}

// ── Settings navigation (v2.6 Item 1 Phase C1) ─────────────────────────────────
// Category → sub-item → content-pane, toggling `hidden` on the matching
// .admin-content-block. Purely additive — every field/button inside a block
// keeps the exact ID it always had, so none of the existing loadX()/bindX()
// functions below need to change; they just now render into a block that
// starts hidden until its nav card is picked.
//
const ADMIN_CATEGORIES = [
  { id: 'library-mgmt', label: 'Library Management', subItems: [
    { id: 'auto-scan', label: 'Auto Scan Settings' },
    { id: 'backup-schedule', label: 'DB Backup Schedule' },
    { id: 'restore-db', label: 'Restore DB' },
    { id: 'access-logs', label: 'Access Logs' },
    { id: 'library-folders', label: 'Library Folders' },
  ] },
  { id: 'library-appearance', label: 'Library Appearance', subItems: [
    { id: 'home-strips', label: 'Home Page Strips' },
    { id: 'libraries', label: 'Add/Remove Libraries' },
    { id: 'theme', label: 'Theme Selection' },
    { id: 'card-size', label: 'Card Size' },
    { id: 'pagination', label: 'Pagination' },
  ] },
  { id: 'processing-tools', label: 'Processing Tools', subItems: [
    { id: 'filename-editor', label: 'Filename Editor' },
    { id: 'converter', label: 'Converter: Archives & Images' },
    { id: 'xml-tagging', label: 'XML Tagging' },
    { id: 'folder-processing', label: 'Folder Processing' },
    { id: 'auto-processing', label: 'Auto Processing' },
  ] },
  { id: 'editor-options', label: 'Editor Options', subItems: [
    { id: 'genre-list', label: 'Genre List' },
    { id: 'format-list', label: 'Format List' },
  ] },
  { id: 'advanced-settings', label: 'Advanced Settings', subItems: [
    { id: 'password-protection', label: 'Password Protection' },
    { id: 'server-port', label: 'Change Server Port' },
    { id: 'wipe-database', label: 'Wipe Database' },
    { id: 'wipe-reading-state', label: 'Wipe Reading State' },
  ] },
];

function bindAdminNav() {
  const categoryNav = document.getElementById('adminCategoryNav');
  const subitemNav  = document.getElementById('adminSubitemNav');
  if (!categoryNav || !subitemNav) return;

  let activeCat = null, activeSub = null;

  function renderSubitems() {
    subitemNav.innerHTML = '';
    const lockWrap = document.getElementById('advancedLockWrap');
    if (lockWrap) lockWrap.hidden = activeCat !== 'advanced-settings';
    const cat = ADMIN_CATEGORIES.find(c => c.id === activeCat);
    if (!cat) { subitemNav.hidden = true; return; }
    subitemNav.hidden = false;
    cat.subItems.forEach(sub => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'admin-nav-card' + (sub.id === activeSub ? ' active' : '');
      btn.textContent = sub.label;
      btn.dataset.subitem = sub.id;
      btn.addEventListener('click', () => { activeSub = sub.id; renderSubitems(); renderContent(); });
      subitemNav.appendChild(btn);
    });
  }

  function renderContent() {
    document.querySelectorAll('.admin-content-block').forEach(block => {
      block.hidden = !(block.dataset.category === activeCat && block.dataset.subitem === activeSub);
    });
  }

  categoryNav.querySelectorAll('.admin-nav-card').forEach(btn => {
    btn.addEventListener('click', () => {
      const catId = btn.dataset.category;
      activeCat = catId === activeCat ? null : catId; // click active category again to collapse
      activeSub = null;
      categoryNav.querySelectorAll('.admin-nav-card').forEach(b => b.classList.toggle('active', b.dataset.category === activeCat));
      renderSubitems();
      renderContent();
    });
  });

  renderSubitems();
  renderContent();
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initAdminBackLink();
  bindAdminNav();
  loadStats();
  loadConfig();
  initPagination();
  initCardSize();
  initTheme();

  document.getElementById('backupBtn').addEventListener('click', doBackup);
  document.getElementById('addRootBtn').addEventListener('click', addRoot);
  document.getElementById('addExcludeBtn').addEventListener('click', addExclude);
  document.getElementById('rootBrowseBtn').addEventListener('click', () => {
    openFilePicker({
      title: 'Choose Scan Root Folder',
      mode: 'folder',
      browseUrl: '/admin/scan-root/browse',
      drivesUrl: '/admin/scan-root/drives',
      onConfirm: (paths) => {
        const input = document.getElementById('newRootInput');
        input.value = paths[0];
        input.dispatchEvent(new Event('input'));
      },
    });
  });
  document.getElementById('excludeBrowseBtn').addEventListener('click', () => openCtPicker('newExcludeInput'));
  document.getElementById('advancedLock').addEventListener('change', toggleAdvanced);
  document.getElementById('saveAdvancedBtn').addEventListener('click', saveAdvanced);

  document.getElementById('newRootInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') addRoot();
  });
  document.getElementById('newExcludeInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') addExclude();
  });
  document.getElementById('newRootInput').addEventListener('input', e => {
    document.getElementById('addRootBtn').classList.toggle('is-ready', e.target.value.trim().length > 0);
  });
  document.getElementById('newExcludeInput').addEventListener('input', e => {
    document.getElementById('addExcludeBtn').classList.toggle('is-ready', e.target.value.trim().length > 0);
  });

  loadCustomTabs();
  loadCtGenreOptions();
  loadCtWriterOptions();
  loadCtPublisherOptions();
  document.getElementById('ctAddBtn').addEventListener('click', addCustomTab);
  document.getElementById('ctAddFavouritesBtn').addEventListener('click', addFavouritesTab);
  document.getElementById('ctAddReadingQueueBtn').addEventListener('click', addReadingQueueTab);
  document.getElementById('ctAddGenreBtn').addEventListener('click', addGenreTab);
  document.getElementById('ctAddWriterBtn').addEventListener('click', addWriterTab);
  document.getElementById('ctAddPublisherBtn').addEventListener('click', addPublisherTab);
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

  initAuthSettings();

  document.getElementById('logViewerCloseBtn').addEventListener('click', closeLogViewer);
  document.getElementById('logViewerOverlay').addEventListener('click', (e) => {
    if (e.target.id === 'logViewerOverlay') closeLogViewer();
  });

  initScanSettings();
  initLogsSection();
  initServerPort();
  initBackupSettings();
  initDangerZone();
  initPasswordRecovery();
  initPWAInstall();
});

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const d = await apiFetch(`/admin/stats`);
    renderStats(d);
    renderScanSection(d.scan_state, d.missing_count, d.log_status);
    renderLastBackup(d.last_backup_at, d.last_backup_error);
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

// ── Last Backup indicator (Scheduled Backup block — 2.3-fixes.md Fix 9) ───────
function renderLastBackup(lastBackupAt, lastBackupError) {
  const valueEl = document.getElementById('lastBackupValue');
  const errorEl = document.getElementById('lastBackupError');
  if (!valueEl) return;

  valueEl.textContent = lastBackupAt ? new Date(lastBackupAt).toLocaleString() : 'Never';

  if (lastBackupError) {
    errorEl.hidden = false;
    errorEl.textContent = `⚠ Last scheduled backup failed: ${lastBackupError}`;
  } else {
    errorEl.hidden = true;
    errorEl.textContent = '';
  }
}

// ── Scan section ──────────────────────────────────────────────────────────────
function renderScanSection(scanState, missingCount, logStatus) {
  const grid = document.getElementById('scanGrid');
  grid.innerHTML = '';
  logStatus = logStatus || {};

  // Card shows the date only — scan_logs.append_last_scan_entry() writes the
  // persisted fallback as "DD/MM/YYYY HH:MM — Duration: HH:MM:SS" (full detail
  // for the Logs viewer); split() drops the time/duration for this summary card.
  const lastScan = scanState.finished_at
    ? new Date(scanState.finished_at).toLocaleDateString()
    : (scanState.last_scan_persisted ? scanState.last_scan_persisted.split(' ')[0] : 'Never');

  // Scan Now card — first
  const scanCard = document.createElement('div');
  scanCard.className = 'stat-card scan-now-card';
  scanCard.id = 'scanNowCard';
  scanCard.innerHTML = `
    <button class="btn-primary" id="scanNowBtn" data-tooltip="Scan the entire library for new and changed files">Scan Now</button>
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

  // Info cards — each maps to a persistent log file (ADMIN_SPEC.md §8)
  const infoCards = [
    { label: 'Last Scan',     value: lastScan,                                     logName: 'last_scan' },
    { label: 'Files Found',   value: (scanState.total_files   || 0).toLocaleString(), logName: null },
    { label: 'New Files',     value: (scanState.new_files     || 0).toLocaleString(), logName: 'new_files' },
    { label: 'Changed Files', value: (scanState.updated_files || 0).toLocaleString(), logName: 'changed_files' },
  ];

  for (const c of infoCards) {
    const card = document.createElement('div');
    card.className = 'stat-card';
    if (c.logName && logStatus[c.logName]) card.classList.add('has-pending');
    card.innerHTML = `
      <div class="stat-label">${c.label}</div>
      <div class="stat-value stat-value--md">${c.value}</div>
      ${c.logName ? `<button class="btn-admin-action log-btn" data-log="${c.logName}" data-tooltip="View recent log entries for this scan category">Logs</button>` : ''}
    `;
    grid.appendChild(card);
  }

  // Missing records card — last
  const mc = missingCount || 0;
  const missingCard = document.createElement('div');
  missingCard.className = 'stat-card scan-now-card';
  missingCard.id = 'missingRecordsCard';
  if (mc > 0 || logStatus.missing) missingCard.classList.add('has-pending');
  missingCard.innerHTML = `
    <div class="stat-label">Missing Records</div>
    <div class="stat-value stat-value--md" id="missingCountVal">${mc.toLocaleString()}</div>
    <button class="btn-admin-action" id="cleanupBtn"${mc === 0 ? ' disabled' : ''}>Clean Up</button>
    <div class="scan-status-text" id="cleanupResult"></div>
    <button class="btn-admin-action log-btn" data-log="missing" data-tooltip="View recent log entries for this scan category">Logs</button>
  `;
  grid.appendChild(missingCard);
  document.getElementById('cleanupBtn').addEventListener('click', doCleanup);

  for (const btn of grid.querySelectorAll('.log-btn')) {
    btn.addEventListener('click', () => openLogViewer(btn.dataset.log, btn.closest('.stat-card')));
  }
}

// ── Scan log viewer modal (ADMIN_SPEC.md §8) ─────────────────────────────────
const LOG_TITLES = {
  last_scan: 'Last Scan Log',
  new_files: 'New Files Log',
  changed_files: 'Changed Files Log',
  missing: 'Missing Records Log',
};

async function openLogViewer(logName, cardEl) {
  document.getElementById('logViewerTitle').textContent = LOG_TITLES[logName] || 'Log';
  document.getElementById('logViewerContent').textContent = 'Loading…';
  document.getElementById('logViewerOverlay').hidden = false;

  const d = await apiFetch(`/admin/logs/${logName}`);
  document.getElementById('logViewerContent').textContent =
    d.exists && d.content ? d.content : 'No entries yet.';

  await apiFetch(`/admin/logs/${logName}/mark-viewed`, { method: 'POST' });
  if (cardEl) cardEl.classList.remove('has-pending');
}

function closeLogViewer() {
  document.getElementById('logViewerOverlay').hidden = true;
}

function showScanProgress() {
  const btn  = document.getElementById('scanNowBtn');
  const prog = document.getElementById('scanProgress');
  const card = document.getElementById('scanNowCard');
  if (btn) { btn.disabled = true; btn.textContent = 'Scanning…'; }
  if (prog) prog.hidden = false;
  if (card) card.classList.add('is-scanning');
}

function resetScanButton() {
  const btn  = document.getElementById('scanNowBtn');
  const card = document.getElementById('scanNowCard');
  if (btn)  { btn.disabled = false; btn.textContent = 'Scan Now'; }
  if (card) card.classList.remove('is-scanning');
}

function showNoLibraryModal() {
  showPtSummary('No Library Configured',
    'No library setup - setup new library in Library Management > Library Folders > Scan Roots.', []);
}

async function doScan() {
  if (!_config.library_roots || _config.library_roots.length === 0) {
    showNoLibraryModal();
    return;
  }
  showScanProgress();
  try {
    const d = await apiFetch(`/scan`, { method: 'POST' });
    if (d.running) {
      startScanPoll();
    } else {
      resetScanButton();
      showNoLibraryModal();
    }
  } catch (e) {
    resetScanButton();
    showToast('Failed to start scan: ' + e.message, true);
  }
}

async function doCleanup() {
  const btn     = document.getElementById('cleanupBtn');
  const countEl = document.getElementById('missingCountVal');
  const result  = document.getElementById('cleanupResult');
  const card    = document.getElementById('missingRecordsCard');
  btn.disabled = true;
  btn.textContent = 'Cleaning…';
  try {
    const d = await apiFetch(`/admin/cleanup-missing`, { method: 'POST' });
    if (countEl) countEl.textContent = '0';
    if (result)  result.textContent = `${d.removed} record${d.removed !== 1 ? 's' : ''} removed`;
    if (card)    card.classList.remove('has-pending');
    showToast(`Removed ${d.removed} missing record${d.removed !== 1 ? 's' : ''}`);
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
    const d = await apiFetch(`/scan/status`);
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
  const card   = document.getElementById('scanNowCard');

  if (!btn) return;

  if (state.running) {
    btn.disabled = true;
    btn.textContent = 'Scanning…';
    if (prog) prog.hidden = false;
    if (card) card.classList.add('is-scanning');

    const pct = state.total_files > 0
      ? Math.round((state.processed_files / state.total_files) * 100)
      : 0;
    if (barEl) barEl.style.width = `${pct}%`;
    if (textEl) textEl.textContent = `${state.processed_files} / ${state.total_files}`;
  } else {
    btn.disabled = false;
    btn.textContent = 'Scan Now';
    if (card) card.classList.remove('is-scanning');
    if (barEl) barEl.style.width = '100%';
    if (textEl && state.finished_at) {
      textEl.textContent =
        `Done — ${state.new_files} new, ${state.updated_files} updated, ${state.missing_files} missing`
        + (state.error_files ? `, ${state.error_files} errors` : '');
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
    const d = await apiFetch(`/admin/backup`, { method: 'POST' });
    showToast('Backup saved: ' + d.backup_file);
    await loadStats();
  } catch (e) {
    showToast('Backup failed: ' + (e.body?.detail || e.message || 'Unknown error'), true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Backup Database';
  }
}

// ── Config / Folders ──────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    _config = await apiFetch(`/admin/config`);
  } catch (_) {
    _config = { library_roots: [], scan_exclude: [], library_root: '' };
  }
  renderRoots();
  renderExcludes();
  renderAdvancedFields();

  document.getElementById('autoScanFreqSelect').value = _config.auto_scan_frequency || 'off';
  document.getElementById('scanOnLaunchCheckbox').checked = !!_config.autostart_scan;
  document.getElementById('logSizeLimitInput').value = _config.log_size_limit_mb || 5;
  document.getElementById('serverPortInput').value = _config.reader_port || 8000;
  document.getElementById('backupFolderInput').value = _config.backup_folder || '';
  document.getElementById('backupFreqSelect').value = _config.backup_frequency || 'off';
}

function initScanSettings() {
  document.getElementById('autoScanFreqSelect').addEventListener('change', (e) => {
    patchConfig({ auto_scan_frequency: e.target.value });
  });
  document.getElementById('scanOnLaunchCheckbox').addEventListener('change', (e) => {
    patchConfig({ autostart_scan: e.target.checked });
  });
}

// ── Server Listening Port (ADMIN_SPEC.md §7.3) ──────────────────────────────
function initServerPort() {
  document.getElementById('savePortBtn').addEventListener('click', async () => {
    const port = parseInt(document.getElementById('serverPortInput').value, 10);
    if (!port || port < 1 || port > 65535) {
      showToast('Enter a valid port (1-65535)', true);
      return;
    }
    if (!confirm('This will restart the server and disconnect active users. Continue?')) {
      return;
    }
    try {
      await apiFetch(`/admin/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reader_port: port }),
      });
      await apiFetch(`/admin/restart`, { method: 'POST' });
      showToast(`Restarting on port ${port}…`);
      setTimeout(() => { window.location.href = `http://${location.hostname}:${port}/admin`; }, 4000);
    } catch (e) {
      showToast('Failed to change port: ' + e.message, true);
    }
  });
}

// ── Scheduled Database Backup (ADMIN_SPEC.md §9) ────────────────────────────
function initBackupSettings() {
  document.getElementById('browseBackupFolderBtn').addEventListener('click', async () => {
    let d;
    try {
      d = await apiFetch(`/admin/browse-folder-dialog`, { method: 'POST' });
    } catch (_) {
      showToast('Folder browsing requires a local session', true);
      return;
    }
    if (!d.path) return; // dialog cancelled
    document.getElementById('backupFolderInput').value = d.path;
    patchConfig({ backup_folder: d.path });
  });

  document.getElementById('backupFreqSelect').addEventListener('change', (e) => {
    patchConfig({ backup_frequency: e.target.value });
  });

  document.getElementById('browseRestoreFileBtn').addEventListener('click', async () => {
    let d;
    try {
      d = await apiFetch(`/admin/browse-backup-file-dialog`, { method: 'POST' });
    } catch (_) {
      showToast('Local access required', true);
      return;
    }
    if (!d.path) return; // dialog cancelled
    document.getElementById('restoreFileInput').value = d.path;
  });

  document.getElementById('restoreBtn').addEventListener('click', doRestore);
}

// ── Restore Database (ADMIN_SPEC.md §9, Restore Database — V2.3 Item 12) ───
async function doRestore() {
  const path = document.getElementById('restoreFileInput').value;
  if (!path) {
    showToast('Choose a backup file first', true);
    return;
  }
  const filename = path.split(/[\\/]/).pop();
  const ok = confirm(
    `Restore database from "${filename}"?\n\nThis replaces your ENTIRE database — ` +
    `including Custom Tabs and Home Page Strips — and restarts the server. A ` +
    `safety snapshot of the current database is taken automatically first.`
  );
  if (!ok) return;

  const btn = document.getElementById('restoreBtn');
  btn.disabled = true;
  btn.textContent = 'Restoring…';
  try {
    await apiFetch(`/admin/restore-database`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_path: path }),
    });
    showToast('Database restored — restarting…');
    setTimeout(() => { window.location.reload(); }, 4000);
  } catch (e) {
    showToast(e.status
      ? (e.body?.detail?.error === 'local_access_required' ? 'Local access required' : (e.body?.detail || 'Restore failed'))
      : 'Restore failed: ' + e.message, true);
    btn.disabled = false;
    btn.textContent = 'Restore Database';
  }
}

// ── Danger Zone (ADMIN_SPEC.md §7.4 / §7.5) ─────────────────────────────────
function initDangerZone() {
  document.getElementById('clearProgressBtn').addEventListener('click', clearReadingProgress);
  document.getElementById('clearDbBtn').addEventListener('click', clearDatabase);
}

async function clearReadingProgress() {
  if (!confirm(
    'Clear all reading progress?\n\nThis resets every issue to unread and erases ' +
    'all saved page positions for your entire library. Issue metadata and comic ' +
    'files are not affected. This cannot be undone.'
  )) return;

  try {
    const d = await apiFetch(`/admin/clear-reading-progress`, { method: 'POST' });
    showToast(`Cleared reading progress for ${d.removed} issue(s)`);
    await loadStats();
  } catch (e) {
    showToast(e.body?.detail?.error === 'local_access_required' ? 'Local access required' : 'Clear failed', true);
  }
}

async function clearDatabase() {
  if (!confirm(
    'Clear the entire database?\n\nThis permanently deletes all issues, genres, ' +
    'credits, and reading progress — your whole library record — and also ' +
    'clears cached thumbnails and resets the scan logs, then restarts the ' +
    'server. Comic files on disk are not touched; re-scanning will re-import ' +
    'them as new entries with blank metadata. Custom Tabs and Home Page Strips ' +
    'are configuration and will NOT be affected. Consider using Backup Database ' +
    'first. This cannot be undone.'
  )) return;

  const btn = document.getElementById('clearDbBtn');
  btn.disabled = true;
  btn.textContent = 'Clearing…';
  try {
    const d = await apiFetch(`/admin/clear-database`, { method: 'POST' });
    showToast(`Cleared ${d.issues_removed} issue(s), ${d.thumbnails_removed} thumbnail(s) — restarting…`);
    setTimeout(() => { window.location.reload(); }, 4000);
  } catch (e) {
    showToast(e.status
      ? (e.body?.detail?.error === 'local_access_required' ? 'Local access required' : (e.body?.detail || 'Clear failed'))
      : 'Clear failed: ' + e.message, true);
    btn.disabled = false;
    btn.textContent = 'Clear Database';
  }
}

// ── Password Recovery (ADMIN_SPEC.md §7.1.7) ────────────────────────────────
function initPasswordRecovery() {
  document.getElementById('passwordRecoveryBtn').addEventListener('click', () => {
    document.getElementById('pwRecoveryOverlay').hidden = false;
  });
  document.getElementById('pwRecoveryCloseBtn').addEventListener('click', () => {
    document.getElementById('pwRecoveryOverlay').hidden = true;
  });
  document.getElementById('pwRecoveryOverlay').addEventListener('click', (e) => {
    if (e.target.id === 'pwRecoveryOverlay') document.getElementById('pwRecoveryOverlay').hidden = true;
  });
}

async function initLogsSection() {
  const d = await apiFetch(`/admin/logs/folder-path`);
  document.getElementById('logsFolderPathInput').value = d.path;

  document.getElementById('openLogsFolderBtn').addEventListener('click', async () => {
    try {
      await apiFetch(`/admin/logs/open-folder`, { method: 'POST' });
    } catch (e) {
      showToast('Failed to open folder: ' + (e.body?.detail?.error || e.message), true);
    }
  });

  document.getElementById('saveLogSizeLimitBtn').addEventListener('click', () => {
    const val = parseInt(document.getElementById('logSizeLimitInput').value, 10);
    if (!val || val < 1) {
      showToast('Enter a valid size in MB', true);
      return;
    }
    patchConfig({ log_size_limit_mb: val });
  });
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
    await apiFetch(`/admin/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    showToast('Saved');
  } catch (e) {
    showToast('Save failed: ' + (e.body?.detail || e.message), true);
  }
}

function addRoot() {
  const input = document.getElementById('newRootInput');
  const val   = input.value.trim();
  if (!val || _config.library_roots.includes(val)) { input.value = ''; document.getElementById('addRootBtn').classList.remove('is-ready'); return; }
  _config.library_roots = [..._config.library_roots, val];
  renderRoots();
  patchConfig({ library_roots: _config.library_roots });
  input.value = '';
  document.getElementById('addRootBtn').classList.remove('is-ready');
}

function removeRoot(path) {
  _config.library_roots = _config.library_roots.filter(r => r !== path);
  renderRoots();
  patchConfig({ library_roots: _config.library_roots });
}

function addExclude() {
  const input = document.getElementById('newExcludeInput');
  const val   = input.value.trim();
  if (!val || _config.scan_exclude.includes(val)) { input.value = ''; document.getElementById('addExcludeBtn').classList.remove('is-ready'); return; }
  _config.scan_exclude = [..._config.scan_exclude, val];
  renderExcludes();
  patchConfig({ scan_exclude: _config.scan_exclude });
  input.value = '';
  document.getElementById('addExcludeBtn').classList.remove('is-ready');
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

// ── Card size ─────────────────────────────────────────────────────────────────
function initCardSize() {
  const sel   = document.getElementById('cardSizeSelect');
  const stored = localStorage.getItem('cv_card_size');
  // A value saved before the 10%/25%/75% options were removed won't match
  // any <option> here — fall back to the default rather than leaving the
  // select blank.
  const saved = sel.querySelector(`option[value="${stored}"]`) ? stored : '30';
  sel.value   = saved;
  sel.addEventListener('change', () => {
    localStorage.setItem('cv_card_size', sel.value);
    showToast(`Card size set to ${sel.value}%`);
  });
}

// ── Theme (SPEC.md §20.17) — "auto" means no override; let the
// prefers-color-scheme CSS media query decide, same as if nothing were ever
// chosen. Explicit light/dark sets data-theme on <html>, mirrored by the
// anti-flash inline script each page's <head> runs on load. ───────────────────
function initTheme() {
  const sel   = document.getElementById('themeSelect');
  const saved = localStorage.getItem('cv_theme') || 'auto';
  sel.value   = saved;
  sel.addEventListener('change', () => {
    localStorage.setItem('cv_theme', sel.value);
    if (sel.value === 'auto') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = sel.value;
    showToast(sel.value === 'auto' ? 'Theme set to match Windows' : `Theme set to ${sel.value}`);
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
let customTabs  = [];
let ctPickerPath = null;
let ctPickerRoots = [];

async function loadCustomTabs() {
  try {
    customTabs = await apiFetch(`/admin/custom-tabs`);
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

  const hasFavouritesTab = customTabs.some(t => t.basis_type === 'favorites');
  document.getElementById('ctAddFavouritesBtn').disabled = hasFavouritesTab;

  const hasReadingQueueTab = customTabs.some(t => t.basis_type === 'reading_queue');
  document.getElementById('ctAddReadingQueueBtn').disabled = hasReadingQueueTab;

  renderCtGenreOptions();
  renderCtWriterOptions();
  renderCtPublisherOptions();
}

// ── Genre Library (CUSTOM_TABS_SPEC.md §10.9) ───────────────────────────────
let ctAllGenres = []; // cached from /browse/genres: [{genre, issue_count}, ...]

async function loadCtGenreOptions() {
  try {
    ctAllGenres = await apiFetch(`/browse/genres`);
  } catch (_) {
    ctAllGenres = [];
  }
  renderCtGenreOptions();
}

function renderCtGenreOptions() {
  const select = document.getElementById('ctGenreSelect');
  if (!select) return;
  const usedGenres = new Set(
    customTabs.filter(t => t.basis_type === 'genre').map(t => t.field_value)
  );
  const prevValue = select.value;
  select.innerHTML = '';
  select.add(new Option('Genre…', ''));
  for (const g of ctAllGenres) {
    if (usedGenres.has(g.genre)) continue;
    select.add(new Option(g.genre, g.genre));
  }
  select.value = usedGenres.has(prevValue) ? '' : prevValue;
}

async function addGenreTab() {
  const select = document.getElementById('ctGenreSelect');
  const genre = select.value;
  if (!genre) {
    showToast('Choose a genre first', true);
    return;
  }
  try {
    await apiFetch(`/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ basis_type: 'genre', field_value: genre }),
    });
    showToast(`Genre Library "${genre}" added`);
    select.value = '';
    // Re-fetch the genre list itself (not just re-render from the cached
    // ctAllGenres) — guarantees the dropdown repopulates correctly even if
    // the page-load fetch was still in flight when this add happened,
    // instead of leaving it empty until a hard refresh.
    await Promise.all([loadCustomTabs(), loadCtGenreOptions()]);
  } catch (e) {
    showToast(e.body?.detail || 'Could not add Genre Library: ' + e.message, true);
  }
}

// ── Writer Library (CUSTOM_TABS_SPEC.md §10.12) ─────────────────────────────
let ctAllWriters = []; // cached from /browse/writers: [{person_id, name, series_count}, ...]

async function loadCtWriterOptions() {
  try {
    ctAllWriters = await apiFetch(`/browse/writers`);
  } catch (_) {
    ctAllWriters = [];
  }
  renderCtWriterOptions();
}

function renderCtWriterOptions() {
  const select = document.getElementById('ctWriterSelect');
  if (!select) return;
  const usedWriters = new Set(
    customTabs.filter(t => t.basis_type === 'writer').map(t => t.field_value)
  );
  const prevValue = select.value;
  select.innerHTML = '';
  select.add(new Option('Writer…', ''));
  for (const w of ctAllWriters) {
    const personId = String(w.person_id);
    if (usedWriters.has(personId)) continue;
    select.add(new Option(w.name, personId));
  }
  select.value = usedWriters.has(prevValue) ? '' : prevValue;
}

async function addWriterTab() {
  const select = document.getElementById('ctWriterSelect');
  const personId = select.value;
  if (!personId) {
    showToast('Choose a writer first', true);
    return;
  }
  const writerName = select.options[select.selectedIndex].textContent;
  try {
    await apiFetch(`/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ basis_type: 'writer', field_value: personId }),
    });
    showToast(`Writer Library "${writerName}" added`);
    select.value = '';
    await Promise.all([loadCustomTabs(), loadCtWriterOptions()]);
  } catch (e) {
    showToast(e.body?.detail || 'Could not add Writer Library: ' + e.message, true);
  }
}

// ── Publisher Library (CUSTOM_TABS_SPEC.md §10.11) ──────────────────────────
let ctAllPublishers = []; // cached from /browse/publishers: [{publisher, series_count}, ...]

async function loadCtPublisherOptions() {
  try {
    ctAllPublishers = await apiFetch(`/browse/publishers`);
  } catch (_) {
    ctAllPublishers = [];
  }
  renderCtPublisherOptions();
}

function renderCtPublisherOptions() {
  const select = document.getElementById('ctPublisherSelect');
  if (!select) return;
  const usedPublishers = new Set(
    customTabs.filter(t => t.basis_type === 'publisher').map(t => t.field_value)
  );
  const prevValue = select.value;
  select.innerHTML = '';
  select.add(new Option('Publisher…', ''));
  for (const p of ctAllPublishers) {
    if (usedPublishers.has(p.publisher)) continue;
    select.add(new Option(p.publisher, p.publisher));
  }
  select.value = usedPublishers.has(prevValue) ? '' : prevValue;
}

async function addPublisherTab() {
  const select = document.getElementById('ctPublisherSelect');
  const publisher = select.value;
  if (!publisher) {
    showToast('Choose a publisher first', true);
    return;
  }
  try {
    await apiFetch(`/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ basis_type: 'publisher', field_value: publisher }),
    });
    showToast(`Publisher Library "${publisher}" added`);
    select.value = '';
    await Promise.all([loadCustomTabs(), loadCtPublisherOptions()]);
  } catch (e) {
    showToast(e.body?.detail || 'Could not add Publisher Library: ' + e.message, true);
  }
}

function makeCustomTabRow(tab) {
  const row = document.createElement('div');
  row.className = 'ct-tab-row';
  const isFavourites = tab.basis_type === 'favorites';
  const isGenre = tab.basis_type === 'genre';
  const isReadingQueue = tab.basis_type === 'reading_queue';
  const isWriter = tab.basis_type === 'writer';
  const isPublisher = tab.basis_type === 'publisher';

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
  pathLine.textContent = isFavourites
    ? 'Library-wide (Favourites)'
    : isReadingQueue
      ? 'Library-wide (Reading Queue)'
      : isGenre
        ? `Genre: ${tab.field_value}`
        : isPublisher
          ? `Publisher: ${tab.field_value}`
          : isWriter
            ? `Writer: ${tab.name}`
            : tab.folder_path;
  info.append(nameLine, pathLine);

  const viewModeSelect = document.createElement('select');
  viewModeSelect.className = 'ct-viewmode-select admin-select';
  viewModeSelect.innerHTML = '<option value="flat">Flat</option><option value="folder">Folder View</option>';
  viewModeSelect.value = tab.view_mode || 'flat';
  viewModeSelect.disabled = isFavourites || isGenre || isReadingQueue || isWriter || isPublisher;
  viewModeSelect.addEventListener('change', () => updateCustomTabViewMode(tab, viewModeSelect.value));

  const toggleBtn = document.createElement('button');
  toggleBtn.className = `ct-visible-toggle${tab.visible ? ' is-visible' : ''}`;
  toggleBtn.textContent = tab.visible ? 'Visible' : 'Hidden';
  toggleBtn.dataset.tooltip = 'Show or hide this library in the sidebar';
  toggleBtn.addEventListener('click', () => toggleCustomTabVisible(tab));

  const delBtn = document.createElement('button');
  delBtn.className = 'folder-remove-btn';
  delBtn.textContent = 'Delete';
  delBtn.dataset.tooltip = 'Removes this tab definition only — comic files and library data are untouched';
  delBtn.addEventListener('click', () => deleteCustomTab(tab));

  row.append(info, viewModeSelect, toggleBtn, delBtn);
  return row;
}

async function updateCustomTabViewMode(tab, view_mode) {
  try {
    await apiFetch(`/admin/custom-tabs/${tab.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ view_mode }),
    });
    showToast(`View mode set to ${view_mode === 'folder' ? 'Folder View' : 'Flat'}`);
    await loadCustomTabs();
  } catch (e) {
    showToast(e.body?.detail || 'Could not update view mode: ' + e.message, true);
  }
}

async function toggleCustomTabVisible(tab) {
  try {
    await apiFetch(`/admin/custom-tabs/${tab.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible: !tab.visible }),
    });
    await loadCustomTabs();
  } catch (e) {
    showToast(e.body?.detail || 'Could not update tab: ' + e.message, true);
  }
}

async function deleteCustomTab(tab) {
  const ok = confirm(
    `Delete tab "${tab.name}"?\n\n` +
    `This only removes the tab definition — it will not touch any comic files or library data.`
  );
  if (!ok) return;
  try {
    await apiFetch(`/admin/custom-tabs/${tab.id}`, { method: 'DELETE' });
    showToast('Tab deleted');
    await loadCustomTabs();
  } catch (e) {
    showToast(e.body?.detail || 'Delete failed: ' + e.message, true);
  }
}

async function addCustomTab() {
  const nameInput = document.getElementById('ctNameInput');
  const pathInput = document.getElementById('ctPathInput');
  const viewModeSelect = document.getElementById('ctViewModeSelect');
  const name = nameInput.value.trim();
  const folder_path = pathInput.value.trim();
  const view_mode = viewModeSelect.value || 'flat';
  if (!name || !folder_path) {
    showToast('Name and folder path are both required', true);
    return;
  }
  try {
    const d = await apiFetch(`/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, folder_path, view_mode }),
    });
    if (d.warning) showToast(d.warning, true);
    else showToast('Tab added');
    nameInput.value = '';
    pathInput.value = '';
    viewModeSelect.value = 'flat';
    await loadCustomTabs();
  } catch (e) {
    showToast(e.body?.detail || 'Could not add tab: ' + e.message, true);
  }
}

async function addFavouritesTab() {
  try {
    await apiFetch(`/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ basis_type: 'favorites' }),
    });
    showToast('Favourites tab added');
    await loadCustomTabs();
  } catch (e) {
    showToast(e.body?.detail || 'Could not add Favourites tab: ' + e.message, true);
  }
}

async function addReadingQueueTab() {
  try {
    await apiFetch(`/admin/custom-tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ basis_type: 'reading_queue' }),
    });
    showToast('Reading Queue tab added');
    await loadCustomTabs();
  } catch (e) {
    showToast(e.body?.detail || 'Could not add Reading Queue tab: ' + e.message, true);
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
  const url = path ? `/admin/browse?path=${encodeURIComponent(path)}` : `/admin/browse`;
  try {
    const data = await apiFetch(url);
    ctPickerPath  = data.path;
    ctPickerRoots = data.roots || [];
    renderCtPickerRoots();
    renderCtPickerBreadcrumb(data.path);
    renderCtPickerTree(data.items || []);
  } catch (e) {
    showToast('Could not browse: ' + (e.body?.detail || e.message), true);
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
  const input = document.getElementById(ctPickerTargetInputId);
  input.value = ctPickerPath || '';
  input.dispatchEvent(new Event('input'));
  closeCtPicker();
}

// ── Home Page Strips (HOME_STRIPS_SPEC.md) ──────────────────────────────────────
const MAX_NON_DEFAULT_HOME_STRIPS = 5;
const HS_FIELD_LABELS = {
  genre: 'Genre', publisher: 'Publisher', writer: 'Writer', artist: 'Artist',
  format: 'Format', decade: 'Decade', year: 'Year', rating: 'Rating', bw: 'Black & White',
  reading_queue: 'Reading Queue',
};
// `key` is the dropdown's display label source; `valueKey` (when different
// from `key`) is what actually gets stored as field_value. writer/artist
// store a Person.id (Tier 4 Item 3) but display the person's name.
const HS_FIELD_ENDPOINTS = {
  genre:     { url: '/browse/genres',     key: 'genre' },
  publisher: { url: '/browse/publishers', key: 'publisher' },
  writer:    { url: '/browse/writers',    key: 'name', valueKey: 'person_id' },
  artist:    { url: '/browse/artists',    key: 'name', valueKey: 'person_id' },
  format:    { url: '/browse/formats',    key: 'format' },
  decade:    { url: '/browse/decades',    key: 'decade' },
  year:      { url: '/browse/years',      key: 'year' },
  rating:    { url: '/browse/ratings',    key: 'rating' },
};
let homeStrips = [];

// Writer/Artist field strips store a Person.id as field_value (Tier 4 Item 3)
// — this resolves it back to a display name for hsBasisSummary(). Only
// fetched if a strip actually needs it (cheap today since no real strip
// uses writer/artist yet, but no reason to fetch ~4,000 names otherwise).
let hsPersonNameCache = null;  // {writer: {id: name}, artist: {id: name}}

async function ensureHsPersonNameCache() {
  if (hsPersonNameCache) return hsPersonNameCache;
  hsPersonNameCache = { writer: {}, artist: {} };
  try {
    const [writers, artists] = await Promise.all([
      apiFetch(`/browse/writers`),
      apiFetch(`/browse/artists`),
    ]);
    for (const w of writers) hsPersonNameCache.writer[w.person_id] = w.name;
    for (const a of artists) hsPersonNameCache.artist[a.person_id] = a.name;
  } catch (_) {
    // Leave cache empty — hsBasisSummary falls back to showing the raw id.
  }
  return hsPersonNameCache;
}

async function loadHomeStrips() {
  try {
    homeStrips = await apiFetch(`/admin/home-strips`);
  } catch (_) {
    homeStrips = [];
  }
  const needsPersonNames = homeStrips.some(s => s.field_name === 'writer' || s.field_name === 'artist');
  if (needsPersonNames) await ensureHsPersonNameCache();
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
  if (strip.basis_type === 'builtin') return 'default';
  if (strip.basis_type === 'field') {
    const label = HS_FIELD_LABELS[strip.field_name] || strip.field_name;
    if (strip.field_name === 'reading_queue') return label;
    // writer/artist field_value is a Person.id (Tier 4 Item 3) — show the
    // name if the cache has loaded it, otherwise fall back to the raw id.
    let value = strip.field_value;
    if (strip.field_name === 'writer' || strip.field_name === 'artist') {
      const name = hsPersonNameCache && hsPersonNameCache[strip.field_name][strip.field_value];
      value = name || `#${strip.field_value}`;
    }
    return `${label}: ${value}`;
  }
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
  upBtn.dataset.tooltip = 'Move this strip up';
  upBtn.addEventListener('click', () => moveHomeStrip(strip, -1));
  const downBtn = document.createElement('button');
  downBtn.type = 'button';
  downBtn.className = 'hs-arrow-btn';
  downBtn.textContent = '▼';
  downBtn.disabled = isLast;
  downBtn.dataset.tooltip = 'Move this strip down';
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
    badge.dataset.tooltip = 'Default strips can be reordered but not edited or removed';
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
    await apiFetch(`/admin/home-strips/reorder`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    await loadHomeStrips();
  } catch (e) {
    showToast(e.body?.detail || 'Reorder failed: ' + e.message, true);
  }
}

async function toggleHomeStripVisible(strip) {
  try {
    await apiFetch(`/admin/home-strips/${strip.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible: !strip.visible }),
    });
    await loadHomeStrips();
  } catch (e) {
    showToast(e.body?.detail || 'Could not update strip: ' + e.message, true);
  }
}

async function deleteHomeStrip(strip) {
  const ok = confirm(
    `Delete strip "${strip.name}"?\n\n` +
    `This only removes the strip definition — it will not touch any comic files or library data.`
  );
  if (!ok) return;
  try {
    await apiFetch(`/admin/home-strips/${strip.id}`, { method: 'DELETE' });
    showToast('Strip deleted');
    await loadHomeStrips();
  } catch (e) {
    showToast(e.body?.detail || 'Delete failed: ' + e.message, true);
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
  valueSelect.disabled = false;
  if (!fieldName) return;

  if (fieldName === 'reading_queue') {
    valueSelect.disabled = true;
    return;
  }

  if (fieldName === 'bw') {
    valueSelect.add(new Option('Yes', 'yes'));
    valueSelect.add(new Option('No', 'no'));
    return;
  }

  const endpoint = HS_FIELD_ENDPOINTS[fieldName];
  if (!endpoint) return;
  try {
    const rows = await apiFetch(endpoint.url);
    for (const row of rows) {
      const label = String(row[endpoint.key]);
      const val   = String(row[endpoint.valueKey || endpoint.key]);
      valueSelect.add(new Option(label, val));
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
    if (!payload.field_name || (payload.field_name !== 'reading_queue' && !payload.field_value)) {
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
    const d = await apiFetch(`/admin/home-strips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (d.warning) showToast(d.warning, true);
    else showToast('Strip added');
    nameInput.value = '';
    document.getElementById('hsFolderInput').value = '';
    document.getElementById('hsFieldNameSelect').value = '';
    document.getElementById('hsFieldValueSelect').innerHTML = '<option value="">Value…</option>';
    await loadHomeStrips();
  } catch (e) {
    showToast(e.body?.detail || 'Could not add strip: ' + e.message, true);
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
    names = await apiFetch(`/editor/${kind}`);
  } catch (_) {
    names = [];
  }
  try {
    const rows = await apiFetch(`/browse/${kind}`);
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
    delBtn.dataset.tooltip = items.length <= 1
      ? 'At least one value must remain'
      : 'Remove from the list — issues keep their current value';
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
    await apiFetch(`/editor/${kind}/${encodeURIComponent(name)}`, { method: 'DELETE' });
    showToast(`${label[0].toUpperCase()}${label.slice(1)} removed`);
    await (kind === 'genres' ? loadGenreList() : loadFormatList());
  } catch (e) {
    showToast(e.body?.detail || 'Delete failed: ' + e.message, true);
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
    await apiFetch(`/editor/${kind}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    showToast(`${label} added`);
    input.value = '';
    await (kind === 'genres' ? loadGenreList() : loadFormatList());
  } catch (e) {
    showToast(e.body?.detail || `Could not add ${label.toLowerCase()}: ` + e.message, true);
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

// ── Password Protection + Remote Administration (ADMIN_SPEC.md §7.1 / §7.2) ────

async function initAuthSettings() {
  const protectionToggle = document.getElementById('authProtectionToggle');
  const passwordFields = document.getElementById('authPasswordFields');
  const remoteToggle = document.getElementById('authRemoteToggle');
  const saveBtn = document.getElementById('authSaveBtn');

  await refreshAuthSettingsUi();

  const disableConfirmRow = document.getElementById('authDisableConfirmRow');

  protectionToggle.addEventListener('change', () => {
    passwordFields.hidden = !protectionToggle.checked;
    document.getElementById('authError').hidden = true;
    if (!protectionToggle.checked) {
      // Turning protection off requires re-entering the current password
      // (it also force-disables Remote Administration in the same action).
      protectionToggle.checked = true;
      passwordFields.hidden = true;
      document.getElementById('authDisableCurrentPassword').value = '';
      document.getElementById('authDisableError').hidden = true;
      disableConfirmRow.hidden = false;
    }
  });

  saveBtn.addEventListener('click', enableProtection);

  document.getElementById('authDisableCancelBtn').addEventListener('click', () => {
    disableConfirmRow.hidden = true;
  });
  document.getElementById('authDisableConfirmBtn').addEventListener('click', disableProtection);

  remoteToggle.addEventListener('change', async () => {
    try {
      await apiFetch(`/admin/auth/remote-toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: remoteToggle.checked }),
      });
    } catch (_) {
      remoteToggle.checked = !remoteToggle.checked;
      showToast('Could not update Remote Administration', true);
      return;
    }
    showToast(remoteToggle.checked ? 'Remote Administration enabled' : 'Remote Administration disabled');
  });

  document.getElementById('passwordResetBtn').addEventListener('click', openPwResetModal);
  document.getElementById('pwResetCloseBtn').addEventListener('click', closePwResetModal);
  document.getElementById('pwResetCancelBtn').addEventListener('click', closePwResetModal);
  document.getElementById('pwResetForm').addEventListener('submit', submitPwReset);
}

async function refreshAuthSettingsUi() {
  const status = await apiFetch(`/admin/auth/status`);

  document.getElementById('authProtectionToggle').checked = status.protection_enabled;
  document.getElementById('authPasswordFields').hidden = true;
  document.getElementById('authDisableConfirmRow').hidden = true;
  document.getElementById('authRemoteToggle').checked = status.remote_admin_enabled;
  document.getElementById('authRemoteToggle').disabled = !status.protection_enabled;

  // Local-only enforcement (ADMIN_SPEC.md §7.1.1) — these controls are only ever
  // submittable from a 127.0.0.1 session, even when advancedLock is unchecked.
  const localOnlyHint = document.getElementById('authLocalOnlyHint');
  const remoteLabel = document.getElementById('authRemoteLabel');
  if (!status.is_local) {
    localOnlyHint.hidden = false;
    document.getElementById('authProtectionToggle').disabled = true;
    document.getElementById('authSaveBtn').disabled = true;
    remoteLabel.querySelector('input').disabled = true;
    document.getElementById('passwordResetBtn').disabled = true;
  } else {
    localOnlyHint.hidden = true;
    document.getElementById('authProtectionToggle').disabled = false;
    document.getElementById('authSaveBtn').disabled = false;
    remoteLabel.querySelector('input').disabled = !status.protection_enabled;
    document.getElementById('passwordResetBtn').disabled = false;
  }

  // Processing Tools (§12 shared notes) — local-only regardless of
  // protection/remote-admin state, same tier as the controls above.
  if (typeof refreshProcessingToolsLocalGate === 'function') {
    refreshProcessingToolsLocalGate(status.is_local);
  }
}

async function enableProtection() {
  const errorBox = document.getElementById('authError');
  errorBox.hidden = true;
  const pw = document.getElementById('authNewPassword').value;
  const confirmPw = document.getElementById('authConfirmPassword').value;

  if (!pw || pw !== confirmPw) {
    errorBox.hidden = false;
    errorBox.textContent = 'Passwords do not match (or are empty).';
    return;
  }

  try {
    await apiFetch(`/admin/auth/enable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pw }),
    });
  } catch (_) {
    errorBox.hidden = false;
    errorBox.textContent = 'Could not enable password protection.';
    return;
  }
  document.getElementById('authNewPassword').value = '';
  document.getElementById('authConfirmPassword').value = '';
  showToast('Password protection enabled');
  await refreshAuthSettingsUi();
}

async function disableProtection() {
  const errorBox = document.getElementById('authDisableError');
  const current_password = document.getElementById('authDisableCurrentPassword').value;
  errorBox.hidden = true;

  try {
    await apiFetch(`/admin/auth/disable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password }),
    });
  } catch (_) {
    errorBox.hidden = false;
    errorBox.textContent = 'Incorrect password.';
    return;
  }
  document.getElementById('authDisableConfirmRow').hidden = true;
  showToast('Password protection disabled');
  await refreshAuthSettingsUi();
}

function openPwResetModal() {
  document.getElementById('pwResetError').hidden = true;
  document.getElementById('pwResetCurrent').value = '';
  document.getElementById('pwResetNew').value = '';
  document.getElementById('pwResetOverlay').hidden = false;
}

function closePwResetModal() {
  document.getElementById('pwResetOverlay').hidden = true;
}

async function submitPwReset(e) {
  e.preventDefault();
  const errorBox = document.getElementById('pwResetError');
  errorBox.hidden = true;

  const current_password = document.getElementById('pwResetCurrent').value;
  const new_password = document.getElementById('pwResetNew').value;

  try {
    await apiFetch(`/admin/auth/change-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password, new_password }),
    });
  } catch (_) {
    errorBox.hidden = false;
    errorBox.textContent = 'Current password incorrect, or local access required.';
    return;
  }
  closePwResetModal();
  showToast('Password changed');
}

// ── PWA Install button ────────────────────────────────────────────────────────
// Hidden by default. Shown when the browser fires beforeinstallprompt
// (captured in pwa.js). Hidden again once installed or if already running
// as a standalone PWA.

function initPWAInstall() {
  const btn = document.getElementById('pwaInstallBtn');
  if (!btn) return;

  // Already running as installed PWA — nothing to offer
  if (window.matchMedia('(display-mode: standalone)').matches) return;

  btn.addEventListener('click', () => {
    window.triggerPWAInstall && window.triggerPWAInstall();
  });

  document.addEventListener('pwa-installable', () => {
    btn.hidden = false;
  });

  document.addEventListener('pwa-installed', () => {
    btn.hidden = true;
  });
}
