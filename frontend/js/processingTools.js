// ── Processing Tools (admin-spec-section-12-processing-tools.md §12) ───────
// File Rename (§12.1) today; Convert Archives/Convert Images/Processing
// Folder Automation join this file as they're built (§12.2-§12.4).

async function postJSON(path, body) {
  const res = await fetch(`${API}/admin${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

function showPtSummary(title, headline, errors) {
  document.getElementById('ptSummaryTitle').textContent = title;
  document.getElementById('ptSummaryHeadline').textContent = headline;
  const list = document.getElementById('ptSummaryErrorList');
  list.innerHTML = '';
  for (const e of errors) {
    const li = document.createElement('li');
    li.textContent = e;
    list.appendChild(li);
  }
  document.getElementById('ptSummaryOverlay').hidden = false;
}

// ── File Rename (§12.1) ──────────────────────────────────────────────────

const RENAME_FIELDS = [
  { dataKey: 'series',      id: 'Series' },
  { dataKey: 'issue_title', id: 'Title'  },
  { dataKey: 'issue_num',   id: 'Issue'  },
  { dataKey: 'year',        id: 'Year'   },
];

let renameFiles = [];          // working set: [{id, filename, path, parsed}]
let renameSelectedId = null;
let renamePreviewMap = {};     // file_id -> true, for files currently in the Preview list
let renamePreviewNames = {};   // file_id -> last computed new filename
let renameFileOverrides = {};  // file_id -> {dataKey: value} — File-checked edits, per file

function renameFieldEls(f) {
  return {
    input: document.getElementById(`rename${f.id}Input`),
    file:  document.getElementById(`rename${f.id}File`),
    all:   document.getElementById(`rename${f.id}All`),
  };
}

function isRenameBatchMode() {
  return RENAME_FIELDS.some(f => renameFieldEls(f).all.checked);
}

function currentRenameBatchOptions() {
  const autoIncrementEl = document.getElementById('renameAutoIncrement');
  const styleEl = document.querySelector('input[name="renameCaseStyle"]:checked');
  return {
    auto_increment: autoIncrementEl.checked && !autoIncrementEl.disabled,
    title_style: styleEl && styleEl.value ? styleEl.value : null,
  };
}

function updateRenameAutoIncrementAvailability() {
  const issueAllChecked = renameFieldEls(RENAME_FIELDS[2]).all.checked; // Issue
  const cb = document.getElementById('renameAutoIncrement');
  cb.disabled = !issueAllChecked;
  if (!issueAllChecked) cb.checked = false;
}

// Merge rule for one file: All-checked field -> shared typed value for
// every file; File-checked field -> typed value only for the currently
// selected file; otherwise -> that file's own parsed baseline.
function computeRenameFileData(entry) {
  const data = {};
  for (const f of RENAME_FIELDS) {
    const els = renameFieldEls(f);
    if (els.all.checked) {
      data[f.dataKey] = els.input.value;
    } else if (els.file.checked && entry.id === renameSelectedId) {
      data[f.dataKey] = els.input.value;
    } else {
      data[f.dataKey] = entry.parsed[f.dataKey] || '';
    }
  }
  return data;
}

async function handleRenameFieldChange() {
  updateRenameAutoIncrementAvailability();
  const batchMode = isRenameBatchMode();
  const anyFileChecked = RENAME_FIELDS.some(f => renameFieldEls(f).file.checked);
  const batchOptions = currentRenameBatchOptions();

  if (batchMode && batchOptions.auto_increment) {
    // Auto-Increment needs one shared call across the whole ordered list so
    // the backend can compute sequential numbers (§12.1.4) — a File-scoped
    // per-file override doesn't combine with sequential numbering, an
    // inherently ambiguous combination the spec doesn't ask for.
    renamePreviewMap = {};
    const renameData = {};
    for (const f of RENAME_FIELDS) {
      const els = renameFieldEls(f);
      renameData[f.dataKey] = els.all.checked ? els.input.value : '';
    }
    const fileIds = renameFiles.map(x => x.id);
    if (fileIds.length) {
      const res = await postJSON('/rename/preview', { file_ids: fileIds, rename_data: renameData, batch_options: batchOptions });
      for (const p of res.previews) { renamePreviewNames[p.file_id] = p.new_name; renamePreviewMap[p.file_id] = true; }
    }
  } else if (batchMode) {
    renamePreviewMap = {};
    for (const entry of renameFiles) {
      const renameData = computeRenameFileData(entry);
      const res = await postJSON('/rename/preview', { file_ids: [entry.id], rename_data: renameData, batch_options: { title_style: batchOptions.title_style } });
      renamePreviewNames[entry.id] = res.previews[0].new_name;
      renamePreviewMap[entry.id] = true;
    }
  } else if (anyFileChecked && renameSelectedId) {
    const entry = renameFiles.find(x => x.id === renameSelectedId);
    if (entry) {
      const renameData = computeRenameFileData(entry);
      const overrides = {};
      for (const f of RENAME_FIELDS) {
        if (renameFieldEls(f).file.checked) overrides[f.dataKey] = renameFieldEls(f).input.value;
      }
      renameFileOverrides[renameSelectedId] = overrides;
      const res = await postJSON('/rename/preview', { file_ids: [renameSelectedId], rename_data: renameData, batch_options: { title_style: batchOptions.title_style } });
      renamePreviewNames[renameSelectedId] = res.previews[0].new_name;
      renamePreviewMap[renameSelectedId] = true;
    }
  }

  renderRenamePreviewList();
  renderRenameFileList();
}

function selectRenameFile(id) {
  renameSelectedId = id;
  const entry = renameFiles.find(x => x.id === id);
  if (!entry) return;
  const overrides = renameFileOverrides[id] || {};
  for (const f of RENAME_FIELDS) {
    const els = renameFieldEls(f);
    els.all.checked = false;
    if (f.dataKey in overrides) {
      els.input.value = overrides[f.dataKey];
      els.file.checked = true;
    } else {
      els.input.value = entry.parsed[f.dataKey] || '';
      els.file.checked = false;
    }
  }
  renderRenameFileList();
}

function moveRenameFile(id, dir) {
  const idx = renameFiles.findIndex(x => x.id === id);
  const newIdx = idx + dir;
  if (idx === -1 || newIdx < 0 || newIdx >= renameFiles.length) return;
  [renameFiles[idx], renameFiles[newIdx]] = [renameFiles[newIdx], renameFiles[idx]];
  renderRenameFileList();
  if (currentRenameBatchOptions().auto_increment) handleRenameFieldChange();
}

function renderRenameFileList() {
  const list = document.getElementById('renameFileList');
  list.innerHTML = '';
  document.getElementById('renameLoadedCount').textContent =
    `${renameFiles.length} file${renameFiles.length === 1 ? '' : 's'} loaded`;

  renameFiles.forEach((entry, idx) => {
    const row = document.createElement('div');
    row.className = 'pt-rename-file-row'
      + (entry.id === renameSelectedId ? ' selected' : '')
      + (renamePreviewMap[entry.id] ? ' in-preview' : '');

    const name = document.createElement('span');
    name.className = 'pt-rename-file-name';
    name.textContent = entry.filename;
    row.appendChild(name);

    const upBtn = document.createElement('button');
    upBtn.type = 'button'; upBtn.className = 'pt-reorder-btn'; upBtn.textContent = '↑';
    upBtn.disabled = idx === 0;
    upBtn.addEventListener('click', (e) => { e.stopPropagation(); moveRenameFile(entry.id, -1); });

    const downBtn = document.createElement('button');
    downBtn.type = 'button'; downBtn.className = 'pt-reorder-btn'; downBtn.textContent = '↓';
    downBtn.disabled = idx === renameFiles.length - 1;
    downBtn.addEventListener('click', (e) => { e.stopPropagation(); moveRenameFile(entry.id, 1); });

    row.append(upBtn, downBtn);
    row.addEventListener('click', () => selectRenameFile(entry.id));
    list.appendChild(row);
  });
}

function renderRenamePreviewList() {
  const list = document.getElementById('renamePreviewList');
  list.innerHTML = '';
  const ids = Object.keys(renamePreviewMap);
  if (!ids.length) {
    list.innerHTML = '<p class="admin-empty-hint">No pending changes.</p>';
    return;
  }
  for (const id of ids) {
    const entry = renameFiles.find(x => x.id === id);
    if (!entry) continue;
    const row = document.createElement('div');
    row.className = 'pt-preview-row';
    row.textContent = `${entry.filename} → ${renamePreviewNames[id] || '…'}`;
    list.appendChild(row);
  }
}

function clearRenamePreview() {
  renamePreviewMap = {};
  renamePreviewNames = {};
  renameFileOverrides = {};
  renderRenamePreviewList();
  renderRenameFileList();
}

function openRenameBrowse() {
  openFilePicker({
    browseUrl: `${API}/admin/rename/browse`,
    drivesUrl: `${API}/admin/rename/drives`,
    mode: 'files',
    title: 'Choose Files to Rename',
    onConfirm: addRenameFiles,
  });
}

async function addRenameFiles(paths) {
  const data = await postJSON('/rename/files/add', { file_paths: paths });
  for (const f of data.files || []) renameFiles.push(f);
  renderRenameFileList();
}

async function clearRenameFiles() {
  await fetch(`${API}/admin/rename/files/clear`, { method: 'DELETE' });
  renameFiles = [];
  renameSelectedId = null;
  clearRenamePreview();
}

async function applyRename() {
  const items = Object.keys(renamePreviewMap)
    .filter(id => renamePreviewNames[id])
    .map(id => ({ file_id: id, new_name: renamePreviewNames[id] }));
  if (!items.length) {
    showToast('Nothing in the preview list to rename', true);
    return;
  }

  const res = await fetch(`${API}/admin/rename/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  });
  const data = await res.json();

  showPtSummary(
    'File Rename',
    `Renamed ${data.renamed} of ${data.total} files`,
    data.results.filter(r => !r.success).map(r => `${r.old_name || r.file_id}: ${r.error}`)
  );

  for (const r of data.results) {
    if (r.success) {
      delete renamePreviewMap[r.file_id];
      delete renamePreviewNames[r.file_id];
      delete renameFileOverrides[r.file_id];
      renameFiles = renameFiles.filter(x => x.id !== r.file_id);
    }
  }
  if (renameSelectedId && !renameFiles.find(x => x.id === renameSelectedId)) renameSelectedId = null;
  renderRenameFileList();
  renderRenamePreviewList();
}

