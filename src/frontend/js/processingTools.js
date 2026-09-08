// ── Processing Tools (admin-spec-section-12-processing-tools.md §12) ───────
// File Rename (§12.1) today; Convert Archives/Convert Images/Processing
// Folder Automation join this file as they're built (§12.2-§12.4).

// Preserves the pre-consolidation contract: always resolves with the parsed
// body, even on a non-2xx response (callers inspect fields like `.started`/
// `.message` themselves rather than relying on HTTP status) — only a genuine
// network failure (no body to fall back to) still throws.
async function postJSON(path, body) {
  try {
    return await apiFetch(`/admin${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (err) {
    if (err.body) return err.body;
    throw err;
  }
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

  // Every tool's run funnels through here on completion — refresh the
  // Needs Attention banner (admin.js) so a critical_failure from this run
  // shows up immediately, not just on the next page load.
  if (typeof loadNeedsAttention === 'function') loadNeedsAttention();
}

// ── File Rename (§12.1) ──────────────────────────────────────────────────

const RENAME_FIELDS = [
  { dataKey: 'series',      id: 'Series' },
  { dataKey: 'issue_num',   id: 'Issue'  },
  { dataKey: 'issue_title', id: 'Title'  },
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
  const issueAllChecked = renameFieldEls(RENAME_FIELDS[1]).all.checked; // Issue
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

function handleRenameFieldChange() {
  updateRenameAutoIncrementAvailability();
}

// Adds the current edit-panel state to the queue (renamePreviewMap /
// renamePreviewNames), which also serves as the Preview list. Only fires on
// an explicit "Add to Queue" click — fields no longer auto-preview on edit.
async function addRenameToQueue() {
  const batchMode = isRenameBatchMode();
  const anyFileChecked = RENAME_FIELDS.some(f => renameFieldEls(f).file.checked);
  const batchOptions = currentRenameBatchOptions();

  if (batchMode && batchOptions.auto_increment) {
    // preview_renames() (backend) takes one shared rename_data dict per
    // call — any field not in it comes back blank, it has no per-file
    // fallback to that file's own parsed baseline. So this can't be one
    // shared call across every file the way the old design assumed (that
    // wiped Series/Title/Year the moment Auto-Increment was on). Instead,
    // go per-file like the plain batchMode branch below — computing each
    // file's own baseline/File/All values via computeRenameFileData — and
    // just override the Issue value with a sequential number computed
    // here on the frontend (mirrors preview_renames()'s own
    // `num_start + idx`), based on the file's position in the current
    // loaded-files order.
    const issueField = RENAME_FIELDS.find(f => f.dataKey === 'issue_num');
    const startNum = parseInt(renameFieldEls(issueField).input.value, 10);
    for (let idx = 0; idx < renameFiles.length; idx++) {
      const entry = renameFiles[idx];
      const renameData = computeRenameFileData(entry);
      if (!Number.isNaN(startNum)) renameData.issue_num = String(startNum + idx);
      const res = await postJSON('/rename/preview', { file_ids: [entry.id], rename_data: renameData, batch_options: { title_style: batchOptions.title_style } });
      renamePreviewNames[entry.id] = res.previews[0].new_name;
      renamePreviewMap[entry.id] = true;
    }
  } else if (batchMode) {
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
  } else {
    showToast('Check a File or All box first', true);
    return;
  }

  renderRenamePreviewList();
  renderRenameFileList();
}

function removeFromRenameQueue(id) {
  delete renamePreviewMap[id];
  delete renamePreviewNames[id];
  delete renameFileOverrides[id];
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

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'pt-remove-btn';
    removeBtn.textContent = '×';
    removeBtn.title = 'Remove file';
    removeBtn.addEventListener('click', (e) => { e.stopPropagation(); removeLoadedRenameFile(entry.id); });

    row.append(upBtn, downBtn, removeBtn);
    row.addEventListener('click', () => selectRenameFile(entry.id));
    list.appendChild(row);
  });
}

function renderRenamePreviewList() {
  const list = document.getElementById('renamePreviewList');
  list.innerHTML = '';
  const ids = Object.keys(renamePreviewMap);
  if (!ids.length) {
    list.innerHTML = '<p class="admin-empty-hint">No files queued.</p>';
    return;
  }
  for (const id of ids) {
    const entry = renameFiles.find(x => x.id === id);
    if (!entry) continue;
    const row = document.createElement('div');
    row.className = 'pt-preview-row';

    const name = document.createElement('span');
    name.className = 'pt-preview-name';
    name.textContent = renamePreviewNames[id] || '…';
    row.appendChild(name);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'pt-remove-btn';
    removeBtn.textContent = '×';
    removeBtn.title = 'Remove from queue';
    removeBtn.addEventListener('click', (e) => { e.stopPropagation(); removeFromRenameQueue(id); });
    row.appendChild(removeBtn);

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

function resetRenameFieldsPanel() {
  for (const f of RENAME_FIELDS) {
    const els = renameFieldEls(f);
    els.input.value = '';
    els.file.checked = false;
    els.all.checked = false;
  }
  updateRenameAutoIncrementAvailability();
}

async function removeLoadedRenameFile(id) {
  await apiFetch(`/admin/rename/files/${id}`, { method: 'DELETE' });
  renameFiles = renameFiles.filter(x => x.id !== id);
  delete renamePreviewMap[id];
  delete renamePreviewNames[id];
  delete renameFileOverrides[id];
  if (renameSelectedId === id) {
    renameSelectedId = null;
    resetRenameFieldsPanel();
  }
  renderRenameFileList();
  renderRenamePreviewList();
}

function openRenameBrowse() {
  openFilePicker({
    browseUrl: `/admin/rename/browse`,
    drivesUrl: `/admin/rename/drives`,
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
  await apiFetch(`/admin/rename/files/clear`, { method: 'DELETE' });
  renameFiles = [];
  renameSelectedId = null;
  resetRenameFieldsPanel();
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

  const data = await apiFetch(`/admin/rename/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  });

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
  document.getElementById('renameAddToQueueBtn').addEventListener('click', addRenameToQueue);
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
    browseUrl: `/admin/convert/browse?from_format=${fromFormat}`,
    drivesUrl: `/admin/convert/drives`,
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
  await apiFetch(`/admin/convert/files/clear`, { method: 'DELETE' });
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
  const status = await apiFetch(`/admin/convert/status`);
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
  const files = await apiFetch(`/admin/convert/files`);
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
    browseUrl: `/admin/convert-images/browse`,
    drivesUrl: `/admin/convert-images/drives`,
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
  await apiFetch(`/admin/convert-images/files/clear`, { method: 'DELETE' });
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
  const status = await apiFetch(`/admin/convert-images/status`);
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

  const files = await apiFetch(`/admin/convert-images/files`);
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

const PF_STAGE_LABELS = {
  convert_archives: 'Convert Archives',
  ct_autotag: 'ComicTagger Auto-Tag',
  convert_images: 'Convert Images',
};

async function loadProcessingFolderConfig() {
  const cfg = await apiFetch(`/admin/processing-folder/config`);

  document.getElementById('pfFolderInput').value = cfg.processing_folder_path || '';
  document.getElementById('pfConvertArchivesEnabled').checked = cfg.processing_folder_convert_archives_enabled;
  document.querySelector(`input[name="pfConvertArchivesFrom"][value="${cfg.processing_folder_convert_archives_from}"]`).checked = true;
  document.getElementById('pfCtAutotagEnabled').checked = cfg.processing_folder_ct_autotag_enabled;
  document.getElementById('pfCtSaveLowConfidence').checked = cfg.processing_folder_ct_save_low_confidence;
  document.getElementById('pfCtMatchThreshold').value = cfg.processing_folder_ct_match_threshold;
  document.getElementById('pfCtMatchThresholdValue').textContent = cfg.processing_folder_ct_match_threshold;
  document.getElementById('pfComicVineKey').value = cfg.comicvine_api_key || '';
  document.getElementById('pfConvertImagesEnabled').checked = cfg.processing_folder_convert_images_enabled;
  document.getElementById('pfConvertImagesLossless').checked = cfg.processing_folder_convert_images_lossless;
  document.getElementById('pfConvertImagesQuality').value = cfg.processing_folder_convert_images_quality;
  document.getElementById('pfConvertImagesQualityValue').textContent = cfg.processing_folder_convert_images_quality;
  document.getElementById('pfScheduleSelect').value = cfg.processing_folder_schedule;
  document.getElementById('pfScheduleTime').value = cfg.processing_folder_schedule_time;
  document.getElementById('pfScheduleDay').value = cfg.processing_folder_schedule_day;
  updatePfScheduleFieldStates();

  const hint = document.getElementById('pfNextRunHint');
  hint.textContent = cfg.next_processing_run
    ? `Next run: ${new Date(cfg.next_processing_run).toLocaleString()}`
    : (cfg.processing_folder_schedule === 'off' ? '' : 'Next run time will be computed shortly.');
}

function updatePfScheduleFieldStates() {
  const schedule = document.getElementById('pfScheduleSelect').value;
  document.getElementById('pfScheduleTime').disabled = schedule === 'off';
  document.getElementById('pfScheduleDay').disabled = schedule !== 'weekly';
}

async function savePfSetting(payload) {
  await postJSON('/processing-folder/config', payload);
  showToast('Saved');
}

async function saveSchedule() {
  await savePfSetting({
    processing_folder_schedule: document.getElementById('pfScheduleSelect').value,
    processing_folder_schedule_time: document.getElementById('pfScheduleTime').value,
    processing_folder_schedule_day: document.getElementById('pfScheduleDay').value,
  });
  await loadProcessingFolderConfig();
}

function openPfBrowse() {
  openFilePicker({
    browseUrl: `/admin/processing-folder/browse`,
    drivesUrl: `/admin/processing-folder/drives`,
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
  const status = await apiFetch(`/admin/processing-folder/status`);
  const label = document.getElementById('pfProgressLabel');

  if (status.running) {
    label.textContent = status.current_stage
      ? `Running — ${PF_STAGE_LABELS[status.current_stage] || status.current_stage}`
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
    if (stage === 'ct_autotag') {
      // CT Auto-Tag's "success" status covers no_match/skipped-low-confidence
      // outcomes too (correctly -- the stage didn't error), so a plain
      // "N of M succeeded" line reads as "N got tagged" when it doesn't mean
      // that. Break out what actually happened per file instead.
      const tagged = results.filter(r => r.tags_written).length;
      const noMatch = results.filter(r => r.confidence === 'no_match').length;
      const skippedLow = results.filter(r => r.confidence === 'low_confidence' && !r.tags_written).length;
      const failed = results.filter(r => r.status === 'failed').length;
      lines.push(`ComicTagger Auto-Tag: ${tagged} tagged, ${noMatch} no match, ${skippedLow} low confidence skipped, ${failed} failed (of ${results.length})`);
      for (const r of results.filter(r => r.status === 'failed')) {
        lines.push(`  ${r.filename}: ${r.error}`);
      }
      continue;
    }
    const ok = results.filter(r => r.status !== 'failed').length;
    lines.push(`${PF_STAGE_LABELS[stage] || stage}: ${ok} of ${results.length} succeeded`);
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

  document.getElementById('pfCtAutotagEnabled').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_ct_autotag_enabled: e.target.checked }));
  document.getElementById('pfCtSaveLowConfidence').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_ct_save_low_confidence: e.target.checked }));
  document.getElementById('pfCtMatchThreshold').addEventListener('input', (e) => {
    document.getElementById('pfCtMatchThresholdValue').textContent = e.target.value;
  });
  document.getElementById('pfCtMatchThreshold').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_ct_match_threshold: e.target.value }));
  document.getElementById('pfComicVineKeyTestBtn').addEventListener('click', async () => {
    const key = document.getElementById('pfComicVineKey').value;
    const resultEl = document.getElementById('pfComicVineKeyResult');
    resultEl.textContent = 'Testing…';
    resultEl.className = 'admin-card-hint';
    const res = await postJSON('/processing-folder/comicvine-key/test', { comicvine_api_key: key });
    resultEl.textContent = res.message;
    resultEl.className = 'admin-card-hint ' + (res.valid ? 'admin-key-ok' : 'admin-backup-error');
  });

  document.getElementById('pfConvertImagesEnabled').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_images_enabled: e.target.checked }));
  document.getElementById('pfConvertImagesLossless').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_images_lossless: e.target.checked }));
  document.getElementById('pfConvertImagesQuality').addEventListener('input', (e) => {
    document.getElementById('pfConvertImagesQualityValue').textContent = e.target.value;
  });
  document.getElementById('pfConvertImagesQuality').addEventListener('change', (e) =>
    savePfSetting({ processing_folder_convert_images_quality: e.target.value }));

  document.getElementById('pfScheduleSelect').addEventListener('change', () => {
    updatePfScheduleFieldStates();
    saveSchedule();
  });
  document.getElementById('pfScheduleTime').addEventListener('change', saveSchedule);
  document.getElementById('pfScheduleDay').addEventListener('change', saveSchedule);

  loadProcessingFolderConfig();
}

