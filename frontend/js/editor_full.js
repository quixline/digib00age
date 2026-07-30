// ComicVault — editor_full.js
// Full Editor toolbox: pre-library batch metadata editing. EDITOR_SPEC.md Section 5.
// Self-contained — no dependency on app.js.
// v2.6 Item 7 — 4-column redesign: Col 1 folder→series→issue tree, Col 2 editor
// with genre chips + apply-to-all column, Col 3 viewer (Fit/Fullscreen/lazy thumb
// strip), Col 4 queue cards, plus a footer status bar. Backend endpoints unchanged.

const AGE_RATING_OPTIONS = [
  'Everyone', 'Early Childhood', 'Everyone 10+', 'PG', 'Adult', 'Teen', 'Teen+', 'Mature',
];

// ── State ────────────────────────────────────────────────────────────────────
let loadedFiles = [];        // [{id, filename, path, xml_files, needs_review}]
let queueFiles = [];         // [{id, filename, path, xml_files, queued_fields}]
let focusedFileId = null;

let genreOptions = [];       // full genre list (editable, from /api/editor/genres)
let selectedGenres = [];     // chips currently on the form

let treeCollapsed = new Set(); // tree nodes the user has collapsed (default: expanded)

let pickerPath = null;
let pickerSelected = new Map(); // path -> 'file' | 'folder'

let viewerFileId = null;
let viewerImageList = [];
let viewerPageNum = 0;
let viewerZoom = 1;
let thumbCache = new Map();   // `${fileId}:${n}` -> data URI (lazy strip)

let multiXmlFileId = null;

// Search Online (EDITOR_SPEC.md §9)
let searchOnlineOpen = false;   // focus trap — blocks card-swap/Process while the modal is open
let soSeriesResults = [];       // cached Step 1 results, so "Back to Series" doesn't re-fetch
let soSelectedSeriesId = null;
let soSelectedSeries = null;    // full series object of the highlighted row (set by previewSoSeries)
let soSelectedIssueId = null;   // issue ID of the currently selected issue (set by previewSoIssue)
let soSortKey = '';             // '' (relevance order, as returned by ComicVine) | name | start_year | count_of_issues | publisher
let soSortDir = 'asc';

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  populateStaticSelects();
  await loadGenreOptions();
  await loadFormatOptions();
  wireFileManagement();
  wireQueue();
  wireXmlEditor();
  wireImageViewer();
  wirePicker();
  wireMultiXmlModal();
  wireProcessErrorModal();
  wireSearchOnlineModal();

  await refreshFileList();
  await refreshQueueList();
});

function populateStaticSelects() {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const optionsHtml = (values, placeholder) => {
    let html = `<option value="">${esc(placeholder)}</option>`;
    for (const v of values) html += `<option value="${esc(v)}">${esc(v)}</option>`;
    return html;
  };
  document.getElementById('fe-agerating').innerHTML = optionsHtml(AGE_RATING_OPTIONS, '-- Select Rating --');
}

async function loadFormatOptions() {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const formats = await fetch('/api/editor/formats').then((r) => r.json());
  let html = `<option value="">-- Select Format --</option>`;
  for (const v of formats) html += `<option value="${esc(v)}">${esc(v)}</option>`;
  document.getElementById('fe-format').innerHTML = html;
}

// ── Genre chips (Col 2) ──────────────────────────────────────────────────────
// Replaces the old checkbox grid (EDITOR_SPEC.md §5.2). The full editable genre
// list still comes from /api/editor/genres; chips hold the current selection and
// the "＋ Add genre" dropdown offers only genres not yet chosen.
async function loadGenreOptions() {
  genreOptions = await fetch('/api/editor/genres').then((r) => r.json());
  renderGenreChips();
}

function renderGenreAddDropdown() {
  const sel = document.getElementById('fe-genre-add');
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  const available = genreOptions.filter((g) => !selectedGenres.includes(g));
  let html = '<option value="">＋ Add genre</option>';
  for (const g of available) html += `<option value="${esc(g)}">${esc(g)}</option>`;
  sel.innerHTML = html;
  sel.value = '';
}

function renderGenreChips() {
  const wrap = document.getElementById('fe-genre-chips');
  wrap.innerHTML = '';
  for (const g of selectedGenres) {
    const chip = document.createElement('span');
    chip.className = 'fe-genre-chip';
    chip.appendChild(document.createTextNode(g));
    const x = document.createElement('button');
    x.type = 'button';
    x.className = 'fe-genre-chip-x';
    x.textContent = '✕';
    x.setAttribute('aria-label', `Remove ${g}`);
    x.dataset.tooltip = 'Remove this genre';
    x.onclick = () => removeGenre(g);
    chip.appendChild(x);
    wrap.appendChild(chip);
  }
  renderGenreAddDropdown();
  updateActionButtonStates();
}

function addGenre(name) {
  if (!name) return;
  if (!selectedGenres.includes(name)) {
    selectedGenres.push(name);
    renderGenreChips();
  }
}

function removeGenre(name) {
  selectedGenres = selectedGenres.filter((g) => g !== name);
  renderGenreChips();
}

function setGenres(list) {
  selectedGenres = (list || []).slice();
  renderGenreChips();
}

// ── Natural (alphanumeric) compare for issue ordering (001 < 002 < 010) ──────
function naturalCompare(a, b) {
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
}

// ══════════════════════════════════════════════════════════════════════════════
//  FILE MANAGEMENT (Column 1) — folder → series → issue tree
// ══════════════════════════════════════════════════════════════════════════════

function wireFileManagement() {
  document.getElementById('feSelectFolderBtn').onclick = openPicker;
  document.getElementById('feClearListBtn').onclick = clearFileList;

  const tree = document.getElementById('feFileTree');
  tree.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    if (!loadedFiles.length) return;
    const idx = loadedFiles.findIndex((f) => f.id === focusedFileId);
    let nextIdx;
    if (idx === -1) nextIdx = 0;
    else nextIdx = e.key === 'ArrowDown' ? Math.min(idx + 1, loadedFiles.length - 1) : Math.max(idx - 1, 0);
    focusFile(loadedFiles[nextIdx].id);
  });
}

async function refreshFileList() {
  const res = await fetch('/api/editor/full/files');
  const data = await res.json();
  // Preserve current display order where possible, append new entries
  const known = new Map(loadedFiles.map((f) => [f.id, f]));
  const incoming = new Map(data.files.map((f) => [f.id, f]));
  const ordered = loadedFiles.filter((f) => incoming.has(f.id)).map((f) => incoming.get(f.id));
  for (const f of data.files) {
    if (!known.has(f.id)) ordered.push(f);
  }
  // carry forward lazily-set needs_review flags across the reorder
  for (const f of ordered) {
    if (known.has(f.id) && known.get(f.id).needs_review) f.needs_review = true;
  }
  loadedFiles = ordered;
  renderFileTree();
  updateMismatchIndicator();
  updateActionButtonStates();
}