function initRenameTool() {
  document.getElementById('renameBrowseBtn').addEventListener('click', openRenameBrowse);
  document.getElementById('renameClearBtn').addEventListener('click', clearRenameFiles);
  document.getElementById('renameClearPreviewBtn').addEventListener('click', clearRenamePreview);
  document.getElementById('renameApplyBtn').addEventListener('click', applyRename);

  for (const f of RENAME_FIELDS) {
    const els = renameFieldEls(f);
    els.input.addEventListener('input', handleRenameFieldChange);
    els.file.addEventListener('change', handleRenameFieldChange);
    els.all.addEventListener('change', handleRenameFieldChange);
  }
  document.getElementById('renameAutoIncrement').addEventListener('change', handleRenameFieldChange);
  document.querySelectorAll('input[name="renameCaseStyle"]').forEach(r => r.addEventListener('change', handleRenameFieldChange));

  renderRenameFileList();
  renderRenamePreviewList();
}

// ── Convert Archives (§11.2) ─────────────────────────────────────────────

let convertFiles = [];       // working set: [{id, filename, path}]
let convertPollTimer = null;

function currentConvertFromFormat() {
  const el = document.querySelector('input[name="convertFromFormat"]:checked');
  return el ? el.value : 'cbr';
}

function renderConvertFileList() {
  const list = document.getElementById('convertFileList');
  list.innerHTML = '';
  document.getElementById('convertLoadedCount').textContent =
    `${convertFiles.length} file${convertFiles.length === 1 ? '' : 's'} loaded`;
  for (const entry of convertFiles) {
    const row = document.createElement('div');
    row.className = 'pt-rename-file-row';
    const name = document.createElement('span');
    name.className = 'pt-rename-file-name';
    name.textContent = entry.filename;
    row.appendChild(name);
    list.appendChild(row);
  }
}

