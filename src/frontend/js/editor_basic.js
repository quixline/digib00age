// digib00age — editor_basic.js
// Basic Editor popup: single-issue metadata edit, opened from /issue/{id}.
// EDITOR_SPEC.md Section 6.

// AgeRating is locked, hardcoded — mirrors backend/editor/constants.py exactly.
// Genre and Format are both editable lists, always fetched from the server —
// see populateStaticSelects below.
const AGE_RATING_OPTIONS = [
  'Everyone', 'Early Childhood', 'Everyone 10+', 'PG', 'Adult', 'Teen', 'Teen+', 'Mature',
];

let editorReady = null;     // Promise — fragment fetched + static options populated
let genreOptionsCache = null;
let currentIssueId = null;
let currentOnSaved = null;

function ensureEditorLoaded() {
  if (editorReady) return editorReady;

  editorReady = fetch('/static/editor_basic.html')
    .then((res) => res.text())
    .then((html) => {
      const container = document.createElement('div');
      container.innerHTML = html;
      document.body.appendChild(container.firstElementChild);
      wireEditorChrome();
      return populateStaticSelects();
    });

  return editorReady;
}

function wireEditorChrome() {
  const overlay = document.getElementById('editorOverlay');
  const form = document.getElementById('editorForm');

  document.getElementById('editorCloseBtn').onclick = closeEditorModal;
  document.getElementById('editorCancelBtn').onclick = closeEditorModal;
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeEditorModal(); });

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

  document.getElementById('ed-format').addEventListener('change', updateSaveButtonState);
  document.getElementById('ed-agerating').addEventListener('change', updateSaveButtonState);

  form.addEventListener('submit', onEditorSubmit);
}

async function populateStaticSelects() {
  const formatSelect = document.getElementById('ed-format');
  const ratingSelect = document.getElementById('ed-agerating');

  const [formatOptions, genreOptions] = await Promise.all([
    apiFetch('/editor/formats'),
    apiFetch('/editor/genres'),
  ]);

  formatSelect.innerHTML = optionsHtml(formatOptions, '-- Select Format --');
  ratingSelect.innerHTML = optionsHtml(AGE_RATING_OPTIONS, '-- Select Rating --');

  genreOptionsCache = genreOptions;
  const grid = document.getElementById('ed-genre-grid');
  grid.innerHTML = '';
  for (const name of genreOptionsCache) {
    const label = document.createElement('label');
    label.className = 'editor-genre-item';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.name = 'Genre';
    checkbox.value = name;
    checkbox.addEventListener('change', updateSaveButtonState);
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(' ' + name));
    grid.appendChild(label);
  }
}

function optionsHtml(values, placeholder) {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  let html = `<option value="">${esc(placeholder)}</option>`;
  for (const v of values) html += `<option value="${esc(v)}">${esc(v)}</option>`;
  return html;
}

function updateSaveButtonState() {
  const anyGenreChecked = document.querySelectorAll('#ed-genre-grid input:checked').length > 0;
  const formatSet = document.getElementById('ed-format').value !== '';
  const ratingSet = document.getElementById('ed-agerating').value !== '';
  const ready = anyGenreChecked && formatSet && ratingSet;
  document.getElementById('editorSaveBtn').disabled = !ready;
  // Tooltip lives on the wrapping span, not the button itself — a native
  // `disabled` button suppresses hover/mouseover events in Chromium, so a
  // data-tooltip on the button alone would never fire while it's disabled.
  const saveWrap = document.getElementById('editorSaveWrap');
  if (saveWrap) {
    if (ready) delete saveWrap.dataset.tooltip;
    else saveWrap.dataset.tooltip = 'Save is enabled once a genre, format and age rating are set';
  }
}

function setField(id, value) {
  document.getElementById(id).value = value || '';
}