// Split a Windows/POSIX path into directory segments (excluding the filename).
function pathDirParts(p) {
  const parts = String(p).replace(/\//g, '\\').split('\\').filter(Boolean);
  parts.pop(); // drop filename
  return parts;
}

// Group loaded files by the two directory levels nearest the file:
// grandparent = folder, parent = series. Shallow paths degrade gracefully.
function buildFileTree(files) {
  const folders = new Map(); // folderName -> {name, series:Map, direct:[]}
  const getFolder = (name) => {
    if (!folders.has(name)) folders.set(name, { name, series: new Map(), direct: [] });
    return folders.get(name);
  };

  for (const f of files) {
    const dirs = pathDirParts(f.path);
    let folderName, seriesName;
    if (dirs.length >= 2) {
      folderName = dirs[dirs.length - 2];
      seriesName = dirs[dirs.length - 1];
    } else if (dirs.length === 1) {
      folderName = dirs[0];
      seriesName = null;
    } else {
      folderName = 'Files';
      seriesName = null;
    }
    const folder = getFolder(folderName);
    if (seriesName) {
      if (!folder.series.has(seriesName)) folder.series.set(seriesName, []);
      folder.series.get(seriesName).push(f);
    } else {
      folder.direct.push(f);
    }
  }
  return folders;
}

// Flat file-id order matching the tree's rendered folder→series→issue order
// exactly (natural-sorted series names and issue filenames, independent of
// collapse state). BUG-031: Process All must send file_ids in this order —
// `loadedFiles` itself stays in raw arrival order (os.walk / picker order,
// neither of which is numeric-aware), and increment numbering just walks
// whatever list it's given, so anything using raw `loadedFiles` order
// silently mismatches what's shown in the tree.
function treeOrderedFileIds(files) {
  const folders = buildFileTree(files);
  const ids = [];
  for (const folder of folders.values()) {
    const seriesNames = Array.from(folder.series.keys()).sort(naturalCompare);
    for (const sName of seriesNames) {
      const issues = folder.series.get(sName).slice().sort((a, b) => naturalCompare(a.filename, b.filename));
      for (const iss of issues) ids.push(iss.id);
    }
    const direct = folder.direct.slice().sort((a, b) => naturalCompare(a.filename, b.filename));
    for (const iss of direct) ids.push(iss.id);
  }
  return ids;
}

// Longest common directory prefix across all loaded files (for the path row).
function commonRootPath(files) {
  if (!files.length) return '';
  let common = pathDirParts(files[0].path);
  for (let i = 1; i < files.length; i++) {
    const parts = pathDirParts(files[i].path);
    let n = 0;
    while (n < common.length && n < parts.length && common[n].toLowerCase() === parts[n].toLowerCase()) n++;
    common = common.slice(0, n);
    if (!common.length) break;
  }
  return common.join('\\');
}

function makeIssueRow(entry, depthPad) {
  const row = document.createElement('div');
  row.className = 'fe-tree-issue' + (entry.id === focusedFileId ? ' selected' : '');
  row.style.paddingLeft = depthPad + 'px';
  row.dataset.id = entry.id;

  const icon = document.createElement('span');
  icon.className = 'fe-tree-ico';
  icon.textContent = '📄';

  const name = document.createElement('span');
  name.className = 'fe-tree-issue-name';
  name.textContent = entry.filename;

  row.appendChild(icon);
  row.appendChild(name);

  if (entry.needs_review) {
    const dot = document.createElement('span');
    dot.className = 'fe-tree-lowconf';
    dot.title = 'Low confidence';
    row.appendChild(dot);
  }
  if (entry.xml_files && entry.xml_files.length) {
    const badge = document.createElement('span');
    badge.className = 'fe-tree-xml' + (entry.xml_files.length > 1 ? ' warning' : '');
    badge.textContent = 'XML';
    if (entry.xml_files.length > 1) badge.title = `${entry.xml_files.length} XML files found`;
    row.appendChild(badge);
  }

  const remove = document.createElement('button');
  remove.type = 'button';
  remove.className = 'fe-tree-remove';
  remove.textContent = '✕';
  remove.title = 'Remove';
  remove.onclick = (e) => { e.stopPropagation(); removeFile(entry.id); };
  row.appendChild(remove);

  row.addEventListener('click', () => focusFile(entry.id));
  return row;
}

function makeChevron(collapsed) {
  const c = document.createElement('span');
  c.className = 'fe-tree-chev';
  c.textContent = collapsed ? '▸' : '▾';
  return c;
}

function renderFileTree() {
  const tree = document.getElementById('feFileTree');
  tree.innerHTML = '';

  // Library-path row
  const root = commonRootPath(loadedFiles);
  const pathText = document.getElementById('feLibPathText');
  pathText.textContent = root || (loadedFiles.length ? '' : 'No folder loaded');
  document.getElementById('feLibPath').title = root;

  if (!loadedFiles.length) {
    const empty = document.createElement('div');
    empty.className = 'fe-tree-empty';
    empty.innerHTML = 'No files loaded.<br>Press <b>Select Folder</b> to add comics.';
    tree.appendChild(empty);
  } else {
    const folders = buildFileTree(loadedFiles);
    for (const folder of folders.values()) {
      const fKey = 'f:' + folder.name;
      const fCollapsed = treeCollapsed.has(fKey);
      const total = folder.direct.length + Array.from(folder.series.values()).reduce((a, s) => a + s.length, 0);

      const fRow = document.createElement('div');
      fRow.className = 'fe-tree-folder';
      fRow.appendChild(makeChevron(fCollapsed));
      const fIco = document.createElement('span'); fIco.className = 'fe-tree-ico'; fIco.textContent = '🗀';
      const fName = document.createElement('span'); fName.className = 'fe-tree-folder-name'; fName.textContent = folder.name;
      const fCount = document.createElement('span'); fCount.className = 'fe-tree-count'; fCount.textContent = total;
      fRow.appendChild(fIco); fRow.appendChild(fName); fRow.appendChild(fCount);
      fRow.onclick = () => toggleTreeNode(fKey);
      tree.appendChild(fRow);

      if (fCollapsed) continue;

      // series groups (natural-sorted by name)
      const seriesNames = Array.from(folder.series.keys()).sort(naturalCompare);
      for (const sName of seriesNames) {
        const sKey = fKey + '|s:' + sName;
        const sCollapsed = treeCollapsed.has(sKey);
        const sRow = document.createElement('div');
        sRow.className = 'fe-tree-series';
        sRow.appendChild(makeChevron(sCollapsed));
        const sIco = document.createElement('span'); sIco.className = 'fe-tree-ico'; sIco.textContent = '🗀';
        const sNameEl = document.createElement('span'); sNameEl.className = 'fe-tree-series-name'; sNameEl.textContent = sName;
        sRow.appendChild(sIco); sRow.appendChild(sNameEl);
        sRow.onclick = () => toggleTreeNode(sKey);
        tree.appendChild(sRow);
        if (sCollapsed) continue;
        const issues = folder.series.get(sName).slice().sort((a, b) => naturalCompare(a.filename, b.filename));
        for (const iss of issues) tree.appendChild(makeIssueRow(iss, 40));
      }

      // folder-direct issues (no series subfolder)
      const direct = folder.direct.slice().sort((a, b) => naturalCompare(a.filename, b.filename));
      for (const iss of direct) tree.appendChild(makeIssueRow(iss, 24));
    }
  }

  // Stats bar
  const total = loadedFiles.length;
  const withXml = loadedFiles.filter((f) => f.xml_files && f.xml_files.length).length;
  document.getElementById('feFilesFound').textContent = total;
  document.getElementById('feWithXml').textContent = withXml;
  document.getElementById('feWithoutXml').textContent = total - withXml;

  updateStatusBar();
}

function toggleTreeNode(key) {
  if (treeCollapsed.has(key)) treeCollapsed.delete(key);
  else treeCollapsed.add(key);
  renderFileTree();
}

async function focusFile(fileId) {
  if (searchOnlineOpen) return;  // Search Online modal traps focus (§9.6)
  focusedFileId = fileId;
  renderFileTree();
  await loadFileIntoEditor(fileId);
  await loadFileIntoViewer(fileId);
}

async function removeFile(fileId) {
  await fetch(`/api/editor/full/files/${fileId}`, { method: 'DELETE' });
  loadedFiles = loadedFiles.filter((f) => f.id !== fileId);
  if (focusedFileId === fileId) {
    focusedFileId = null;
    resetForm();
    resetViewer();
  }
  renderFileTree();
  updateMismatchIndicator();
  updateActionButtonStates();
}

async function clearFileList() {
  await fetch('/api/editor/full/files/clear', { method: 'DELETE' });
  loadedFiles = [];
  focusedFileId = null;
  resetForm();
  resetViewer();
  renderFileTree();
  updateMismatchIndicator();
  updateActionButtonStates();
}

// ══════════════════════════════════════════════════════════════════════════════
//  QUEUE (Column 4)
// ══════════════════════════════════════════════════════════════════════════════

function wireQueue() {
  document.getElementById('feQueueBtn').onclick = addCurrentToQueue;
  document.getElementById('feClearQueueBtn').onclick = clearQueue;
  document.getElementById('feProcessQueueBtn').onclick = () => processBatch('queue');
  document.getElementById('feProcessAllBtn').onclick = () => processBatch('all');
}

async function refreshQueueList() {
  const res = await fetch('/api/editor/full/queue');
  const data = await res.json();
  queueFiles = data.files;
  renderQueueList();
  updateMismatchIndicator();
  updateActionButtonStates();
}

function renderQueueList() {
  const list = document.getElementById('feQueueList');
  list.innerHTML = '';

  if (!queueFiles.length) {
    const empty = document.createElement('div');
    empty.className = 'fe-queue-empty';
    empty.innerHTML = 'Queue is empty.<br>Edit a file and press <b>＋ Queue</b>.';
    list.appendChild(empty);
  }

  for (const entry of queueFiles) {
    const card = document.createElement('div');
    card.className = 'fe-queue-card';

    const check = document.createElement('span');
    check.className = 'fe-queue-check';
    check.textContent = '✓';

    const info = document.createElement('div');
    info.className = 'fe-queue-info';
    const name = document.createElement('div');
    name.className = 'fe-queue-name';
    name.textContent = entry.filename;
    const status = document.createElement('div');
    status.className = 'fe-queue-status';
    status.textContent = 'Edited';
    info.appendChild(name);
    info.appendChild(status);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'fe-queue-remove';
    removeBtn.textContent = '✕';
    removeBtn.dataset.tooltip = 'Remove this file from the queue';
    removeBtn.onclick = () => removeFromQueue(entry.id);

    card.appendChild(check);
    card.appendChild(info);
    card.appendChild(removeBtn);
    list.appendChild(card);
  }

  document.getElementById('feQueueCount').textContent =
    `${queueFiles.length} file${queueFiles.length === 1 ? '' : 's'} in queue`;
  updateStatusBar();
}

function updateMismatchIndicator() {
  const indicator = document.getElementById('feMismatchIndicator');
  indicator.hidden = loadedFiles.length === queueFiles.length;
}

async function removeFromQueue(fileId) {
  await fetch(`/api/editor/full/queue/${fileId}`, { method: 'DELETE' });
  queueFiles = queueFiles.filter((f) => f.id !== fileId);
  renderQueueList();
  updateMismatchIndicator();
  updateActionButtonStates();
}

async function clearQueue() {
  await fetch('/api/editor/full/queue/clear', { method: 'DELETE' });
  queueFiles = [];
  renderQueueList();
  updateMismatchIndicator();
  updateActionButtonStates();
}

// Non-blocking save-time check against existing deduped people (Tier 4 Item
// 3) — splits a Writer/Penciller CSV value, checks each name against
// /api/people/fuzzy-match, and lets the user swap in the close existing
// match or keep what they typed. Never prevents queueing/processing either way.
async function warnOnFuzzyCredits(fields) {
  for (const [role, label] of [['Writer', 'writer'], ['Penciller', 'artist']]) {
    const raw = fields[role];
    if (!raw) continue;
    const names = raw.split(',').map((s) => s.trim()).filter(Boolean);
    const resolved = [];
    for (const name of names) {
      try {
        const res = await fetch(`/api/people/fuzzy-match?name=${encodeURIComponent(name)}`);
        const data = await res.json();
        if (data.closest_match) {
          const useExisting = confirm(
            `"${name}" is close to an existing ${label}: "${data.closest_match.name}".\n\n` +
            `OK = use "${data.closest_match.name}" instead\nCancel = save "${name}" as typed`
          );
          resolved.push(useExisting ? data.closest_match.name : name);
        } else {
          resolved.push(name);
        }
      } catch (_) {
        resolved.push(name);  // best-effort — a network hiccup never blocks the save
      }
    }
    fields[role] = resolved.join(', ');
  }
  return fields;
}

async function addCurrentToQueue() {
  if (!focusedFileId) {
    showError('Select a loaded file first.');
    return;
  }
  const fields = await warnOnFuzzyCredits(collectFormFields());
  const res = await fetch('/api/editor/full/queue/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: focusedFileId, fields }),
  });
  if (!res.ok) {
    showError('Could not add this file to the queue.');
    return;
  }
  clearError();
  await refreshQueueList();
}

