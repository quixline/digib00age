// ComicVault — editor_full.js
// Full Editor toolbox: pre-library batch metadata editing. EDITOR_SPEC.md Section 5.
// Self-contained — no dependency on app.js.

const AGE_RATING_OPTIONS = [
  'Everyone', 'Early Childhood', 'Everyone 10+', 'PG', 'Adult', 'Teen', 'Teen+', 'Mature',
];

// ── State ────────────────────────────────────────────────────────────────────
let loadedFiles = [];        // [{id, filename, path, xml_files}] — display order (drag-drop reorder)
let queueFiles = [];         // [{id, filename, path, xml_files, queued_fields}]
let focusedFileId = null;
let dragSourceId = null;

let pickerPath = null;
let pickerSelected = new Map(); // path -> 'file' | 'folder'

let viewerFileId = null;
let viewerImageList = [];
let viewerPageNum = 0;
let viewerZoom = 1;

let multiXmlFileId = null;

// Search Online (EDITOR_SPEC.md §9)
let searchOnlineOpen = false;   // focus trap — blocks card-swap/Process while the modal is open
let soSeriesResults = [];       // cached Step 1 results, so "Back to Series" doesn't re-fetch
let soSelectedSeriesId = null;

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

async function loadGenreOptions() {
  const genres = await fetch('/api/editor/genres').then((r) => r.json());
  const grid = document.getElementById('fe-genre-grid');
  grid.innerHTML = '';
  for (const name of genres) {
    const label = document.createElement('label');
    label.className = 'editor-genre-item';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = name;
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(' ' + name));
    grid.appendChild(label);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  FILE MANAGEMENT (Column 1, upper)
// ══════════════════════════════════════════════════════════════════════════════

function wireFileManagement() {
  document.getElementById('feExplorerBtn').onclick = openPicker;
  document.getElementById('feClearListBtn').onclick = clearFileList;

  const list = document.getElementById('feFileList');
  list.addEventListener('keydown', (e) => {
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
  // Preserve current display order where possible (drag-drop), append new entries
  const known = new Map(loadedFiles.map((f) => [f.id, f]));
  const incoming = new Map(data.files.map((f) => [f.id, f]));
  const ordered = loadedFiles.filter((f) => incoming.has(f.id)).map((f) => incoming.get(f.id));
  for (const f of data.files) {
    if (!known.has(f.id)) ordered.push(f);
  }
  loadedFiles = ordered;
  renderFileList();
  updateMismatchIndicator();
  updateActionButtonStates();
}

function xmlStatusLine(entry) {
  if (!entry.xml_files || entry.xml_files.length === 0) return 'No XML — will use filename';
  if (entry.xml_files.length > 1) return `⚠ ${entry.xml_files.length} XML files found`;
  return entry.xml_files[0];
}

function renderFileList() {
  const list = document.getElementById('feFileList');
  list.innerHTML = '';

  for (const entry of loadedFiles) {
    const row = document.createElement('div');
    row.className = 'fe-file-row'
      + (entry.id === focusedFileId ? ' focused' : '')
      + (entry.needs_review ? ' needs-review' : '');
    row.draggable = true;
    row.dataset.id = entry.id;

    const info = document.createElement('div');
    info.className = 'fe-file-row-info';
    const name = document.createElement('div');
    name.className = 'fe-file-row-name';
    name.textContent = entry.filename;
    const status = document.createElement('div');
    status.className = 'fe-file-row-status' + (entry.xml_files && entry.xml_files.length > 1 ? ' warning' : '');
    status.textContent = xmlStatusLine(entry);
    info.appendChild(name);
    info.appendChild(status);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'folder-remove-btn';
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = (e) => { e.stopPropagation(); removeFile(entry.id); };

    row.appendChild(info);
    row.appendChild(removeBtn);

    row.addEventListener('click', () => focusFile(entry.id));
    row.addEventListener('dragstart', () => { dragSourceId = entry.id; row.classList.add('dragging'); });
    row.addEventListener('dragend', () => row.classList.remove('dragging'));
    row.addEventListener('dragover', (e) => e.preventDefault());
    row.addEventListener('drop', (e) => {
      e.preventDefault();
      if (!dragSourceId || dragSourceId === entry.id) return;
      const fromIdx = loadedFiles.findIndex((f) => f.id === dragSourceId);
      const toIdx = loadedFiles.findIndex((f) => f.id === entry.id);
      const [moved] = loadedFiles.splice(fromIdx, 1);
      loadedFiles.splice(toIdx, 0, moved);
      renderFileList();
    });

    list.appendChild(row);
  }

  document.getElementById('feLoadedCount').textContent = `${loadedFiles.length} File(s) Loaded`;

  // §9.3 — counted off the Loaded list only, not the Queue. Read live off
  // in-memory state (entry.needs_review, set lazily on focus below, or
  // cleared immediately by confirmSoIssue()) — not a save round-trip.
  const lowConfCount = loadedFiles.filter((f) => f.needs_review).length;
  document.getElementById('feLowConfidenceCount').textContent = `${lowConfCount} Low Confidence`;
}

async function focusFile(fileId) {
  if (searchOnlineOpen) return;  // Search Online modal traps focus (§9.6)
  focusedFileId = fileId;
  renderFileList();
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
  renderFileList();
  updateMismatchIndicator();
  updateActionButtonStates();
}

async function clearFileList() {
  await fetch('/api/editor/full/files/clear', { method: 'DELETE' });
  loadedFiles = [];
  focusedFileId = null;
  resetForm();
  resetViewer();
  renderFileList();
  updateMismatchIndicator();
  updateActionButtonStates();
}

// ══════════════════════════════════════════════════════════════════════════════
//  QUEUE (Column 1, lower)
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

  for (const entry of queueFiles) {
    const row = document.createElement('div');
    row.className = 'fe-file-row';

    const info = document.createElement('div');
    info.className = 'fe-file-row-info';
    const name = document.createElement('div');
    name.className = 'fe-file-row-name';
    name.textContent = entry.filename;
    const status = document.createElement('div');
    status.className = 'fe-file-row-status';
    status.textContent = xmlStatusLine(entry);
    info.appendChild(name);
    info.appendChild(status);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'folder-remove-btn';
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = () => removeFromQueue(entry.id);

    row.appendChild(info);
    row.appendChild(removeBtn);
    list.appendChild(row);
  }

  document.getElementById('feQueueCount').textContent = `${queueFiles.length} File(s) Loaded`;
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
  indicator.textContent = active ? 'Processing…' : 'Ready to process';
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
    payload.file_ids = loadedFiles.map((f) => f.id);
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
  // happens on every focus, so reading NeedsReview off it costs nothing
  // extra — the tradeoff is the count/border build up as files are visited
  // rather than being accurate immediately after a batch load.
  const entry = loadedFiles.find((f) => f.id === fileId);
  if (entry) {
    entry.needs_review = !!data.fields.NeedsReview;
    renderFileList();
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
  for (const checkbox of document.querySelectorAll('#fe-genre-grid input')) {
    checkbox.checked = existingGenres.includes(checkbox.value);
  }

  updateActionButtonStates();
}

function resetForm() {
  document.getElementById('feForm').reset();
  for (const checkbox of document.querySelectorAll('#fe-genre-grid input')) checkbox.checked = false;
  document.getElementById('fe-format').value = '';
  document.getElementById('fe-agerating').value = '';
  updateActionButtonStates();
}

function collectFormFields() {
  const genreNames = Array.from(document.querySelectorAll('#fe-genre-grid input:checked')).map((c) => c.value);
  return {
    Series: document.getElementById('fe-series').value,
    Title: document.getElementById('fe-title').value,
    Number: document.getElementById('fe-number').value,
    Year: document.getElementById('fe-year').value,
    Genre: genreNames.join(', '),
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

// EDITOR_SPEC.md §5.2 amended note — Process All only bulk-applies fields
// whose "Apply to: All" checkbox is checked; everything else is omitted so
// build_xml_from_fields() (backend) leaves each file's existing value
// untouched, the same way it already preserves any tag the editor doesn't
// expose at all. Issue Number has no checkbox — it's governed entirely by
// the separate increment_enabled/start_issue_no mechanism, never by this set.
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
  // Section 4.4's hard validation gate (block until Genre/Format/AgeRating are
  // valid) is explicitly scoped to the Basic Editor only — Full Editor relies
  // on the server-side check at process time instead (per-file errors are
  // reported without aborting the batch), so Queue/Process All are only
  // gated on whether there's anything to act on.
  document.getElementById('feQueueBtn').disabled = !focusedFileId;
  document.getElementById('feProcessAllBtn').disabled = loadedFiles.length === 0;
  document.getElementById('feProcessQueueBtn').disabled = queueFiles.length === 0;
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

// ══════════════════════════════════════════════════════════════════════════════
//  IMAGE VIEWER (Column 3)
// ══════════════════════════════════════════════════════════════════════════════

function wireImageViewer() {
  document.getElementById('fePrevBtn').onclick = () => changeViewerPage(-1);
  document.getElementById('feNextBtn').onclick = () => changeViewerPage(1);
  document.getElementById('feZoomInBtn').onclick = () => setZoom(viewerZoom + 0.25);
  document.getElementById('feZoomOutBtn').onclick = () => setZoom(viewerZoom - 0.25);
}

function resetViewer() {
  viewerFileId = null;
  viewerImageList = [];
  viewerPageNum = 0;
  viewerZoom = 1;
  document.getElementById('feViewerImg').hidden = true;
  document.getElementById('feViewerEmpty').hidden = false;
  document.getElementById('fePageInfo').textContent = '—';
  for (const id of ['fePrevBtn', 'feNextBtn', 'feZoomInBtn', 'feZoomOutBtn']) {
    document.getElementById(id).disabled = true;
  }
}

async function loadFileIntoViewer(fileId) {
  const res = await fetch(`/api/editor/full/files/${fileId}/preview`);
  if (!res.ok) { resetViewer(); return; }
  const data = await res.json();

  viewerFileId = fileId;
  viewerImageList = data.image_list;
  viewerPageNum = 0;
  viewerZoom = 1;

  const hasPages = viewerImageList.length > 0;
  document.getElementById('feViewerEmpty').hidden = hasPages;
  document.getElementById('feViewerImg').hidden = !hasPages;
  for (const id of ['feZoomInBtn', 'feZoomOutBtn']) document.getElementById(id).disabled = !hasPages;

  if (hasPages) await showViewerPage();
}

async function showViewerPage() {
  const res = await fetch(`/api/editor/full/files/${viewerFileId}/page/${viewerPageNum}`);
  if (!res.ok) return;
  const data = await res.json();

  const img = document.getElementById('feViewerImg');
  img.src = data.data;
  img.style.width = `${100 * viewerZoom}%`;

  document.getElementById('fePageInfo').textContent = `Page ${viewerPageNum + 1} of ${viewerImageList.length}`;
  document.getElementById('fePrevBtn').disabled = viewerPageNum === 0;
  document.getElementById('feNextBtn').disabled = viewerPageNum >= viewerImageList.length - 1;
}

function changeViewerPage(delta) {
  const next = viewerPageNum + delta;
  if (next < 0 || next >= viewerImageList.length) return;
  viewerPageNum = next;
  showViewerPage();
}

function setZoom(value) {
  viewerZoom = Math.max(0.5, Math.min(3, value));
  const img = document.getElementById('feViewerImg');
  if (!img.hidden) img.style.width = `${100 * viewerZoom}%`;
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
    return a.name.localeCompare(b.name);
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
// #feError / showError() / clearError() are unchanged — still used for short
// single-line cases (network errors, "select a file first", etc). This modal
// is only for Process All's per-file validation errors, which can be long and
// repetitive across many files.

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
    showError('Could not resolve the multiple XML files.');
    return;
  }
  const data = await res.json();
  populateForm(data.fields);

  // Refresh the file row's xml_files so the warning clears
  const entry = loadedFiles.find((f) => f.id === multiXmlFileId);
  if (entry) entry.xml_files = ['ComicInfo.xml'];
  renderFileList();
}

// ══════════════════════════════════════════════════════════════════════════════
//  SEARCH ONLINE — Select Series / Select Issue (EDITOR_SPEC.md §9)
//  One modal, two internal steps (not two stacked windows) — a "← Back to
//  Series" control returns to the cached soSeriesResults, no re-fetch.
// ══════════════════════════════════════════════════════════════════════════════

function wireSearchOnlineModal() {
  document.getElementById('feSearchOnlineBtn').onclick = openSearchOnline;
  document.getElementById('feSearchOnlineCloseBtn').onclick = closeSearchOnlineModal;
  document.getElementById('feSoBackBtn').onclick = () => showSoStep('series');
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
    // Matches CT's own taggerwindow.py::query_online() guard wording.
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

function renderSoSeriesTable() {
  const tbody = document.getElementById('feSoSeriesTbody');
  tbody.innerHTML = '';
  document.getElementById('feSoSeriesCover').src = '';
  document.getElementById('feSoSeriesDescription').innerHTML = '';

  if (!soSeriesResults.length) {
    tbody.innerHTML = '<tr><td colspan="4">No results found.</td></tr>';
    return;
  }

  for (const series of soSeriesResults) {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${escapeHtml(series.name)}</td><td>${series.start_year || ''}</td>` +
      `<td>${series.count_of_issues != null ? series.count_of_issues : ''}</td><td>${escapeHtml(series.publisher)}</td>`;
    row.addEventListener('click', () => previewSoSeries(series, row));
    row.addEventListener('dblclick', () => proceedToSoIssues(series.id));
    tbody.appendChild(row);
  }
  previewSoSeries(soSeriesResults[0], tbody.firstElementChild);
}

function previewSoSeries(series, row) {
  document.querySelectorAll('#feSoSeriesTbody tr').forEach((r) => r.classList.remove('selected'));
  if (row) row.classList.add('selected');
  document.getElementById('feSoSeriesCover').src = series.image_url || '';
  document.getElementById('feSoSeriesDescription').innerHTML = series.description || '';
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
  document.getElementById('feSoIssueDescription').innerHTML = '';

  if (!issues.length) {
    tbody.innerHTML = '<tr><td colspan="3">No issues found.</td></tr>';
    return;
  }

  for (const issue of issues) {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${escapeHtml(issue.number)}</td><td>${escapeHtml(issue.date)}</td><td>${escapeHtml(issue.title)}</td>`;
    row.addEventListener('click', () => previewSoIssue(issue, row));
    row.addEventListener('dblclick', () => confirmSoIssue(issue.issue_id));
    tbody.appendChild(row);
  }
  previewSoIssue(issues[0], tbody.firstElementChild);
}

function previewSoIssue(issue, row) {
  document.querySelectorAll('#feSoIssueTbody tr').forEach((r) => r.classList.remove('selected'));
  if (row) row.classList.add('selected');
  document.getElementById('feSoIssueCover').src = issue.cover_url || '';
  document.getElementById('feSoIssueDescription').innerHTML = issue.description || '';
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
  // BlackAndWhite/PageCount (never in the mapped set) are left untouched
  // since they're preserved from the current form state underneath.
  populateForm({ ...collectFormFields(), ...data.fields });
  closeSearchOnlineModal();
  clearNeedsReviewIndicatorFor(focusedFileId);
}

// §9.7 — clears the border/count immediately in frontend in-memory state;
// the NeedsReview XML tag itself only actually clears on the file's next
// real save (Process Queue/Process All already send NeedsReview: "").
function clearNeedsReviewIndicatorFor(fileId) {
  const entry = loadedFiles.find((f) => f.id === fileId);
  if (entry) entry.needs_review = false;
  renderFileList();
}