function openConvertBrowse() {
  const fromFormat = currentConvertFromFormat();
  openFilePicker({
    browseUrl: `${API}/admin/convert/browse?from_format=${fromFormat}`,
    drivesUrl: `${API}/admin/convert/drives`,
    mode: 'files',
    title: `Choose ${fromFormat.toUpperCase()} Files to Convert`,
    onConfirm: addConvertFiles,
  });
}

async function addConvertFiles(paths) {
  const data = await postJSON('/convert/files/add', { file_paths: paths });
  for (const f of data.files || []) convertFiles.push(f);
  renderConvertFileList();
}

async function clearConvertFiles() {
  await fetch(`${API}/admin/convert/files/clear`, { method: 'DELETE' });
  convertFiles = [];
  renderConvertFileList();
}

async function runConvert() {
  if (!convertFiles.length) {
    showToast('No files loaded to convert', true);
    return;
  }
  const res = await postJSON('/convert/run', { from_format: currentConvertFromFormat() });
  if (res.started === false) {
    showToast(res.message || 'Could not start conversion', true);
    return;
  }
  document.getElementById('convertRunBtn').disabled = true;
  document.getElementById('convertProgressWrap').hidden = false;
  pollConvertStatus();
}

async function pollConvertStatus() {
  const status = await (await fetch(`${API}/admin/convert/status`)).json();
  const label = document.getElementById('convertProgressLabel');
  const bar = document.getElementById('convertProgressBar');

  if (status.running) {
    label.textContent = `Converting file ${status.current_file_index + 1} of ${status.total_files} — ${status.current_filename}`;
    bar.max = status.total_files || 1;
    bar.value = status.current_file_index;
    convertPollTimer = setTimeout(pollConvertStatus, 500);
    return;
  }

  clearTimeout(convertPollTimer);
  document.getElementById('convertRunBtn').disabled = false;
  document.getElementById('convertProgressWrap').hidden = true;

  if (!status.results.length) return; // nothing ran (e.g. already-idle poll)

  const ok = status.results.filter(r => r.status !== 'failed').length;
  const errors = status.results
    .filter(r => r.status === 'failed')
    .map(r => `${r.filename}: ${r.error}`);
  const warnings = status.results
    .filter(r => r.status === 'success_with_warning')
    .map(r => `${r.filename} → ${r.new_filename}: ${r.pages_skipped} pages skipped, original kept as .bak`);

  showPtSummary('Convert Archives', `Converted ${ok} of ${status.results.length} files`, [...warnings, ...errors]);

  // Reload working set — successes were removed server-side, failures remain.
  const files = await (await fetch(`${API}/admin/convert/files`)).json();
  convertFiles = files.files || [];
  renderConvertFileList();
}