// ══════════════════════════════════════════════════════════════════════════════
//  BATCH PROCESSING
// ══════════════════════════════════════════════════════════════════════════════

function setProcessingState(active) {
  const indicator = document.getElementById('feStatusIndicator');
  indicator.textContent = active ? 'Processing…' : 'Files will be updated with edited ComicInfo.xml.';
  indicator.classList.toggle('processing', active);
}

async function processBatch(mode) {
  if (searchOnlineOpen) return;  // Search Online modal traps focus (§9.6)
  if (mode === 'queue' && queueFiles.length === 0) return;
  if (mode === 'all' && loadedFiles.length === 0) return;

  const incrementEnabled = document.getElementById('fe-increment').checked;
  const startIssueNo = parseInt(document.getElementById('fe-number').value, 10) || 1;

  const payload = { mode, increment_enabled: incrementEnabled, start_issue_no: startIssueNo };
  if (mode === 'all') {
    payload.fields = await warnOnFuzzyCredits(collectFieldsForProcessAll());
    payload.file_ids = treeOrderedFileIds(loadedFiles);
  }

  setProcessingState(true);
  clearError();
  try {
    const res = await fetch('/api/editor/full/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    if (result.errors && result.errors.length) {
      openProcessErrorModal(result.processed, result.errors);
    }
    await refreshFileList();
    await refreshQueueList();
    if (focusedFileId) await loadFileIntoEditor(focusedFileId);
  } catch (err) {
    showError('Network error — processing did not complete.');
  } finally {
    setProcessingState(false);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  XML EDITOR (Column 2)
// ══════════════════════════════════════════════════════════════════════════════

function wireXmlEditor() {
  for (const btn of document.querySelectorAll('.editor-tab-btn')) {
    btn.addEventListener('click', () => {
      for (const b of document.querySelectorAll('.editor-tab-btn')) b.classList.remove('active');
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      for (const panel of document.querySelectorAll('.editor-tab-panel')) {
        panel.hidden = panel.dataset.panel !== tab;
      }
    });
  }
  document.getElementById('feQueueBtn').onclick = addCurrentToQueue;
  document.getElementById('fe-genre-add').addEventListener('change', (e) => {
    addGenre(e.target.value);
    e.target.value = '';
  });
  document.getElementById('fe-format').addEventListener('change', updateActionButtonStates);
  document.getElementById('fe-agerating').addEventListener('change', updateActionButtonStates);
}

function setField(id, value) {
  document.getElementById(id).value = value || '';
}

async function loadFileIntoEditor(fileId) {
  const res = await fetch(`/api/editor/full/files/${fileId}/xml`);
  if (!res.ok) {
    showError('Could not load this file for editing.');
    return;
  }
  const data = await res.json();

  if (data.multiple_xml) {
    openMultiXmlModal(fileId, data.candidates);
    return;
  }

  // Lazy-on-focus (confirmed with Tez, 2026-07-03): this XML parse already
  // happens on every focus, so reading NeedsReview off it costs nothing extra.
  const entry = loadedFiles.find((f) => f.id === fileId);
  if (entry) {
    entry.needs_review = !!data.fields.NeedsReview;
    renderFileTree();
  }

  populateForm(data.fields);
}

function populateForm(fields) {
  setField('fe-series', fields.Series);
  setField('fe-title', fields.Title);
  setField('fe-number', fields.Number);
  setField('fe-year', fields.Year);
  setField('fe-summary', fields.Summary);
  setField('fe-count', fields.Count);
  setField('fe-pagecount', fields.PageCount);
  setField('fe-writer', fields.Writer);
  setField('fe-penciller', fields.Penciller);
  setField('fe-publisher', fields.Publisher);
  setField('fe-storyarc', fields.StoryArc);
  setField('fe-language', fields.Language);
  setField('fe-notes', fields.Notes || 'Modified with the CAPT');

  document.getElementById('fe-bw').checked = fields.BlackAndWhite === 'on';

  // No matching <option> for a stale/removed Format leaves the select unselected, i.e. blank.
  const formatSelect = document.getElementById('fe-format');
  formatSelect.value = fields.Format || '';

  const ratingSelect = document.getElementById('fe-agerating');
  ratingSelect.value = AGE_RATING_OPTIONS.includes(fields.AgeRating) ? fields.AgeRating : '';

  const existingGenres = (fields.Genre || '').split(',').map((g) => g.trim()).filter(Boolean);
  setGenres(existingGenres);

  updateActionButtonStates();
}

function resetForm() {
  document.getElementById('feForm').reset();
  setGenres([]);
  document.getElementById('fe-format').value = '';
  document.getElementById('fe-agerating').value = '';
  updateActionButtonStates();
}

function collectFormFields() {
  return {
    Series: document.getElementById('fe-series').value,
    Title: document.getElementById('fe-title').value,
    Number: document.getElementById('fe-number').value,
    Year: document.getElementById('fe-year').value,
    Genre: selectedGenres.join(', '),
    Format: document.getElementById('fe-format').value,
    BlackAndWhite: document.getElementById('fe-bw').checked ? 'on' : '',
    AgeRating: document.getElementById('fe-agerating').value,
    Summary: document.getElementById('fe-summary').value,
    Count: document.getElementById('fe-count').value,
    Writer: document.getElementById('fe-writer').value,
    Penciller: document.getElementById('fe-penciller').value,
    Publisher: document.getElementById('fe-publisher').value,
    PageCount: document.getElementById('fe-pagecount').value,
    StoryArc: document.getElementById('fe-storyarc').value,
    Language: document.getElementById('fe-language').value,
    Notes: document.getElementById('fe-notes').value,
  };
}

// EDITOR_SPEC.md §5.2 — Process All only bulk-applies fields whose "Apply to
// All" checkbox is checked; everything else is omitted so build_xml_from_fields()
// leaves each file's existing value untouched. Issue Number has no checkbox —
// it's governed entirely by the increment_enabled/start_issue_no mechanism.
function collectFieldsForProcessAll() {
  const all = collectFormFields();
  const checked = new Set(
    Array.from(document.querySelectorAll('.fe-apply-all:checked')).map((c) => c.dataset.field)
  );
  const result = {};
  for (const field of checked) {
    if (field in all) result[field] = all[field];
  }
  return result;
}

function updateActionButtonStates() {
  document.getElementById('feQueueBtn').disabled = !focusedFileId;
  const queueReady = selectedGenres.length > 0
    && document.getElementById('fe-format').value !== ''
    && document.getElementById('fe-agerating').value !== '';
  document.getElementById('feQueueBtn').classList.toggle('is-ready', queueReady);
  document.getElementById('feProcessAllBtn').disabled = loadedFiles.length === 0 || queueFiles.length > 0;
  document.getElementById('feProcessQueueBtn').disabled = queueFiles.length === 0;
  document.getElementById('feClearQueueBtn').disabled = queueFiles.length === 0;
}

function showError(msg) {
  const box = document.getElementById('feError');
  box.hidden = false;
  box.textContent = msg;
}

function clearError() {
  const box = document.getElementById('feError');
  box.hidden = true;
  box.textContent = '';
}

// ── Footer status bar ────────────────────────────────────────────────────────
function updateStatusBar() {
  const sel = loadedFiles.find((f) => f.id === focusedFileId);
  document.getElementById('feStatusSelected').textContent = sel ? sel.filename : '—';

  const xmlEl = document.getElementById('feStatusXml');
  if (!sel) {
    xmlEl.textContent = '—';
    xmlEl.className = 'fe-sb-strong';
  } else if (!sel.xml_files || sel.xml_files.length === 0) {
    xmlEl.textContent = 'No XML';
    xmlEl.className = 'fe-sb-strong fe-sb-warn';
  } else if (sel.xml_files.length > 1) {
    xmlEl.textContent = `${sel.xml_files.length} XML`;
    xmlEl.className = 'fe-sb-strong fe-sb-warn';
  } else {
    xmlEl.textContent = 'Valid ✓';
    xmlEl.className = 'fe-sb-strong fe-sb-ok';
  }

  const low = loadedFiles.filter((f) => f.needs_review).length;
  const lowEl = document.getElementById('feStatusLowConf');
  lowEl.textContent = low;
  lowEl.className = 'fe-sb-strong' + (low ? ' fe-sb-warn' : '');

  document.getElementById('feStatusQueued').textContent = queueFiles.length;
}

// ══════════════════════════════════════════════════════════════════════════════
//  COMIC VIEWER (Column 3) — zoom / fit / fullscreen / lazy thumbnail strip
// ══════════════════════════════════════════════════════════════════════════════

function wireImageViewer() {
  document.getElementById('fePrevBtn').onclick = () => changeViewerPage(-1);
  document.getElementById('feNextBtn').onclick = () => changeViewerPage(1);
  document.getElementById('feThumbPrev').onclick = () => changeViewerPage(-1);
  document.getElementById('feThumbNext').onclick = () => changeViewerPage(1);
  document.getElementById('feZoomInBtn').onclick = () => setZoom(viewerZoom + 0.25);
  document.getElementById('feZoomOutBtn').onclick = () => setZoom(viewerZoom - 0.25);
  document.getElementById('feFitBtn').onclick = fitViewer;
  document.getElementById('feFullscreenBtn').onclick = toggleFullscreen;
  wireViewerPan();
}

// Drag-to-pan — once zoomed past 100% the frame scrolls (overflow: auto),
// but a zoomed-in comic page is usually bigger than the visible frame in
// both axes, so a click-drag is the natural way to look around it (plain
// scrollbars only cover one axis at a time comfortably). Only active while
// zoomed; at 100% the image already fits so there's nothing to pan.
function wireViewerPan() {
  const frame = document.getElementById('feViewerFrame');
  let dragging = false;
  let startX = 0, startY = 0, startScrollLeft = 0, startScrollTop = 0;

  frame.addEventListener('pointerdown', (e) => {
    if (viewerZoom === 1 || e.button !== 0) return;
    dragging = true;
    startX = e.clientX;
    startY = e.clientY;
    startScrollLeft = frame.scrollLeft;
    startScrollTop = frame.scrollTop;
    frame.classList.add('fe-viewer-frame--dragging');
    frame.setPointerCapture(e.pointerId);
    e.preventDefault();
  });

  frame.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    frame.scrollLeft = startScrollLeft - (e.clientX - startX);
    frame.scrollTop = startScrollTop - (e.clientY - startY);
  });

  const endDrag = (e) => {
    if (!dragging) return;
    dragging = false;
    frame.classList.remove('fe-viewer-frame--dragging');
    if (e && frame.hasPointerCapture(e.pointerId)) frame.releasePointerCapture(e.pointerId);
  };
  frame.addEventListener('pointerup', endDrag);
  frame.addEventListener('pointercancel', endDrag);
}