// ── Folder Processing card: Sort by Filename (§11.5), Move Series Folders /
// Move Singles Folders (§11.7) ──────────────────────────────────────────
// One shared card/picker/Run button; the selected <option> in fsScriptSelect
// decides which endpoint Run/poll talk to. §11.5.6 anticipated this: "a
// second script is expected eventually, at which point this becomes a real
// dropdown with minimal rework."

let fsPollTimer = null;

const FS_SCRIPTS = {
  filename_sort: {
    label: 'Sort by Filename',
    browseUrl: `/admin/filename-sort/browse`,
    drivesUrl: `/admin/filename-sort/drives`,
    pickerTitle: 'Choose Folder to Sort',
    runPath: '/filename-sort/run',
    runBody: (folder) => ({ folder }),
    statusPath: () => '/filename-sort/status',
  },
  move_series: {
    label: 'Move Series Folders',
    browseUrl: `/admin/library-move/browse`,
    drivesUrl: `/admin/library-move/drives`,
    pickerTitle: 'Choose Folder Containing Series Folders to Move',
    runPath: '/library-move/run',
    runBody: (folder) => ({ folder, group: 'series' }),
    statusPath: () => '/library-move/status?group=series',
  },
  move_singles: {
    label: 'Move Singles Folders',
    browseUrl: `/admin/library-move/browse`,
    drivesUrl: `/admin/library-move/drives`,
    pickerTitle: 'Choose Folder Containing Singles Folders to Move',
    runPath: '/library-move/run',
    runBody: (folder) => ({ folder, group: 'singles' }),
    statusPath: () => '/library-move/status?group=singles',
  },
};