function initConvertTool() {
  document.getElementById('convertBrowseBtn').addEventListener('click', openConvertBrowse);
  document.getElementById('convertClearBtn').addEventListener('click', clearConvertFiles);
  document.getElementById('convertRunBtn').addEventListener('click', runConvert);
  document.querySelectorAll('input[name="convertFromFormat"]').forEach(r =>
    r.addEventListener('change', clearConvertFiles) // switching format invalidates the loaded (format-filtered) list
  );
  renderConvertFileList();
}

// ── Convert Images (§11.3) ───────────────────────────────────────────────

let convertImagesFiles = [];
let convertImagesPollTimer = null;

function renderConvertImagesFileList() {
  const list = document.getElementById('convertImagesFileList');
  list.innerHTML = '';
  document.getElementById('convertImagesLoadedCount').textContent =
    `${convertImagesFiles.length} file${convertImagesFiles.length === 1 ? '' : 's'} loaded`;
  for (const entry of convertImagesFiles) {
    const row = document.createElement('div');
    row.className = 'pt-rename-file-row';
    const name = document.createElement('span');
    name.className = 'pt-rename-file-name';
    name.textContent = entry.filename;
    row.appendChild(name);
    list.appendChild(row);
  }
}

function openConvertImagesBrowse() {
  openFilePicker({
    browseUrl: `${API}/admin/convert-images/browse`,
    drivesUrl: `${API}/admin/convert-images/drives`,
    mode: 'files',
    title: 'Choose CBZ/CBR Files to Convert',
    onConfirm: addConvertImagesFiles,
  });
}

async function addConvertImagesFiles(paths) {
  const data = await postJSON('/convert-images/files/add', { file_paths: paths });
  for (const f of data.files || []) convertImagesFiles.push(f);
  renderConvertImagesFileList();
}

async function clearConvertImagesFiles() {
  await fetch(`${API}/admin/convert-images/files/clear`, { method: 'DELETE' });
  convertImagesFiles = [];
  renderConvertImagesFileList();
}

async function runConvertImages() {
  if (!convertImagesFiles.length) {
    showToast('No files loaded to convert', true);
    return;
  }
  const lossless = document.getElementById('convertImagesLossless').checked;
  const quality = parseInt(document.getElementById('convertImagesQuality').value, 10);
  const res = await postJSON('/convert-images/run', { lossless, quality });
  if (res.started === false) {
    showToast(res.message || 'Could not start conversion', true);
    return;
  }
  document.getElementById('convertImagesRunBtn').disabled = true;
  document.getElementById('convertImagesProgressWrap').hidden = false;
  pollConvertImagesStatus();
}