const VIEWER_BTNS = ['fePrevBtn', 'feNextBtn', 'feThumbPrev', 'feThumbNext',
  'feZoomInBtn', 'feZoomOutBtn', 'feFitBtn', 'feFullscreenBtn'];

function resetViewer() {
  viewerFileId = null;
  viewerImageList = [];
  viewerPageNum = 0;
  viewerZoom = 1;
  thumbCache = new Map();
  const img = document.getElementById('feViewerImg');
  img.hidden = true;
  img.style.width = '';
  document.getElementById('feViewerFrame').classList.remove('fe-viewer-frame--zoomed');
  document.getElementById('feViewerEmpty').hidden = false;
  document.getElementById('fePageInfo').textContent = '—';
  document.getElementById('feThumbStrip').innerHTML = '';
  for (const id of VIEWER_BTNS) document.getElementById(id).disabled = true;
}

async function loadFileIntoViewer(fileId) {
  const res = await fetch(`/api/editor/full/files/${fileId}/preview`);
  if (!res.ok) { resetViewer(); return; }
  const data = await res.json();

  viewerFileId = fileId;
  viewerImageList = data.image_list;
  viewerPageNum = 0;
  viewerZoom = 1;
  thumbCache = new Map();

  const hasPages = viewerImageList.length > 0;
  document.getElementById('feViewerEmpty').hidden = hasPages;
  document.getElementById('feViewerImg').hidden = !hasPages;
  for (const id of ['feZoomInBtn', 'feZoomOutBtn', 'feFitBtn', 'feFullscreenBtn']) {
    document.getElementById(id).disabled = !hasPages;
  }

  if (hasPages) {
    await showViewerPage();
  } else {
    document.getElementById('feThumbStrip').innerHTML = '';
  }
}