function currentFsScript() {
  return FS_SCRIPTS[document.getElementById('fsScriptSelect').value];
}

function openFsBrowse() {
  const script = currentFsScript();
  openFilePicker({
    browseUrl: script.browseUrl,
    drivesUrl: script.drivesUrl,
    mode: 'folder',
    title: script.pickerTitle,
    onConfirm: ([folderPath]) => {
      document.getElementById('fsFolderInput').value = folderPath;
    },
  });
}

function renderFsResult(headline, isError, detailLines) {
  const line = document.getElementById('fsResultLine');
  line.textContent = headline;
  line.className = 'admin-card-hint ' + (isError ? 'admin-backup-error' : 'admin-key-ok');
  line.hidden = false;

  const detail = document.getElementById('fsResultDetail');
  const list = document.getElementById('fsResultDetailList');
  list.innerHTML = '';
  if (detailLines && detailLines.length) {
    for (const d of detailLines) {
      const li = document.createElement('li');
      li.textContent = d;
      list.appendChild(li);
    }
    detail.hidden = false;
  } else {
    detail.hidden = true;
  }
}

async function runFilenameSort() {
  const script = currentFsScript();
  const folder = document.getElementById('fsFolderInput').value;
  if (!folder) {
    showToast('Choose a folder first', true);
    return;
  }
  const res = await postJSON(script.runPath, script.runBody(folder));
  if (res.started === false || res.detail) {
    showToast(res.detail || res.message || 'Could not start run', true);
    return;
  }
  document.getElementById('fsRunBtn').disabled = true;
  document.getElementById('fsScriptSelect').disabled = true;
  document.getElementById('fsProgressWrap').hidden = false;
  document.getElementById('fsResultLine').hidden = true;
  document.getElementById('fsResultDetail').hidden = true;
  pollFsStatus(script);
}