async function openEditorModal(issueId, onSaved) {
  // authLocked comes from auth.js (shared global scope, always loaded
  // alongside this file) — password protection on, not authenticated. Show
  // the login popup instead of opening a modal that can't do anything useful.
  if (authLocked) {
    showLoginPopup();
    return;
  }

  await ensureEditorLoaded();

  currentIssueId = issueId;
  currentOnSaved = onSaved;

  const errorBox = document.getElementById('editorError');
  errorBox.hidden = true;
  errorBox.textContent = '';

  let fields, saving;
  try {
    ({ fields, saving } = await apiFetch(`/editor/${issueId}`));
  } catch (_) {
    errorBox.hidden = false;
    errorBox.textContent = 'Could not load this issue for editing.';
    document.getElementById('editorOverlay').hidden = false;
    return;
  }

  const form = document.getElementById('editorForm');
  // Cancel stays enabled either way — this only ever gates the fields and
  // Save, never the user's ability to dismiss the modal.
  const controls = form.querySelectorAll('input, select, textarea, #editorSaveBtn');
  if (saving) {
    errorBox.hidden = false;
    errorBox.classList.add('editor-error--notice');
    errorBox.textContent =
      'A previous save for this issue is still finishing in the background — close and reopen in a moment.';
    for (const el of controls) el.disabled = true;
    document.getElementById('editorOverlay').hidden = false;
    return;
  }
  errorBox.classList.remove('editor-error--notice');
  for (const el of controls) el.disabled = false;

  setField('ed-series', fields.Series);
  setField('ed-title', fields.Title);
  setField('ed-number', fields.Number);
  setField('ed-year', fields.Year);
  setField('ed-summary', fields.Summary);
  setField('ed-count', fields.Count);
  setField('ed-pagecount', fields.PageCount);
  setField('ed-writer', fields.Writer);
  setField('ed-penciller', fields.Penciller);
  setField('ed-publisher', fields.Publisher);
  setField('ed-storyarc', fields.StoryArc);
  setField('ed-language', fields.Language);
  // Notes defaults to the established convention when blank, rather than
  // saving an empty tag (EDITOR_SPEC.md Section 3.3).
  setField('ed-notes', fields.Notes || 'Modified with the CAPT');

  document.getElementById('ed-bw').checked = fields.BlackAndWhite === 'on';

  // Section 4.4 — assigning a value with no matching <option> (a stale/removed
  // Format) leaves the select unselected, i.e. blank, same as the genre/rating gate below.
  const formatSelect = document.getElementById('ed-format');
  formatSelect.value = fields.Format || '';

  const ratingSelect = document.getElementById('ed-agerating');
  ratingSelect.value = AGE_RATING_OPTIONS.includes(fields.AgeRating) ? fields.AgeRating : '';

  // Section 4.4 — only pre-check genres that are still in the enforced list;
  // a stale/invalid value (e.g. "Zombie") simply has no checkbox to match.
  const existingGenres = (fields.Genre || '').split(',').map((g) => g.trim()).filter(Boolean);
  for (const checkbox of document.querySelectorAll('#ed-genre-grid input')) {
    checkbox.checked = existingGenres.includes(checkbox.value);
  }

  updateSaveButtonState();

  // Reset to the Main tab every time the popup opens.
  document.querySelector('.editor-tab-btn[data-tab="main"]').click();

  document.getElementById('editorOverlay').hidden = false;
}

function closeEditorModal() {
  const overlay = document.getElementById('editorOverlay');
  if (overlay) overlay.hidden = true;
  currentIssueId = null;
  currentOnSaved = null;
}