async function showViewerPage() {
  const res = await fetch(`/api/editor/full/files/${viewerFileId}/page/${viewerPageNum}`);
  if (!res.ok) return;
  const data = await res.json();

  const img = document.getElementById('feViewerImg');
  img.src = data.data;
  applyViewerZoom();

  document.getElementById('fePageInfo').textContent = `${viewerPageNum + 1} / ${viewerImageList.length}`;
  document.getElementById('fePrevBtn').disabled = viewerPageNum === 0;
  document.getElementById('feNextBtn').disabled = viewerPageNum >= viewerImageList.length - 1;
  document.getElementById('feThumbPrev').disabled = viewerPageNum === 0;
  document.getElementById('feThumbNext').disabled = viewerPageNum >= viewerImageList.length - 1;

  renderThumbStrip();
}

function changeViewerPage(delta) {
  const next = viewerPageNum + delta;
  if (next < 0 || next >= viewerImageList.length) return;
  viewerPageNum = next;
  showViewerPage();
}

function goToViewerPage(n) {
  if (n < 0 || n >= viewerImageList.length || n === viewerPageNum) return;
  viewerPageNum = n;
  showViewerPage();
}

function setZoom(value) {
  viewerZoom = Math.max(0.5, Math.min(3, value));
  applyViewerZoom();
}