async function pollFsStatus(script) {
  const status = await apiFetch(`/admin${script.statusPath()}`);

  if (status.running) {
    fsPollTimer = setTimeout(() => pollFsStatus(script), 500);
    return;
  }

  clearTimeout(fsPollTimer);
  document.getElementById('fsRunBtn').disabled = false;
  document.getElementById('fsScriptSelect').disabled = false;
  document.getElementById('fsProgressWrap').hidden = true;

  if (status.error) {
    renderFsResult(`❌ Failed: ${status.error}`, true, []);
    return;
  }
  if (!status.result) return; // idle poll, nothing ran

  if ('files' in status.result) {
    // Sort by Filename result shape
    const { moved, total, folders, files } = status.result;
    const failed = files.filter(f => !f.success);

    if (!total) {
      renderFsResult('No CBZ/CBR files found in this folder.', false, []);
    } else if (!failed.length) {
      renderFsResult(`✅ Sorted ${moved} file${moved === 1 ? '' : 's'} into ${folders} folder${folders === 1 ? '' : 's'}`, false, []);
    } else {
      renderFsResult(
        `⚠️ Sorted ${moved} of ${total} file${total === 1 ? '' : 's'} into ${folders} folder${folders === 1 ? '' : 's'} — ${failed.length} failed`,
        true,
        failed.map(f => `${f.filename}: ${f.error}`)
      );
    }
    return;
  }

  // Move Series/Singles Folders result shape
  const { moved, total, folders, near_misses } = status.result;
  const failed = folders.filter(f => !f.success);
  const detailLines = [];
  for (const f of failed) {
    detailLines.push(`${f.folder_name}: ${f.error}`);
  }
  for (const nm of (near_misses || [])) {
    detailLines.push(`⚠ '${nm.folder_name}' looks similar to an existing folder: '${nm.existing_match}' — check before relying on this move`);
  }

  if (!total) {
    renderFsResult('No folders found to move.', false, detailLines);
  } else if (!failed.length) {
    renderFsResult(`✅ Moved ${moved} of ${total} folder${total === 1 ? '' : 's'}`, false, detailLines);
  } else {
    renderFsResult(
      `⚠️ Moved ${moved} of ${total} folder${total === 1 ? '' : 's'} — ${failed.length} failed`,
      true,
      detailLines
    );
  }
}

