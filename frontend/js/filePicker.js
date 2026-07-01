// ── Shared Processing Tools file/folder picker ──────────────────────────────
// admin-spec-section-12-processing-tools.md §12 shared notes: one in-app
// folder-tree picker, no library_root restriction, Home/Up with a
// drive-letter ("This PC") listing as the Up-navigation terminus, no
// recursion. Reused by File Rename, Convert Archives, Convert Images, and
// Processing Folder Automation — one shared overlay (#ptPickerOverlay in
// admin.html), reconfigured per open() call rather than one instance per
// tool (same pattern admin.js's #ctPickerOverlay already uses for Custom
// Tabs + Home Strips).

let ptPickerConfig = null;     // { browseUrl, drivesUrl, mode: 'files'|'folder', title, onConfirm }
let ptPickerPath   = null;     // null while showing "This PC"
let ptPickerSelected = new Map(); // path -> 'file' | 'folder' (mode: 'files' only)

function wireFilePicker() {
  document.getElementById('ptPickerCloseBtn').addEventListener('click', closeFilePicker);
  document.getElementById('ptPickerHomeBtn').addEventListener('click', () => loadPtPickerDirectory(null));
  document.getElementById('ptPickerUpBtn').addEventListener('click', ptPickerNavigateUp);
  document.getElementById('ptPickerSelectAllBtn').addEventListener('click', ptPickerSelectAll);
  document.getElementById('ptPickerDeselectAllBtn').addEventListener('click', ptPickerDeselectAll);
  document.getElementById('ptPickerConfirmBtn').addEventListener('click', ptPickerConfirm);
}

// config: { browseUrl, drivesUrl, mode: 'files'|'folder', title, onConfirm(paths) }
function openFilePicker(config) {
  ptPickerConfig = config;
  ptPickerSelected.clear();
  document.getElementById('ptPickerTitle').textContent = config.title || 'Choose Files';
  document.getElementById('ptPickerConfirmBtn').textContent =
    config.mode === 'folder' ? 'Select This Folder' : 'Add Selected';
  const multiSelectBtns = ['ptPickerSelectAllBtn', 'ptPickerDeselectAllBtn'];
  multiSelectBtns.forEach(id => {
    document.getElementById(id).style.display = config.mode === 'folder' ? 'none' : '';
  });
  document.getElementById('ptPickerOverlay').hidden = false;
  loadPtPickerDirectory(null);
}

function closeFilePicker() {
  document.getElementById('ptPickerOverlay').hidden = true;
}

async function loadPtPickerDirectory(path) {
  // browseUrl may already carry its own query string (e.g. Convert
  // Archives' `?from_format=cbr`) — join with `&` in that case rather than
  // a second `?`, which would silently mangle both params into one.
  let url = ptPickerConfig.browseUrl;
  if (path) {
    const sep = url.includes('?') ? '&' : '?';
    url += `${sep}path=${encodeURIComponent(path)}`;
  }
  const res = await fetch(url);
  if (!res.ok) return;
  const data = await res.json();
  ptPickerPath = data.path;
  renderPtPickerBreadcrumb(data.path);
  renderPtPickerTree(data.folders || [], data.files || []);
}

async function loadPtPickerDrives() {
  const res = await fetch(ptPickerConfig.drivesUrl);
  if (!res.ok) return;
  const data = await res.json();
  ptPickerPath = null;
  renderPtPickerBreadcrumb(null);
  renderPtPickerTree(data.drives || [], []);
}

function renderPtPickerBreadcrumb(path) {
  const breadcrumb = document.getElementById('ptPickerBreadcrumb');
  breadcrumb.innerHTML = '';

  const thisPc = document.createElement('a');
  thisPc.href = '#';
  thisPc.textContent = 'This PC';
  thisPc.onclick = (e) => { e.preventDefault(); loadPtPickerDrives(); };
  breadcrumb.appendChild(thisPc);

  const parts = (path || '').split('\\').filter(Boolean);
  let accumulated = '';
  parts.forEach((part, index) => {
    breadcrumb.appendChild(document.createTextNode(' \\ '));
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
      link.onclick = (e) => { e.preventDefault(); loadPtPickerDirectory(target); };
      breadcrumb.appendChild(link);
    }
  });
}