function fitViewer() {
  viewerZoom = 1;
  applyViewerZoom();
}

function applyViewerZoom() {
  const img = document.getElementById('feViewerImg');
  if (img.hidden) return;
  // zoom === 1 → let the CSS max-width/height fit the frame. Otherwise the
  // .fe-viewer-img max-width/max-height: 100% rules must be cleared too —
  // left in place they clamp the inline width straight back down, so zooming
  // in (>100%) had no visible effect while zooming out still "worked".
  if (viewerZoom === 1) {
    img.style.width = '';
    img.style.maxWidth = '';
    img.style.maxHeight = '';
  } else {
    img.style.width = `${100 * viewerZoom}%`;
    img.style.maxWidth = 'none';
    img.style.maxHeight = 'none';
  }
  document.getElementById('feViewerFrame')
    .classList.toggle('fe-viewer-frame--zoomed', viewerZoom !== 1);
}

function toggleFullscreen() {
  const frame = document.getElementById('feViewerFrame');
  if (!document.fullscreenElement) {
    if (frame.requestFullscreen) frame.requestFullscreen();
  } else if (document.exitFullscreen) {
    document.exitFullscreen();
  }
}

// Lazy thumbnail strip — renders a 7-cell window around the current page and
// fetches each cell's image on demand (downscaled via ?w=120), cached so page
// navigation on a large archive never re-decodes the whole book.
function renderThumbStrip() {
  const strip = document.getElementById('feThumbStrip');
  strip.innerHTML = '';
  const total = viewerImageList.length;
  if (!total) return;

  let start = Math.max(0, viewerPageNum - 3);
  let end = Math.min(total - 1, start + 6);
  start = Math.max(0, end - 6);

  for (let n = start; n <= end; n++) {
    const cell = document.createElement('button');
    cell.type = 'button';
    cell.className = 'fe-thumb' + (n === viewerPageNum ? ' active' : '');
    cell.title = `Page ${n + 1}`;

    const imgBox = document.createElement('div');
    imgBox.className = 'fe-thumb-img';
    const num = document.createElement('span');
    num.className = 'fe-thumb-num';
    num.textContent = n + 1;

    cell.appendChild(imgBox);
    cell.appendChild(num);
    cell.onclick = () => goToViewerPage(n);
    strip.appendChild(cell);

    loadThumbImage(n, imgBox);
  }
}

function loadThumbImage(n, el) {
  const fileId = viewerFileId;
  const key = `${fileId}:${n}`;
  if (thumbCache.has(key)) {
    el.style.backgroundImage = `url("${thumbCache.get(key)}")`;
    return;
  }
  fetch(`/api/editor/full/files/${fileId}/page/${n}?w=120`)
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => {
      if (!d || !d.data) return;
      thumbCache.set(key, d.data);
      // Only paint if we're still on the same file (async guard).
      if (viewerFileId === fileId) el.style.backgroundImage = `url("${d.data}")`;
    })
    .catch(() => {});
}

// ══════════════════════════════════════════════════════════════════════════════
//  FILE PICKER MODAL (ported from file_mgmnt.html/js, Section 5.1)
// ══════════════════════════════════════════════════════════════════════════════

function wirePicker() {
  document.getElementById('fePickerCloseBtn').onclick = closePicker;
  document.getElementById('fePickerHomeBtn').onclick = () => loadPickerDirectory(null);
  document.getElementById('fePickerUpBtn').onclick = pickerNavigateUp;
  document.getElementById('fePickerSelectAllBtn').onclick = pickerSelectAll;
  document.getElementById('fePickerDeselectAllBtn').onclick = pickerDeselectAll;
  document.getElementById('fePickerAddFilesBtn').onclick = pickerAddSelectedFiles;
  document.getElementById('fePickerAddFolderBtn').onclick = pickerAddSelectedFolder;
}

function openPicker() {
  pickerSelected.clear();
  document.getElementById('fePickerOverlay').hidden = false;
  updatePickerButtonStates();
  loadPickerDirectory(pickerPath);
}

function closePicker() {
  document.getElementById('fePickerOverlay').hidden = true;
}

async function loadPickerDirectory(path) {
  const url = path ? `/api/editor/full/browse?path=${encodeURIComponent(path)}` : '/api/editor/full/browse';
  const res = await fetch(url);
  if (!res.ok) return;
  const data = await res.json();
  pickerPath = data.path;
  pickerSelected.clear();
  renderPickerTree(data.items || []);
  renderPickerBreadcrumb(data.path);
}

function renderPickerBreadcrumb(path) {
  const breadcrumb = document.getElementById('fePickerBreadcrumb');
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
      link.onclick = (e) => { e.preventDefault(); loadPickerDirectory(target); };
      breadcrumb.appendChild(link);
    }
    if (!isLast) breadcrumb.appendChild(document.createTextNode(' \\ '));
  });
}

function renderPickerTree(items) {
  const tree = document.getElementById('fePickerTree');
  tree.innerHTML = '';

  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'fe-picker-empty';
    empty.textContent = 'No items found.';
    tree.appendChild(empty);
    updatePickerSelectedCount();
    return;
  }

  items.sort((a, b) => {
    if (a.type === 'folder' && b.type === 'file') return -1;
    if (a.type === 'file' && b.type === 'folder') return 1;
    return naturalCompare(a.name, b.name);
  });

  for (const item of items) {
    const row = document.createElement('div');
    row.className = `fe-picker-item ${item.type}`;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.addEventListener('change', () => {
      row.classList.toggle('selected', checkbox.checked);
      if (checkbox.checked) pickerSelected.set(item.path, item.type);
      else pickerSelected.delete(item.path);
      updatePickerSelectedCount();
    });

    const name = document.createElement('span');
    name.className = 'fe-picker-item-name';
    name.textContent = item.type === 'file' && item.xml_files && item.xml_files.length
      ? `${item.name} (${item.xml_files.length} XML)`
      : item.name;

    row.appendChild(checkbox);
    row.appendChild(name);

    if (item.type === 'folder') {
      row.addEventListener('click', (e) => { if (e.target !== checkbox) loadPickerDirectory(item.path); });
    } else {
      row.addEventListener('click', (e) => {
        if (e.target === checkbox) return;
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event('change'));
      });
    }

    tree.appendChild(row);
  }

  updatePickerSelectedCount();
}

function updatePickerSelectedCount() {
  const count = pickerSelected.size;
  document.getElementById('fePickerSelectedCount').textContent = `${count} item${count === 1 ? '' : 's'} selected`;
  updatePickerButtonStates();
}