function initFilenameSortTool() {
  document.getElementById('fsBrowseBtn').addEventListener('click', openFsBrowse);
  document.getElementById('fsRunBtn').addEventListener('click', runFilenameSort);
  document.getElementById('fsScriptSelect').addEventListener('change', () => {
    document.getElementById('fsFolderInput').value = '';
    document.getElementById('fsResultLine').hidden = true;
    document.getElementById('fsResultDetail').hidden = true;
  });
}

// ── XML Tagging (§11.6) ──────────────────────────────────────────────────
// Standalone CT Auto-Tag run against any folder. Match Ratio Threshold,
// Save on Low Confidence, and the ComicVine API Key fields living in this
// tool's pane are the same pfCtMatchThreshold/pfCtSaveLowConfidence/
// pfComicVineKey elements Processing Folder Automation always used —
// loadProcessingFolderConfig()/initProcessingFolderTool() above already
// bind to them via getElementById regardless of where in the DOM they
// physically sit, so no changes were needed there for the relocation.

let xtPollTimer = null;

function openXtBrowse() {
  openFilePicker({
    browseUrl: `/admin/xml-tagging/browse`,
    drivesUrl: `/admin/xml-tagging/drives`,
    mode: 'folder',
    title: 'Choose Folder to Tag',
    onConfirm: ([folderPath]) => {
      document.getElementById('xtFolderInput').value = folderPath;
    },
  });
}