function renderPtPickerTree(folders, files) {
  const tree = document.getElementById('ptPickerTree');
  tree.innerHTML = '';
  ptPickerSelected.clear();
  updatePtPickerSelectedCount();

  const folderMode = ptPickerConfig.mode === 'folder';
  const items = [
    ...folders.map(f => ({ ...f, type: 'folder' })),
    ...(folderMode ? [] : files.map(f => ({ ...f, type: 'file' }))),
  ];

  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'fe-picker-empty';
    empty.textContent = 'No items found.';
    tree.appendChild(empty);
    return;
  }

  for (const item of items) {
    const row = document.createElement('div');
    row.className = `fe-picker-item ${item.type}`;

    if (item.type === 'folder' && folderMode) {
      // Single-folder-select mode (Processing Folder Automation) — clicking
      // a folder navigates into it; the currently-browsed folder itself is
      // what "Select This Folder" commits, no per-row checkbox needed.
      const name = document.createElement('span');
      name.className = 'fe-picker-item-name';
      name.textContent = item.name;
      row.appendChild(name);
      row.addEventListener('click', () => loadPtPickerDirectory(item.path));
      tree.appendChild(row);
      continue;
    }

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.addEventListener('change', () => {
      row.classList.toggle('selected', checkbox.checked);
      if (checkbox.checked) ptPickerSelected.set(item.path, item.type);
      else ptPickerSelected.delete(item.path);
      updatePtPickerSelectedCount();
    });

    const name = document.createElement('span');
    name.className = 'fe-picker-item-name';
    name.textContent = item.name;

    row.appendChild(checkbox);
    row.appendChild(name);

    if (item.type === 'folder') {
      row.addEventListener('click', (e) => { if (e.target !== checkbox) loadPtPickerDirectory(item.path); });
    } else {
      row.addEventListener('click', (e) => {
        if (e.target === checkbox) return;
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event('change'));
      });
    }

    tree.appendChild(row);
  }
}

function updatePtPickerSelectedCount() {
  const count = ptPickerSelected.size;
  const el = document.getElementById('ptPickerSelectedCount');
  if (el) el.textContent = `${count} item${count === 1 ? '' : 's'} selected`;
}

function ptPickerSelectAll() {
  document.querySelectorAll('#ptPickerTree input[type="checkbox"]').forEach((cb) => {
    if (!cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change')); }
  });
}

function ptPickerDeselectAll() {
  document.querySelectorAll('#ptPickerTree input[type="checkbox"]').forEach((cb) => {
    if (cb.checked) { cb.checked = false; cb.dispatchEvent(new Event('change')); }
  });
}

function ptPickerNavigateUp() {
  if (!ptPickerPath) return; // already at "This PC" — nothing above it
  const parts = ptPickerPath.split('\\').filter(Boolean);
  if (parts.length > 1) {
    parts.pop();
    loadPtPickerDirectory(parts.join('\\'));
  } else {
    loadPtPickerDrives();
  }
}

function ptPickerConfirm() {
  if (ptPickerConfig.mode === 'folder') {
    if (!ptPickerPath) return; // "This PC" itself isn't a selectable folder
    ptPickerConfig.onConfirm([ptPickerPath]);
  } else {
    const paths = Array.from(ptPickerSelected.entries())
      .filter(([, type]) => type === 'file')
      .map(([path]) => path);
    if (!paths.length) return;
    ptPickerConfig.onConfirm(paths);
  }
  closeFilePicker();
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('ptPickerOverlay')) wireFilePicker();
});