async function pollConvertImagesStatus() {
  const status = await (await fetch(`${API}/admin/convert-images/status`)).json();
  const label = document.getElementById('convertImagesProgressLabel');
  const bar = document.getElementById('convertImagesProgressBar');

  if (status.running) {
    label.textContent = `Converting file ${status.current_file_index + 1} of ${status.total_files} — ${status.current_filename}`;
    bar.max = status.total_files || 1;
    bar.value = status.current_file_index;
    convertImagesPollTimer = setTimeout(pollConvertImagesStatus, 500);
    return;
  }

  clearTimeout(convertImagesPollTimer);
  document.getElementById('convertImagesRunBtn').disabled = false;
  document.getElementById('convertImagesProgressWrap').hidden = true;

  if (!status.results.length) return;

  const ok = status.results.filter(r => r.status !== 'failed').length;
  const errors = status.results
    .filter(r => r.status === 'failed')
    .map(r => `${r.filename}: ${r.error}`);
  const warnings = status.results
    .filter(r => r.status === 'success_with_warning')
    .map(r => `${r.filename} → ${r.new_filename}: ${r.images_skipped} images skipped, original kept as .bak`);

  showPtSummary('Convert Images', `Converted ${ok} of ${status.results.length} files`, [...warnings, ...errors]);

  const files = await (await fetch(`${API}/admin/convert-images/files`)).json();
  convertImagesFiles = files.files || [];
  renderConvertImagesFileList();
}

function initConvertImagesTool() {
  document.getElementById('convertImagesBrowseBtn').addEventListener('click', openConvertImagesBrowse);
  document.getElementById('convertImagesClearBtn').addEventListener('click', clearConvertImagesFiles);
  document.getElementById('convertImagesRunBtn').addEventListener('click', runConvertImages);
  document.getElementById('convertImagesQuality').addEventListener('input', (e) => {
    document.getElementById('convertImagesQualityValue').textContent = e.target.value;
  });
  document.getElementById('convertImagesLossless').addEventListener('change', (e) => {
    document.getElementById('convertImagesQuality').disabled = e.target.checked;
  });
  renderConvertImagesFileList();
}

// ── Processing Folder Automation (§11.4) ─────────────────────────────────

let pfPollTimer = null;

async function loadProcessingFolderConfig() {
  const cfg = await (await fetch(`${API}/admin/processing-folder/config`)).json();

  document.getElementById('pfFolderInput').value = cfg.processing_folder_path || '';
  document.getElementById('pfConvertArchivesEnabled').checked = cfg.processing_folder_convert_archives_enabled;
  document.querySelector(`input[name="pfConvertArchivesFrom"][value="${cfg.processing_folder_convert_archives_from}"]`).checked = true;
  document.getElementById('pfConvertImagesEnabled').checked = cfg.processing_folder_convert_images_enabled;
  document.getElementById('pfConvertImagesLossless').checked = cfg.processing_folder_convert_images_lossless;
  document.getElementById('pfConvertImagesQuality').value = cfg.processing_folder_convert_images_quality;
  document.getElementById('pfConvertImagesQualityValue').textContent = cfg.processing_folder_convert_images_quality;
  document.getElementById('pfScheduleSelect').value = cfg.processing_folder_schedule;
  document.getElementById('pfScheduleTime').value = cfg.processing_folder_schedule_time;
  document.getElementById('pfScheduleDay').value = cfg.processing_folder_schedule_day;

  const hint = document.getElementById('pfNextRunHint');
  hint.textContent = cfg.next_processing_run
    ? `Next run: ${new Date(cfg.next_processing_run).toLocaleString()}`
    : (cfg.processing_folder_schedule === 'off' ? '' : 'Next run time will be computed shortly.');
}

async function savePfSetting(payload) {
  await postJSON('/processing-folder/config', payload);
}

function openPfBrowse() {
  openFilePicker({
    browseUrl: `${API}/admin/processing-folder/browse`,
    drivesUrl: `${API}/admin/processing-folder/drives`,
    mode: 'folder',
    title: 'Choose Processing Folder',
    onConfirm: async ([folderPath]) => {
      document.getElementById('pfFolderInput').value = folderPath;
      await savePfSetting({ processing_folder_path: folderPath });
      showToast('Processing folder saved');
    },
  });
}