// Non-blocking save-time check against existing deduped people (Tier 4 Item
// 3) — splits a Writer/Penciller CSV value, checks each name against
// /api/people/fuzzy-match, and lets the user swap in the close existing
// match or keep what they typed. Never prevents the save either way.
async function warnOnFuzzyCredits(fields) {
  for (const [role, label] of [['Writer', 'writer'], ['Penciller', 'artist']]) {
    const raw = fields[role];
    if (!raw) continue;
    const names = raw.split(',').map(s => s.trim()).filter(Boolean);
    const resolved = [];
    for (const name of names) {
      try {
        const data = await apiFetch(`/people/fuzzy-match?name=${encodeURIComponent(name)}`);
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

async function onEditorSubmit(e) {
  e.preventDefault();

  const form = document.getElementById('editorForm');
  const formData = new FormData(form);
  const genreNames = formData.getAll('Genre');

  let fields = {
    Series: formData.get('Series') || '',
    Title: formData.get('Title') || '',
    Number: formData.get('Number') || '',
    Year: formData.get('Year') || '',
    Genre: genreNames.join(', '),
    Format: formData.get('Format') || '',
    BlackAndWhite: formData.get('BlackAndWhite') || '',
    AgeRating: formData.get('AgeRating') || '',
    Summary: formData.get('Summary') || '',
    Count: formData.get('Count') || '',
    Writer: formData.get('Writer') || '',
    Penciller: formData.get('Penciller') || '',
    Publisher: formData.get('Publisher') || '',
    PageCount: formData.get('PageCount') || '',
    StoryArc: formData.get('StoryArc') || '',
    Language: formData.get('Language') || '',
    Notes: formData.get('Notes') || '',
  };

  fields = await warnOnFuzzyCredits(fields);

  const saveBtn = document.getElementById('editorSaveBtn');
  const errorBox = document.getElementById('editorError');
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving…';
  errorBox.hidden = true;

  try {
    const body = await apiFetch(`/editor/${currentIssueId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields }),
    });

    const onSaved = currentOnSaved;
    const issueId = currentIssueId;
    closeEditorModal();
    if (body.pending) {
      showEditorToast('Saving in background…');
      pollEditorSaveStatus(issueId, onSaved);
    } else if (onSaved) {
      onSaved();
    }
  } catch (err) {
    errorBox.hidden = false;
    if (err.status === 409) {
      errorBox.textContent = err.body?.detail || 'A save is already in progress for this issue.';
    } else if (err.status) {
      const messages = err.body?.detail?.errors || [err.body?.detail || 'Save failed.'];
      errorBox.textContent = messages.join(' ');
    } else {
      errorBox.textContent = 'Network error — save did not complete.';
    }
  } finally {
    saveBtn.textContent = 'Save';
    updateSaveButtonState();
  }
}

// Self-rescheduling poll (not setInterval — same pattern as
// processingTools.js's pollXtStatus()) for the background archive
// rewrite + rescan queued by onEditorSubmit. If the user navigates away
// before this finishes, the timer is just torn down by the browser — no
// cleanup needed, that silent-on-navigate-away behaviour is deliberate
// (DECISIONS.md).
async function pollEditorSaveStatus(issueId, onSaved) {
  let status;
  try {
    status = await apiFetch(`/editor/${issueId}/save-status`, { retry: false });
  } catch (_) {
    setTimeout(() => pollEditorSaveStatus(issueId, onSaved), 700);
    return;
  }
  if (status.running) {
    setTimeout(() => pollEditorSaveStatus(issueId, onSaved), 700);
    return;
  }
  if (status.error) {
    showEditorToast('Save failed: ' + status.error, true);
    return;
  }
  showEditorToast('Saved');
  if (onSaved) onSaved();
}

// Reuses the existing .admin-toast/.admin-toast--show/.admin-toast--error
// CSS (style.css is loaded globally, not just on the Admin page) with its
// own element id — issue.html doesn't load admin.js, so admin.js's own
// showToast() isn't available here.
function showEditorToast(msg, isError = false) {
  let toast = document.getElementById('editorToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'editorToast';
    toast.className = 'admin-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.toggle('admin-toast--error', isError);
  toast.classList.add('admin-toast--show');
  setTimeout(() => toast.classList.remove('admin-toast--show'), 3500);
}