function renderXtResult(headline, isError, detailLines) {
  const line = document.getElementById('xtResultLine');
  line.textContent = headline;
  line.className = 'admin-card-hint ' + (isError ? 'admin-backup-error' : 'admin-key-ok');
  line.hidden = false;

  const detail = document.getElementById('xtResultDetail');
  const list = document.getElementById('xtResultDetailList');
  list.innerHTML = '';
  if (detailLines && detailLines.length) {
    for (const d of detailLines) {
      const li = document.createElement('li');
      li.textContent = d;
      list.appendChild(li);
    }
    detail.hidden = false;
  } else {
    detail.hidden = true;
  }
}

async function runXmlTagging() {
  const folder = document.getElementById('xtFolderInput').value;
  if (!folder) {
    showToast('Choose a folder first', true);
    return;
  }
  const res = await postJSON('/xml-tagging/run', { folder });
  if (res.started === false || res.detail) {
    showToast(res.detail || res.message || 'Could not start run', true);
    return;
  }
  document.getElementById('xtRunBtn').disabled = true;
  document.getElementById('xtProgressWrap').hidden = false;
  document.getElementById('xtResultLine').hidden = true;
  document.getElementById('xtResultDetail').hidden = true;
  pollXtStatus();
}

async function pollXtStatus() {
  const status = await apiFetch(`/admin/xml-tagging/status`);

  if (status.running) {
    xtPollTimer = setTimeout(pollXtStatus, 700);
    return;
  }

  clearTimeout(xtPollTimer);
  document.getElementById('xtRunBtn').disabled = false;
  document.getElementById('xtProgressWrap').hidden = true;

  if (status.error) {
    renderXtResult(`❌ Failed: ${status.error}`, true, []);
    return;
  }
  if (!status.result) return; // idle poll, nothing ran

  const { total, files } = status.result;
  const tagged = files.filter(f => f.tags_written).length;
  const noMatch = files.filter(f => f.confidence === 'no_match').length;
  const skippedLow = files.filter(f => f.confidence === 'low_confidence' && !f.tags_written).length;
  const failed = files.filter(f => f.status === 'failed');

  if (!total) {
    renderXtResult('No CBZ/CBR files found in this folder.', false, []);
  } else {
    renderXtResult(
      `${failed.length ? '⚠️' : '✅'} ${tagged} tagged, ${noMatch} no match, ${skippedLow} low confidence skipped, ${failed.length} failed (of ${total})`,
      !!failed.length,
      failed.map(f => `${f.filename}: ${f.error}`)
    );
  }
}

function initXmlTaggingTool() {
  document.getElementById('xtBrowseBtn').addEventListener('click', openXtBrowse);
  document.getElementById('xtRunBtn').addEventListener('click', runXmlTagging);
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
  initFilenameSortTool();
  initXmlTaggingTool();
}

document.addEventListener('DOMContentLoaded', initProcessingTools);