function updatePickerButtonStates() {
  const fileBtn = document.getElementById('fePickerAddFilesBtn');
  const folderBtn = document.getElementById('fePickerAddFolderBtn');

  const hasFiles = Array.from(pickerSelected.values()).some(type => type === 'file');
  const hasFolders = Array.from(pickerSelected.values()).some(type => type === 'folder');

  fileBtn.disabled = !hasFiles;
  fileBtn.classList.toggle('is-ready', hasFiles);

  folderBtn.disabled = !hasFolders;
  folderBtn.classList.toggle('is-ready', hasFolders);
}

function pickerSelectAll() {
  document.querySelectorAll('#fePickerTree input[type="checkbox"]').forEach((cb) => {
    if (!cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change')); }
  });
}

function pickerDeselectAll() {
  document.querySelectorAll('#fePickerTree input[type="checkbox"]').forEach((cb) => {
    if (cb.checked) { cb.checked = false; cb.dispatchEvent(new Event('change')); }
  });
}

function pickerNavigateUp() {
  const parts = (pickerPath || '').split('\\').filter(Boolean);
  if (parts.length > 1) {
    parts.pop();
    loadPickerDirectory(parts.join('\\'));
  }
}

function pickerGetSelectedPaths(type) {
  return Array.from(pickerSelected.entries()).filter(([, t]) => t === type).map(([p]) => p);
}

async function pickerAddSelectedFiles() {
  const filePaths = pickerGetSelectedPaths('file');
  if (!filePaths.length) return;
  await fetch('/api/editor/full/files/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_paths: filePaths }),
  });
  closePicker();
  await refreshFileList();
}

async function pickerAddSelectedFolder() {
  const folderPaths = pickerGetSelectedPaths('folder');
  if (!folderPaths.length) return;
  await fetch('/api/editor/full/folders/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_paths: folderPaths }),
  });
  closePicker();
  await refreshFileList();
}

// ══════════════════════════════════════════════════════════════════════════════
//  MULTI-COMICINFO.XML RESOLUTION (Section 3.5)
// ══════════════════════════════════════════════════════════════════════════════

function wireMultiXmlModal() {
  document.getElementById('feMultiXmlCloseBtn').onclick = () => {
    document.getElementById('feMultiXmlOverlay').hidden = true;
  };
}

// ── Process All error modal (2.3-fixes.md Fix 3) ────────────────────────────
function wireProcessErrorModal() {
  const close = () => { document.getElementById('feProcessErrorOverlay').hidden = true; };
  document.getElementById('feProcessErrorCloseBtn').onclick = close;
  document.getElementById('feProcessErrorDismissBtn').onclick = close;
}

function openProcessErrorModal(processed, errors) {
  const body = document.getElementById('feProcessErrorBody');
  const total = processed + errors.length;
  let text = `Processed ${processed} of ${total} files.\n\n${errors[0]}`;
  if (errors.length > 1) {
    text += `\n\n(${errors.length - 1} more file${errors.length - 1 === 1 ? '' : 's'} have the same ` +
      `errors — unchecked required fields default to blank and will fail validation. Tick Genre, ` +
      `Format, and Age Rating in the "Apply to All" column, or leave these files unselected.)`;
  }
  body.textContent = text;
  document.getElementById('feProcessErrorOverlay').hidden = false;
}

function openMultiXmlModal(fileId, candidates) {
  multiXmlFileId = fileId;
  const container = document.getElementById('feMultiXmlCandidates');
  container.innerHTML = '';

  for (const candidate of candidates) {
    const card = document.createElement('div');
    card.className = 'fe-multixml-candidate';

    const header = document.createElement('div');
    header.className = 'fe-multixml-candidate-header';
    header.textContent = candidate.filename;

    const fieldsBox = document.createElement('div');
    fieldsBox.className = 'fe-multixml-candidate-fields';
    for (const [key, value] of Object.entries(candidate.fields)) {
      if (!value) continue;
      const row = document.createElement('div');
      row.className = 'fe-multixml-field-row';
      row.innerHTML = `<strong>${key}:</strong> `;
      row.appendChild(document.createTextNode(String(value).slice(0, 200)));
      fieldsBox.appendChild(row);
    }

    const keepBtn = document.createElement('button');
    keepBtn.type = 'button';
    keepBtn.className = 'btn-primary';
    keepBtn.textContent = 'Keep this one';
    keepBtn.dataset.tooltip = 'Keep this ComicInfo.xml and delete the other(s) from the archive';
    keepBtn.onclick = () => resolveMultiXml(candidate.filename);

    card.appendChild(header);
    card.appendChild(fieldsBox);
    card.appendChild(keepBtn);
    container.appendChild(card);
  }

  document.getElementById('feMultiXmlOverlay').hidden = false;
}

async function resolveMultiXml(keepFilename) {
  const res = await fetch(`/api/editor/full/files/${multiXmlFileId}/resolve-xml`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keep: keepFilename }),
  });
  document.getElementById('feMultiXmlOverlay').hidden = true;

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    showError(body?.detail || 'Could not resolve the multiple XML files.');
    return;
  }
  const data = await res.json();
  populateForm(data.fields);

  // Refresh the file row's xml_files so the warning clears
  const entry = loadedFiles.find((f) => f.id === multiXmlFileId);
  if (entry) entry.xml_files = ['ComicInfo.xml'];
  renderFileTree();
}

// ══════════════════════════════════════════════════════════════════════════════
//  SEARCH ONLINE — Select Series / Select Issue (EDITOR_SPEC.md §9)
//  One modal, two internal steps — a "← Back to Series" control returns to the
//  cached soSeriesResults, no re-fetch.
// ══════════════════════════════════════════════════════════════════════════════

function wireSearchOnlineModal() {
  document.getElementById('feSearchOnlineBtn').onclick = openSearchOnline;
  document.getElementById('feSearchOnlineCloseBtn').onclick = closeSearchOnlineModal;
  document.getElementById('feSoBackBtn').onclick = () => showSoStep('series');
  document.getElementById('feSoSortSelect').onchange = (e) => { soSortKey = e.target.value; renderSoSeriesTable(); };
  document.getElementById('feSoSortDirBtn').onclick = () => {
    soSortDir = soSortDir === 'asc' ? 'desc' : 'asc';
    document.getElementById('feSoSortDirBtn').innerHTML = soSortDir === 'asc' ? '&#8593;' : '&#8595;';
    renderSoSeriesTable();
  };
  document.getElementById('feSoCancelBtn').onclick = closeSearchOnlineModal;
  document.getElementById('feSoIssuesBtn').onclick = soIssuesBtnClick;
  document.getElementById('feSoOkBtn').onclick = soOkBtnClick;
  document.getElementById('feSoIssueOkBtn').onclick = () => {
    if (soSelectedIssueId) confirmSoIssue(soSelectedIssueId);
  };
}

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function openSearchOnline() {
  if (!focusedFileId) {
    showError('Select a loaded file first.');
    return;
  }
  const fields = collectFormFields();
  if (!fields.Series || !fields.Series.trim()) {
    showError('Need to enter a series name to search.');
    return;
  }
  clearError();

  searchOnlineOpen = true;
  document.getElementById('feSearchOnlineOverlay').hidden = false;
  showSoStep('series');

  document.getElementById('feSoSeriesTbody').innerHTML = '<tr><td colspan="4">Searching…</td></tr>';
  const res = await fetch(`/api/editor/full/search/series?q=${encodeURIComponent(fields.Series.trim())}`);
  if (!res.ok) {
    document.getElementById('feSoSeriesTbody').innerHTML = '<tr><td colspan="4">Search failed.</td></tr>';
    return;
  }
  const data = await res.json();
  soSeriesResults = data.results;
  renderSoSeriesTable();
}