async function runPfNow() {
  const res = await postJSON('/processing-folder/run', {});
  // Two distinct failure shapes: a rejected-but-200 response (`started:
  // false`, e.g. already running) vs. a raised HTTPException (400 "No
  // stages enabled"), which FastAPI serializes as `{detail: "..."}`, not
  // `{message: ...}` — postJSON doesn't check res.ok, so both land here.
  if (res.started === false || res.detail) {
    showToast(res.detail || res.message || 'Could not start run', true);
    return;
  }
  document.getElementById('pfRunNowBtn').disabled = true;
  document.getElementById('pfProgressWrap').hidden = false;
  pollPfStatus();
}

async function pollPfStatus() {
  const status = await (await fetch(`${API}/admin/processing-folder/status`)).json();
  const label = document.getElementById('pfProgressLabel');

  if (status.running) {
    label.textContent = status.current_stage
      ? `Running — ${status.current_stage === 'convert_archives' ? 'Convert Archives' : 'Convert Images'}`
      : 'Running…';
    pfPollTimer = setTimeout(pollPfStatus, 700);
    return;
  }

  clearTimeout(pfPollTimer);
  document.getElementById('pfRunNowBtn').disabled = false;
  document.getElementById('pfProgressWrap').hidden = true;

  if (status.error) {
    showToast(status.error, true);
    return;
  }
  if (!Object.keys(status.stage_results).length) return;

  const lines = [];
  for (const [stage, results] of Object.entries(status.stage_results)) {
    if (stage.endsWith('_error')) {
      lines.push(`${stage.replace('_error', '')} stage failed: ${results}`);
      continue;
    }
    const ok = results.filter(r => r.status !== 'failed').length;
    lines.push(`${stage === 'convert_archives' ? 'Convert Archives' : 'Convert Images'}: ${ok} of ${results.length} succeeded`);
    for (const r of results.filter(r => r.status === 'failed')) {
      lines.push(`  ${r.filename}: ${r.error}`);
    }
  }
  showPtSummary('Processing Folder Automation', 'Run complete', lines);
}

function initProcessingFolderTool() {
  document.getElementById('pfBrowseBtn').addEventListener('click', openPfBrowse);
  document.getElementById('pfRunNowBtn').addEventListener('click', runPfNow);

  document.getElementById('pfConvertArchivesEnabled').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_archives_enabled: e.target.checked }));
  document.querySelectorAll('input[name="pfConvertArchivesFrom"]').forEach(r =>
    r.addEventListener('change', (e) => savePfSetting({ processing_folder_convert_archives_from: e.target.value })));
  document.getElementById('pfConvertImagesEnabled').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_images_enabled: e.target.checked }));
  document.getElementById('pfConvertImagesLossless').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_images_lossless: e.target.checked }));
  document.getElementById('pfConvertImagesQuality').addEventListener('input', (e) => {
    document.getElementById('pfConvertImagesQualityValue').textContent = e.target.value;
  });
  document.getElementById('pfConvertImagesQuality').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_images_quality: e.target.value }));

  document.getElementById('pfSaveScheduleBtn').addEventListener('click', async () => {
    await savePfSetting({
      processing_folder_schedule: document.getElementById('pfScheduleSelect').value,
      processing_folder_schedule_time: document.getElementById('pfScheduleTime').value,
      processing_folder_schedule_day: document.getElementById('pfScheduleDay').value,
    });
    showToast('Schedule saved');
    await loadProcessingFolderConfig();
  });

  loadProcessingFolderConfig();
}

// ── Local-only gating (§12 shared notes) ────────────────────────────────
// Hooked from admin.js's refreshAuthSettingsUi(), which already fetches
// GET /api/admin/auth/status once per refresh — avoids a second fetch here.
function refreshProcessingToolsLocalGate(isLocal) {
  const hint = document.getElementById('ptLocalOnlyHint');
  const section = document.getElementById('processingToolsSection');
  if (!hint || !section) return;
  hint.hidden = isLocal;
  section.querySelectorAll('input, button, select, textarea').forEach(el => {
    if (el.id === 'ptLocalOnlyHint') return;
    el.disabled = !isLocal;
  });
}

function initProcessingTools() {
  if (!document.getElementById('renameToolCard')) return;
  document.getElementById('ptSummaryCloseBtn').addEventListener('click', () => {
    document.getElementById('ptSummaryOverlay').hidden = true;
  });
  initRenameTool();
  initConvertTool();
  initConvertImagesTool();
  initProcessingFolderTool();
}

document.addEventListener('DOMContentLoaded', initProcessingTools);