function closeSearchOnlineModal() {
  searchOnlineOpen = false;
  document.getElementById('feSearchOnlineOverlay').hidden = true;
}

function showSoStep(step) {
  document.getElementById('feSoStepSeries').hidden = step !== 'series';
  document.getElementById('feSoStepIssue').hidden = step !== 'issue';
  document.getElementById('feSearchOnlineTitle').textContent = step === 'series' ? 'Select Series' : 'Select Issue';
}

const SO_SORT_KEY_FNS = {
  name:             s => (s.name || '').toLowerCase(),
  start_year:       s => s.start_year || 0,
  count_of_issues:  s => s.count_of_issues || 0,
  publisher:        s => (s.publisher || '').toLowerCase(),
};

// soSeriesResults stays in ComicVine's own relevance order (closest match
// first) and is never mutated — sorting only ever applies to what's
// displayed, and only once the user picks a Sort option.
function getSortedSoSeriesResults() {
  if (!soSortKey) return soSeriesResults;
  const keyFn = SO_SORT_KEY_FNS[soSortKey] || SO_SORT_KEY_FNS.name;
  return [...soSeriesResults].sort((a, b) => {
    const ka = keyFn(a), kb = keyFn(b);
    const cmp = typeof ka === 'string' ? ka.localeCompare(kb) : ka - kb;
    return soSortDir === 'desc' ? -cmp : cmp;
  });
}

function renderSoSeriesTable() {
  const tbody = document.getElementById('feSoSeriesTbody');
  tbody.innerHTML = '';
  document.getElementById('feSoSeriesCover').src = '';
  document.getElementById('feSoSeriesDescription').textContent = '';

  const sorted = getSortedSoSeriesResults();
  if (!sorted.length) {
    tbody.innerHTML = '<tr><td colspan="4">No results found.</td></tr>';
    return;
  }

  for (const series of sorted) {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${escapeHtml(series.name)}</td><td>${series.start_year || ''}</td>` +
      `<td>${series.count_of_issues != null ? series.count_of_issues : ''}</td><td>${escapeHtml(series.publisher)}</td>`;
    row.addEventListener('click', () => previewSoSeries(series, row));
    row.addEventListener('dblclick', () => proceedToSoIssues(series.id));
    tbody.appendChild(row);
  }
  previewSoSeries(sorted[0], tbody.firstElementChild);
}

function previewSoSeries(series, row) {
  soSelectedSeries = series;
  document.querySelectorAll('#feSoSeriesTbody tr').forEach((r) => r.classList.remove('selected'));
  if (row) row.classList.add('selected');
  document.getElementById('feSoSeriesCover').src = series.image_url || '';
  document.getElementById('feSoSeriesDescription').textContent = series.description || '';
}

function soIssuesBtnClick() {
  if (!soSelectedSeries) return;
  proceedToSoIssues(soSelectedSeries.id);
}

async function soOkBtnClick() {
  if (!soSelectedSeries) return;
  const res = await fetch(`/api/editor/full/search/issues?series_id=${encodeURIComponent(soSelectedSeries.id)}`);
  if (!res.ok) {
    showError('Could not load issues.');
    return;
  }
  const data = await res.json();
  if (!data.results.length) {
    showError('No issues found for this series.');
    return;
  }
  confirmSoIssue(data.results[0].issue_id);
}

async function proceedToSoIssues(seriesId) {
  soSelectedSeriesId = seriesId;
  showSoStep('issue');
  const tbody = document.getElementById('feSoIssueTbody');
  tbody.innerHTML = '<tr><td colspan="3">Loading…</td></tr>';
  const res = await fetch(`/api/editor/full/search/issues?series_id=${encodeURIComponent(seriesId)}`);
  if (!res.ok) {
    tbody.innerHTML = '<tr><td colspan="3">Could not load issues.</td></tr>';
    return;
  }
  const data = await res.json();
  renderSoIssueTable(data.results);
}

function renderSoIssueTable(issues) {
  const tbody = document.getElementById('feSoIssueTbody');
  tbody.innerHTML = '';
  document.getElementById('feSoIssueCover').src = '';
  document.getElementById('feSoIssueDescription').textContent = '';

  if (!issues.length) {
    tbody.innerHTML = '<tr><td colspan="3">No issues found.</td></tr>';
    return;
  }

  for (const issue of issues) {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${escapeHtml(issue.number)}</td><td>${escapeHtml(issue.date)}</td><td>${escapeHtml(issue.title)}</td>`;
    row.dataset.tooltip = "Double-click to apply this issue's data, overwriting all current fields";
    row.addEventListener('click', () => previewSoIssue(issue, row));
    row.addEventListener('dblclick', () => confirmSoIssue(issue.issue_id));
    tbody.appendChild(row);
  }
  previewSoIssue(issues[0], tbody.firstElementChild);
}

function previewSoIssue(issue, row) {
  soSelectedIssueId = issue.issue_id;
  document.querySelectorAll('#feSoIssueTbody tr').forEach((r) => r.classList.remove('selected'));
  if (row) row.classList.add('selected');
  document.getElementById('feSoIssueCover').src = issue.cover_url || '';
  document.getElementById('feSoIssueDescription').textContent = issue.description || '';
}

async function confirmSoIssue(issueId) {
  const res = await fetch('/api/editor/full/search/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ issue_id: issueId }),
  });
  if (!res.ok) {
    showError('Could not apply this match.');
    return;
  }
  const data = await res.json();
  // §9.7 — fully overwrites only the mapped fields; Genre/Format/AgeRating/
  // BlackAndWhite/PageCount (never in the mapped set) are left untouched.
  populateForm({ ...collectFormFields(), ...data.fields });
  closeSearchOnlineModal();
  clearNeedsReviewIndicatorFor(focusedFileId);
}

// §9.7 — clears the border/count immediately in frontend in-memory state; the
// NeedsReview XML tag itself only actually clears on the file's next real save.
function clearNeedsReviewIndicatorFor(fileId) {
  const entry = loadedFiles.find((f) => f.id === fileId);
  if (entry) entry.needs_review = false;
  renderFileTree();
}
