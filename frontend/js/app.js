// ComicVault — app.js
// Library home (index.html), series detail (series.html), issue detail (issue.html)

const API = '/api';

// ── Utilities ────────────────────────────────────────────────────────────────

async function apiFetch(path, signal) {
  let res;
  try {
    res = await fetch(API + path, signal ? { signal } : undefined);
  } catch (networkErr) {
    if (networkErr.name === 'AbortError') throw networkErr;
    throw new Error(`Network error (server unreachable): ${path}`);
  }
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${path}`);
  return res.json();
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// ══════════════════════════════════════════════════════════════════════════════
//  MULTI-SELECT — long-press to select, short tap to add more
//  Only attached to elements that map 1:1 to a single issue (Singles cards,
//  series-detail issue rows, 2000 AD prog cards) — never series-aggregate
//  cards, where a bulk action's meaning would be ambiguous.
// ══════════════════════════════════════════════════════════════════════════════

const LONG_PRESS_MS         = 500;
const PRESS_MOVE_TOLERANCE  = 10;  // px — a drag/scroll cancels the long-press

let selectionActive = false;
const selectedIds   = new Map();   // issue id -> true

function makeSelectable(element, issueId) {
  element.dataset.issueId = issueId;

  let pressTimer     = null;
  let longPressFired = false;
  let startX = 0, startY = 0;

  const clearPress = () => { clearTimeout(pressTimer); pressTimer = null; };

  element.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;  // ignore right/middle click
    longPressFired = false;
    startX = e.clientX; startY = e.clientY;
    clearPress();
    pressTimer = setTimeout(() => {
      longPressFired = true;
      if (!selectionActive) enterSelectionMode(issueId);
      else toggleSelected(issueId);
    }, LONG_PRESS_MS);
  });

  element.addEventListener('pointermove', (e) => {
    if (!pressTimer) return;
    if (Math.abs(e.clientX - startX) > PRESS_MOVE_TOLERANCE ||
        Math.abs(e.clientY - startY) > PRESS_MOVE_TOLERANCE) {
      clearPress();
    }
  });

  element.addEventListener('pointerup', (e) => {
    const firedLongPress = longPressFired;
    clearPress();
    if (selectionActive) {
      e.preventDefault();
      if (!firedLongPress) toggleSelected(issueId);  // short tap while already selecting
    }
    // else: plain short tap, no long-press — let the <a href> navigate normally
  });

  element.addEventListener('pointercancel', clearPress);
}

// Suppress navigation for any click landing on a selectable element while
// selection mode is active. A delegated capture-phase listener is more
// reliable than preventDefault() in the pointerup handler alone, since some
// browsers still dispatch a synthetic click afterward.
document.addEventListener('click', (e) => {
  if (selectionActive && e.target.closest('[data-issue-id]')) {
    e.preventDefault();
    e.stopPropagation();
  }
}, true);

function enterSelectionMode(firstId) {
  selectionActive = true;
  showSelectionToolbar();
  toggleSelected(firstId);
}

function exitSelectionMode() {
  if (!selectionActive && selectedIds.size === 0) return;
  selectionActive = false;
  for (const id of selectedIds.keys()) {
    const node = document.querySelector(`[data-issue-id="${id}"]`);
    if (node) node.classList.remove('selected');
  }
  selectedIds.clear();
  hideSelectionToolbar();
}

function toggleSelected(id) {
  if (selectedIds.has(id)) selectedIds.delete(id);
  else selectedIds.set(id, true);

  const node = document.querySelector(`[data-issue-id="${id}"]`);
  if (node) node.classList.toggle('selected', selectedIds.has(id));

  if (selectedIds.size === 0) exitSelectionMode();
  else updateSelectionToolbar();
}

function ensureSelectionToolbar() {
  let bar = document.getElementById('selectionToolbar');
  if (bar) return bar;

  bar = el('div', 'selection-toolbar');
  bar.id = 'selectionToolbar';
  bar.hidden = true;

  const count = el('span', 'selection-count');
  count.id = 'selectionCount';
  bar.appendChild(count);

  const actions = el('div', 'selection-actions');
  const mkBtn = (id, label, handler) => {
    const b = el('button', 'selection-action-btn', label);
    b.id   = id;
    b.type = 'button';
    b.addEventListener('click', handler);
    actions.appendChild(b);
    return b;
  };
  mkBtn('selMarkRead',   'Mark Read',
    () => runBulkAction('/progress/bulk/mark-read',   {}, ids => applyReadStateToDom(ids, 'read')));
  mkBtn('selMarkUnread', 'Mark Unread',
    () => runBulkAction('/progress/bulk/mark-unread', {}, ids => applyReadStateToDom(ids, 'unread')));
  mkBtn('selFavorite',   '★ Favorite',
    () => runBulkAction('/progress/bulk/favorite',    {}, ids => applyFavoriteToDom(ids, true)));

  const rateWrap = el('div', 'selection-rate');
  for (let i = 1; i <= 5; i++) {
    const star = el('button', 'rating-star', '★');
    star.type  = 'button';
    star.title = `Rate ${i}`;
    star.addEventListener('click', () => runBulkAction('/progress/bulk/rate', { rating: i }));
    rateWrap.appendChild(star);
  }
  actions.appendChild(rateWrap);
  bar.appendChild(actions);

  const endWrap    = el('div', 'selection-toolbar-end');
  const cancelBtn  = el('button', 'selection-cancel-btn', 'Cancel');
  cancelBtn.id     = 'selCancel';
  cancelBtn.type   = 'button';
  cancelBtn.addEventListener('click', () => exitSelectionMode());
  const doneBtn    = el('button', 'selection-done-btn', 'Done');
  doneBtn.id       = 'selDone';
  doneBtn.type     = 'button';
  doneBtn.addEventListener('click', () => exitSelectionMode());
  endWrap.append(cancelBtn, doneBtn);
  bar.appendChild(endWrap);

  document.body.appendChild(bar);
  return bar;
}

function showSelectionToolbar() {
  ensureSelectionToolbar().hidden = false;
  updateSelectionToolbar();
}

function hideSelectionToolbar() {
  const bar = document.getElementById('selectionToolbar');
  if (bar) bar.hidden = true;
}

function updateSelectionToolbar() {
  const countEl = document.getElementById('selectionCount');
  if (countEl) countEl.textContent = `${selectedIds.size} selected`;
}

async function runBulkAction(path, extraBody, applyFn) {
  const ids = Array.from(selectedIds.keys());
  if (!ids.length) return;
  try {
    await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ issue_ids: ids, ...extraBody }),
    });
    if (applyFn) applyFn(ids);
  } catch (_) {
    // Best-effort — selection still clears; a reload reflects true server state.
  }
  exitSelectionMode();
}

// Targeted DOM + cache updates so the grid doesn't need a full refetch after
// a bulk action — mirrors the existing single-issue buildStatusButton pattern.
function applyReadStateToDom(ids, status) {
  for (const id of ids) {
    const node = document.querySelector(`[data-issue-id="${id}"]`);
    if (node) {
      node.classList.remove('state-read', 'state-reading', 'state-unread', 'state-part-read');
      node.classList.add(status === 'read' ? 'state-read' : 'state-unread');
    }
    // Singles cards in the browse grid: series_anchor_id IS the issue id —
    // patch the cached aggregate counts so the status-pill filter stays correct.
    const lib = allLibrary.find(s => s.series_anchor_id === id);
    if (lib) {
      if (status === 'read') { lib.read_count = lib.issue_count; lib.unread_count = 0; lib.reading_count = 0; }
      else                   { lib.read_count = 0; lib.unread_count = lib.issue_count; lib.reading_count = 0; }
    }
  }
}

function applyFavoriteToDom(ids, value) {
  for (const id of ids) {
    const node = document.querySelector(`[data-issue-id="${id}"]`);
    if (node) node.classList.toggle('is-favorite', value);
    const lib = allLibrary.find(s => s.series_anchor_id === id);
    if (lib) lib.favorites = value;
  }
}

// ── Page dispatch ─────────────────────────────────────────────────────────────
// Defer to DOMContentLoaded so the full DOM is guaranteed to be available
// before any getElementById / querySelectorAll calls fire.

document.addEventListener('DOMContentLoaded', () => {
  switch (document.body.dataset.page) {
    case 'library': initLibrary(); break;
    case 'series':  initSeries();  break;
    case 'issue':   initIssue();   break;
  }
});

// ══════════════════════════════════════════════════════════════════════════════
//  LIBRARY PAGE
// ══════════════════════════════════════════════════════════════════════════════

// ── State ─────────────────────────────────────────────────────────────────────

let allLibrary  = [];           // raw /api/library response (cached)
let filtersReady = false;       // filter dropdowns populated
let tabLibraryCache = {};       // custom tab id (string) -> /api/library?tab_id=… response

// Active filter state
let activeSurface   = 'home';   // home | series | singles | all | 2000ad
let activeStatus    = '';       // '' | unread | reading | read
let activeGenre     = '';
let activePublisher = '';
let activeFormat    = '';
let activeDecade    = '';
let activeYear      = '';
let activeRating    = '';
let activeBW        = '';       // '' | yes | no
let activeSort      = 'alpha';  // alpha | newest | recent
let activeGroupBy   = '';       // '' | year | genre | publisher | writer
let activeSearch    = '';

// 'fieldview'/'folderview' surfaces — transient, opened from a home strip's
// clickable heading (HOME_STRIPS_SPEC.md 5.2), not part of the persistent nav.
let viewField       = '';
let viewFieldValue  = '';
let viewFolderPath  = '';
let viewLibraryCache = {};      // cache key (see loadBrowse) -> /api/library response

let viewMode = localStorage.getItem('cv_view_mode') || 'grid';

let currentPage = 1;
let pageSize    = parseInt(localStorage.getItem('cv_page_size') || '50', 10);

// ── Init ──────────────────────────────────────────────────────────────────────

async function initLibrary() {
  try {
    bindSurfaceNav();
    bindFilterEvents();
    bindSearchEvents();
    await loadCustomTabsNav();
    // Honour ?surface= so the back button from detail pages returns to the right tab
    const params     = new URLSearchParams(location.search);
    const reqSurface = params.get('surface') || 'home';
    const VALID      = ['home', 'series', 'singles', 'all', '2000ad', 'fieldview', 'folderview'];
    const known      = VALID.includes(reqSurface) || reqSurface.startsWith('tab-');
    viewField      = params.get('field') || '';
    viewFieldValue = params.get('value') || '';
    viewFolderPath = params.get('folder') || '';
    await switchSurface(known ? reqSurface : 'home');
  } catch (err) {
    console.error('initLibrary failed:', err);
    const homeStrips = document.getElementById('homeStrips');
    if (homeStrips) {
      homeStrips.innerHTML =
        '<div class="empty-state"><div class="empty-icon">⚠️</div>' +
        `<p>Failed to initialise.<br><small>${err.message}</small></p>` +
        '<p><button onclick="loadHome()">Retry</button></p></div>';
    }
  }
}

// ── Surface navigation ────────────────────────────────────────────────────────

function bindSurfaceNav() {
  // Delegated (rather than bound per-button) so custom-tab buttons injected
  // later by loadCustomTabsNav() work without a second bind pass.
  document.querySelector('.surface-nav').addEventListener('click', (e) => {
    const btn = e.target.closest('.surface-btn');
    if (btn) switchSurface(btn.dataset.surface);
  });
}

function isBrowseSurface(surface) {
  return ['series', 'singles', 'all', 'fieldview', 'folderview'].includes(surface)
    || surface.startsWith('tab-');
}

function isFlatSurface(surface) {
  return surface === 'all' || surface.startsWith('tab-') || surface === 'fieldview' || surface === 'folderview';
}

// Custom Tabs (CUSTOM_TABS_SPEC.md) — admin-managed, folder-scoped tabs,
// appended after the fixed nav so they render last (Home, All, Singles,
// Series, 2000 AD, then visible custom tabs in created_at order).
async function loadCustomTabsNav() {
  try {
    const nav = await apiFetch('/nav/config');
    const container = document.querySelector('.surface-nav');
    const names = {};
    for (const tab of nav.custom_tabs || []) {
      const btn = el('button', 'surface-btn', tab.name);
      btn.dataset.surface = `tab-${tab.id}`;
      btn.setAttribute('role', 'tab');
      btn.setAttribute('aria-selected', 'false');
      container.appendChild(btn);
      names[`tab-${tab.id}`] = tab.name;
    }
    // Cached so series.html/issue.html (separate page loads) can label a
    // "from=tab-N" back link with the tab's actual name instead of "Library".
    sessionStorage.setItem('cv_custom_tab_names', JSON.stringify(names));
  } catch (_) {
    // Fixed-tab nav still works if this fails; not fatal.
  }
}

function customTabLabel(from) {
  try {
    const names = JSON.parse(sessionStorage.getItem('cv_custom_tab_names') || '{}');
    return names[from] || null;
  } catch (_) {
    return null;
  }
}

async function switchSurface(surface) {
  exitSelectionMode();
  activeSurface = surface;
  const isBrowse = isBrowseSurface(surface);

  // Update tab state
  document.querySelectorAll('.surface-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.surface === surface);
    b.setAttribute('aria-selected', String(b.dataset.surface === surface));
  });

  // Show/hide major views
  document.getElementById('homeView').hidden   = surface !== 'home';
  document.getElementById('browseView').hidden = !isBrowse;
  document.getElementById('adView').hidden     = surface !== '2000ad';
  document.getElementById('searchWrap').hidden = !isBrowse;

  if (surface === 'home') {
    await loadHome();
  } else if (isBrowse) {
    // Clear search when switching surface
    const input = document.getElementById('searchInput');
    if (input) { input.value = ''; activeSearch = ''; }
    document.getElementById('searchClear').style.display = 'none';
    await loadBrowse();
  } else if (surface === '2000ad') {
    await load2000AD();
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  HOME SURFACE
// ══════════════════════════════════════════════════════════════════════════════

async function loadHome() {
  const homeStrips = document.getElementById('homeStrips');

  homeStrips.innerHTML = '<div class="loading-state">Loading…</div>';

  // 20-second timeout so the page never silently hangs.
  const ctrl    = new AbortController();
  const timerId = setTimeout(() => ctrl.abort(), 20000);

  try {
    const stripsData = await apiFetch('/home/strips', ctrl.signal);
    clearTimeout(timerId);

    homeStrips.innerHTML = '';
    for (const strip of stripsData.strips) {
      if (!strip.items || !strip.items.length) continue;
      homeStrips.appendChild(buildHomeStrip(strip));
    }
    if (!homeStrips.children.length) {
      homeStrips.innerHTML =
        '<div class="empty-state"><div class="empty-icon">📚</div><p>No content yet.</p></div>';
    }
  } catch (err) {
    clearTimeout(timerId);
    const msg   = err.name === 'AbortError' ? 'Server took too long to respond.' : err.message;
    homeStrips.innerHTML =
      '<div class="empty-state"><div class="empty-icon">⚠️</div>' +
      `<p>${msg}<br><button onclick="loadHome()">Retry</button></p></div>`;
  }
}

function stripViewAllHref(strip) {
  // Defaults (basis_type 'builtin') don't get a listing page in this round —
  // HOME_STRIPS_SPEC.md only requires this for admin-added field/folder strips.
  if (strip.basis_type === 'field') {
    return `/?surface=fieldview&field=${encodeURIComponent(strip.field_name)}&value=${encodeURIComponent(strip.field_value)}`;
  }
  if (strip.basis_type === 'folder') {
    return `/?surface=folderview&folder=${encodeURIComponent(strip.folder_path)}`;
  }
  return null;
}

function buildHomeStrip(strip) {
  const section = el('div', 'home-strip');
  const viewAllHref = stripViewAllHref(strip);
  if (viewAllHref) {
    const heading = el('a', 'section-label section-label--link', strip.title);
    heading.href = viewAllHref;
    section.appendChild(heading);
  } else {
    section.appendChild(el('p', 'section-label', strip.title));
  }

  const track    = el('div', 'strip-track');
  const btnLeft  = el('button', 'strip-arrow strip-arrow--left');
  const btnRight = el('button', 'strip-arrow strip-arrow--right');
  btnLeft.innerHTML  = '&#8249;';  // ‹
  btnRight.innerHTML = '&#8250;';  // ›
  btnLeft.setAttribute('aria-label', 'Scroll left');
  btnRight.setAttribute('aria-label', 'Scroll right');

  const scrollArea = el('div', 'continue-strip');
  for (const item of strip.items) scrollArea.appendChild(buildStripCard(item));

  const STEP = 340;
  btnLeft.addEventListener('click',  () => scrollArea.scrollBy({ left: -STEP, behavior: 'smooth' }));
  btnRight.addEventListener('click', () => scrollArea.scrollBy({ left:  STEP, behavior: 'smooth' }));

  const syncArrows = () => {
    const { scrollLeft, clientWidth, scrollWidth } = scrollArea;
    btnLeft.classList.toggle('at-edge',  scrollLeft <= 1);
    btnRight.classList.toggle('at-edge', scrollLeft + clientWidth >= scrollWidth - 1);
  };
  scrollArea.addEventListener('scroll', syncArrows, { passive: true });
  // Sync after layout so clientWidth / scrollWidth are known
  requestAnimationFrame(syncArrows);

  track.append(btnLeft, scrollArea, btnRight);
  section.appendChild(track);
  return section;
}

function buildStripCard(item) {
  const isSingle = item.format_group === 'Singles';
  const href = `/issue/${item.id}?from=home`;

  const state = item.read_status === 'read'    ? 'state-read'
              : item.read_status === 'reading'  ? 'state-part-read'
              : 'state-unread';

  const card = el('a', `cover-card strip-card ${state}`);
  card.href  = href;
  card.title = item.series;

  const wrap = el('div', 'cover-img-wrap');
  const img  = el('img');
  img.src     = item.cover_path;
  img.alt     = item.series;
  img.loading = 'lazy';
  img.onerror = () => { wrap.innerHTML = '<div class="cover-placeholder">📖</div>'; };
  wrap.appendChild(img);

  // Part-read progress bar
  if (state === 'state-part-read' && item.page_count > 0) {
    const pct = Math.min(100, Math.round((item.current_page / item.page_count) * 100));
    const bar = el('div', 'card-progress-bar');
    bar.style.width = `${pct}%`;
    wrap.appendChild(bar);
  }

  const info = el('div', 'cover-info');
  info.appendChild(el('div', 'cover-title', item.series));

  if (item.year) info.appendChild(el('div', 'cover-year', String(item.year)));
  if (isSingle) {
    if (item.page_count) info.appendChild(el('div', 'cover-count', `${item.page_count} pages`));
  } else {
    if (item.number) info.appendChild(el('div', 'cover-count', `#${item.number}`));
  }

  card.append(wrap, info);
  return card;
}

// ══════════════════════════════════════════════════════════════════════════════
//  BROWSE SURFACES (Series / Singles / All)
// ══════════════════════════════════════════════════════════════════════════════

async function loadBrowse() {
  const grid = document.getElementById('coverGrid');

  if (!allLibrary.length) {
    // Fetched regardless of surface — filter dropdown options (populated
    // below) are global across the whole library, same as the existing
    // Series/Singles/All surfaces.
    grid.innerHTML = '<div class="loading-state">Loading…</div>';
    try {
      allLibrary = await apiFetch('/library');
    } catch (err) {
      grid.innerHTML =
        '<div class="empty-state"><div class="empty-icon">⚠️</div>' +
        '<p>Could not reach the server. Is it running?</p></div>';
      return;
    }
  }

  if (!filtersReady) {
    await populateFilterDropdowns();
    filtersReady = true;
  }

  if (activeSurface.startsWith('tab-')) {
    const tabId = activeSurface.slice(4);
    if (!tabLibraryCache[tabId]) {
      grid.innerHTML = '<div class="loading-state">Loading…</div>';
      try {
        tabLibraryCache[tabId] = await apiFetch(`/library?tab_id=${tabId}`);
      } catch (err) {
        grid.innerHTML =
          '<div class="empty-state"><div class="empty-icon">⚠️</div>' +
          '<p>This tab is no longer available.</p></div>';
        return;
      }
    }
  } else if (activeSurface === 'fieldview' || activeSurface === 'folderview') {
    const cacheKey = activeSurface === 'fieldview' ? `field:${viewField}:${viewFieldValue}` : `folder:${viewFolderPath}`;
    if (!viewLibraryCache[cacheKey]) {
      grid.innerHTML = '<div class="loading-state">Loading…</div>';
      const qs = activeSurface === 'fieldview'
        ? `field=${encodeURIComponent(viewField)}&value=${encodeURIComponent(viewFieldValue)}`
        : `folder_path=${encodeURIComponent(viewFolderPath)}`;
      try {
        viewLibraryCache[cacheKey] = await apiFetch(`/library?${qs}`);
      } catch (err) {
        grid.innerHTML =
          '<div class="empty-state"><div class="empty-icon">⚠️</div>' +
          '<p>This view is no longer available.</p></div>';
        return;
      }
    }
  }

  renderBrowse();
}

// ── Filter dropdown population ────────────────────────────────────────────────

async function populateFilterDropdowns() {
  // Derive from allLibrary where possible
  const addOpts = (selId, values, labelFn) => {
    const sel = document.getElementById(selId);
    for (const v of values) {
      const o = document.createElement('option');
      o.value = v; o.textContent = labelFn ? labelFn(v) : v;
      sel.appendChild(o);
    }
  };

  const genres     = [...new Set(allLibrary.flatMap(s => s.genres  || []))].sort();
  const publishers = [...new Set(allLibrary.map(s => s.publisher).filter(Boolean))].sort();
  const years      = [...new Set(allLibrary.map(s => s.year).filter(Boolean))].sort((a,b) => b-a);
  const decades    = [...new Set(years.map(y => Math.floor(y/10)*10))].sort((a,b) => b-a);
  const formats    = [...new Set(allLibrary.flatMap(s => s.formats  || []))].sort();
  const ratings    = [...new Set(allLibrary.flatMap(s => s.age_ratings || []))].sort();

  addOpts('genreFilter',     genres,     null);
  addOpts('publisherFilter', publishers, null);
  addOpts('yearFilter',      years,      null);
  addOpts('decadeFilter',    decades,    d => `${d}s`);
  addOpts('formatFilter',    formats,    null);
  addOpts('ratingFilter',    ratings,    null);
}

// ── Filter + sort + render ────────────────────────────────────────────────────

function getFilteredLibrary() {
  let pool;

  if (activeSurface.startsWith('tab-')) {
    // Custom tab — already folder-scoped server-side; flat like 'all' (no
    // format_group split), per CUSTOM_TABS_SPEC.md 5.3.
    pool = tabLibraryCache[activeSurface.slice(4)] || [];
  } else if (activeSurface === 'fieldview' || activeSurface === 'folderview') {
    // Home strip "view all" — already field/folder-scoped server-side,
    // flat like 'all', per HOME_STRIPS_SPEC.md 5.2.
    const cacheKey = activeSurface === 'fieldview' ? `field:${viewField}:${viewFieldValue}` : `folder:${viewFolderPath}`;
    pool = viewLibraryCache[cacheKey] || [];
  } else {
    pool = allLibrary;
    if (activeSurface === 'series')  pool = pool.filter(s => s.format_group === 'Series');
    if (activeSurface === 'singles') pool = pool.filter(s => s.format_group === 'Singles');
    // 'all' = both
  }

  // Inline search
  if (activeSearch) {
    const q = activeSearch.toLowerCase();
    pool = pool.filter(s =>
      s.series.toLowerCase().includes(q) ||
      (s.publisher || '').toLowerCase().includes(q) ||
      (s.genres || []).some(g => g.toLowerCase().includes(q)) ||
      (s.writers || []).some(w => w.toLowerCase().includes(q))
    );
  }

  // Status
  if (activeStatus === 'unread')  pool = pool.filter(s => s.unread_count === s.issue_count);
  if (activeStatus === 'reading') pool = pool.filter(s => s.reading_count > 0);
  if (activeStatus === 'read')    pool = pool.filter(s => s.read_count === s.issue_count);

  // Dropdowns
  if (activeGenre)     pool = pool.filter(s => (s.genres     || []).includes(activeGenre));
  if (activePublisher) pool = pool.filter(s => s.publisher === activePublisher);
  if (activeFormat)    pool = pool.filter(s => (s.formats    || []).includes(activeFormat));
  if (activeRating)    pool = pool.filter(s => (s.age_ratings|| []).includes(activeRating));
  if (activeDecade)    pool = pool.filter(s => s.year && Math.floor(s.year/10)*10 === parseInt(activeDecade));
  if (activeYear)      pool = pool.filter(s => String(s.year) === String(activeYear));
  if (activeBW === 'yes') pool = pool.filter(s => s.has_bw);
  if (activeBW === 'no')  pool = pool.filter(s => !s.has_bw);

  // Sort
  if (activeSort === 'newest') {
    pool = [...pool].sort((a, b) => (b.year || 0) - (a.year || 0));
  } else if (activeSort === 'recent') {
    // 'recent' = by date_added; not available per series in library response,
    // so fall through to alpha (date_added would require a different endpoint)
    pool = [...pool].sort((a, b) => a.series.localeCompare(b.series));
  } else {
    pool = [...pool].sort((a, b) =>
      a.series.replace(/^['"]/,'').localeCompare(b.series.replace(/^['"]/,''))
    );
  }

  return pool;
}

function hasActiveFilters() {
  return activeSearch || activeStatus || activeGenre || activePublisher ||
    activeFormat || activeDecade ||
    activeYear || activeRating || activeBW;
}

function clearAllFilters() {
  activeStatus = activeGenre = activePublisher =
    activeFormat = activeDecade = activeYear = activeRating = activeBW = activeSearch = '';

  ['genreFilter','publisherFilter',
   'formatFilter','decadeFilter','yearFilter','ratingFilter','bwFilter'].forEach(id => {
    const el_ = document.getElementById(id);
    if (el_) { el_.value = ''; el_.classList.remove('active'); }
  });

  document.querySelectorAll('.status-pill').forEach(p => {
    p.classList.toggle('active', p.dataset.status === '');
  });

  const input = document.getElementById('searchInput');
  if (input) { input.value = ''; }
  document.getElementById('searchClear').style.display = 'none';
}

function renderBrowse() {
  currentPage = 1;
  _renderBrowsePage();
}

function _renderBrowsePage() {
  exitSelectionMode();
  const grid    = document.getElementById('coverGrid');
  const countEl = document.getElementById('browseCount');
  const clearBtn= document.getElementById('filterClear');
  const pagEl   = document.getElementById('pagination');

  const filtered   = getFilteredLibrary();
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  currentPage      = Math.min(currentPage, totalPages);

  // All surface (and custom tabs / strip "view all" pages, flat like All)
  // show grand total of individual comics (spec 20.1 / 20.3). Series and
  // Singles show card count.
  const flat = isFlatSurface(activeSurface);
  const displayCount = flat
    ? filtered.reduce((sum, s) => sum + (s.issue_count || 1), 0)
    : filtered.length;
  const countSuffix = { series: 'Series', singles: 'Titles', all: 'Titles' };
  const suffix = flat ? 'Titles' : (countSuffix[activeSurface] || '');
  countEl.textContent = suffix
    ? `${displayCount.toLocaleString()} ${suffix}`
    : displayCount.toLocaleString();
  clearBtn.style.display = hasActiveFilters() ? 'inline-block' : 'none';

  grid.innerHTML = '';

  if (!filtered.length) {
    grid.innerHTML =
      '<div class="empty-state"><div class="empty-icon">📚</div>' +
      '<p>No comics match these filters.</p></div>';
    if (pagEl) pagEl.innerHTML = '';
    return;
  }

  // Slice to current page
  const start     = (currentPage - 1) * pageSize;
  const pageItems = filtered.slice(start, start + pageSize);

  // Group-by
  if (activeGroupBy && activeGroupBy !== '') {
    renderGrouped(grid, pageItems);
  } else {
    const frag = document.createDocumentFragment();
    for (const s of pageItems) frag.appendChild(buildCoverCard(s));
    grid.appendChild(frag);
  }

  if (pagEl) renderPagination(pagEl, totalPages);
}

function pageWindow(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = new Set([1, total]);
  for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) pages.add(i);
  return [...pages].sort((a, b) => a - b);
}

function renderPagination(container, totalPages) {
  container.innerHTML = '';
  if (totalPages <= 1) return;

  const makeBtn = (label, page, isCurrent, disabled) => {
    const btn = el('button', 'page-btn' + (isCurrent ? ' page-btn--current' : ''), label);
    if (disabled) btn.disabled = true;
    else btn.addEventListener('click', () => {
      currentPage = page;
      _renderBrowsePage();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    return btn;
  };

  container.appendChild(makeBtn('‹', currentPage - 1, false, currentPage === 1));

  let prev = null;
  for (const p of pageWindow(currentPage, totalPages)) {
    if (prev !== null && p - prev > 1) container.appendChild(el('span', 'page-ellipsis', '…'));
    container.appendChild(makeBtn(String(p), p, p === currentPage, false));
    prev = p;
  }

  container.appendChild(makeBtn('›', currentPage + 1, false, currentPage === totalPages));
}

function renderGrouped(grid, items) {
  const groups = new Map();
  for (const s of items) {
    let key = '';
    if (activeGroupBy === 'year')      key = String(s.year || 'Unknown');
    if (activeGroupBy === 'publisher') key = s.publisher || 'Unknown';
    if (activeGroupBy === 'genre')     key = (s.genres && s.genres[0]) || 'Unknown';
    if (activeGroupBy === 'writer')    key = (s.writers && s.writers[0]) || 'Unknown';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  }

  for (const [groupName, groupItems] of groups) {
    const heading = el('div', 'group-heading', groupName);
    heading.style.gridColumn = '1 / -1';
    grid.appendChild(heading);
    for (const s of groupItems) grid.appendChild(buildCoverCard(s));
  }
}

// ── Card builder ──────────────────────────────────────────────────────────────

function seriesReadState(s) {
  if (s.read_count === s.issue_count) return 'state-read';
  if (s.read_count > 0 || s.reading_count > 0) return 'state-part-read';
  return 'state-unread';
}

function buildCoverCard(s) {
  const isSingle = s.format_group === 'Singles';
  const from     = activeSurface ? `?from=${activeSurface}` : '';
  const href     = isSingle
    ? `/issue/${s.series_anchor_id}${from}`
    : `/series/${s.series_anchor_id}${from}`;
  const state    = seriesReadState(s);

  const card = el('a', `cover-card ${state}${s.favorites ? ' is-favorite' : ''}`);
  card.href  = href;

  // Multi-select only on single-issue cards (Singles) — series-aggregate
  // cards stay click-to-navigate only (Tier 4 Item 2 scope decision).
  if (isSingle) makeSelectable(card, s.series_anchor_id);

  const wrap = el('div', 'cover-img-wrap');
  const img  = el('img');
  img.src     = s.cover_path;
  img.alt     = s.series;
  img.loading = 'lazy';
  img.onerror = () => { wrap.innerHTML = '<div class="cover-placeholder">📖</div>'; };
  wrap.appendChild(img);

  if (s.unread_count > 0 && s.unread_count < s.issue_count) {
    wrap.appendChild(el('span', 'unread-badge', s.unread_count));
  }

  // Part-read progress bar (grid view)
  if (state === 'state-part-read') {
    const pct  = Math.round((s.read_count / s.issue_count) * 100);
    const bar  = el('div', 'card-progress-bar');
    bar.style.width = `${pct}%`;
    wrap.appendChild(bar);
  }

  const info = el('div', 'cover-info');
  info.appendChild(el('div', 'cover-title', s.series));

  // Grid info — spec 20.5: Title, Year, # issues (series) / page count (singles)
  if (isSingle) {
    if (s.year)       info.appendChild(el('div', 'cover-year',  String(s.year)));
    if (s.page_count) info.appendChild(el('div', 'cover-count', `${s.page_count} pages`));
  } else {
    if (s.year) info.appendChild(el('div', 'cover-year', String(s.year)));
    info.appendChild(el('div', 'cover-count',
      `${s.issue_count} issue${s.issue_count !== 1 ? 's' : ''}`
    ));
  }

  // List-view extras — hidden in grid mode via CSS (spec 20.5)
  const listMeta = el('div', 'list-meta');
  if (s.genres && s.genres.length) {
    listMeta.appendChild(el('div', 'list-genres', s.genres.join(' · ')));
  }
  const metaParts = [s.publisher, s.writers && s.writers[0]].filter(Boolean);
  if (metaParts.length) listMeta.appendChild(el('div', 'list-pub-writer', metaParts.join(' · ')));
  if (s.summary)        listMeta.appendChild(el('div', 'list-summary', s.summary));
  // List view shows "X% Read" text instead of the grid progress bar
  if (state === 'state-part-read') {
    const pct = Math.round((s.read_count / s.issue_count) * 100);
    listMeta.appendChild(el('div', 'list-progress-text', `${pct}% Read`));
  }
  info.appendChild(listMeta);

  card.append(wrap, info);
  return card;
}

// ── Search (inline) ───────────────────────────────────────────────────────────

function bindSearchEvents() {
  const input    = document.getElementById('searchInput');
  const clearBtn = document.getElementById('searchClear');
  if (!input) return;

  const doSearch = debounce(q => {
    activeSearch = q;
    renderBrowse();
  }, 260);

  input.addEventListener('input', e => {
    const q = e.target.value.trim();
    clearBtn.style.display = q ? 'block' : 'none';
    doSearch(q);
  });

  clearBtn.addEventListener('click', () => {
    input.value            = '';
    clearBtn.style.display = 'none';
    activeSearch = '';
    input.focus();
    renderBrowse();
  });
}

// ── Filter events ─────────────────────────────────────────────────────────────

function bindFilterEvents() {
  // Status pills
  document.querySelectorAll('.status-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.status-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeStatus = pill.dataset.status;
      renderBrowse();
    });
  });

  // Dropdown helpers
  const bindSelect = (id, setter) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.addEventListener('change', e => {
      setter(e.target.value);
      e.target.classList.toggle('active', !!e.target.value);
      renderBrowse();
    });
  };

  bindSelect('genreFilter',     v => activeGenre     = v);
  bindSelect('publisherFilter', v => activePublisher = v);
  bindSelect('formatFilter',    v => activeFormat    = v);
  bindSelect('decadeFilter',    v => activeDecade    = v);
  bindSelect('yearFilter',      v => activeYear      = v);
  bindSelect('ratingFilter',    v => activeRating    = v);
  bindSelect('bwFilter',        v => activeBW        = v);

  document.getElementById('filterClear').addEventListener('click', () => {
    clearAllFilters();
    renderBrowse();
  });

  // Sort toggle
  const sortBtn = document.getElementById('sortBtn');
  const SORT_CYCLE = ['alpha', 'newest', 'recent'];
  const SORT_LABELS = { alpha: 'A–Z', newest: 'Newest', recent: 'Recent' };
  sortBtn.addEventListener('click', () => {
    const idx = SORT_CYCLE.indexOf(activeSort);
    activeSort = SORT_CYCLE[(idx + 1) % SORT_CYCLE.length];
    sortBtn.textContent = SORT_LABELS[activeSort];
    renderBrowse();
  });

  // Group by
  document.getElementById('groupBySelect').addEventListener('change', e => {
    activeGroupBy = e.target.value;
    renderBrowse();
  });

  // Grid / list toggle — sync initial state from localStorage then persist on change
  const viewBtn = document.getElementById('viewToggle');
  viewBtn.textContent = viewMode === 'list' ? '⊞' : '☰';
  document.getElementById('coverGrid').classList.toggle('list-view', viewMode === 'list');
  viewBtn.addEventListener('click', () => {
    viewMode = viewMode === 'grid' ? 'list' : 'grid';
    localStorage.setItem('cv_view_mode', viewMode);
    document.getElementById('coverGrid').classList.toggle('list-view', viewMode === 'list');
    viewBtn.textContent = viewMode === 'list' ? '⊞' : '☰';
  });
}

// ══════════════════════════════════════════════════════════════════════════════
//  2000 AD SURFACE
// ══════════════════════════════════════════════════════════════════════════════

let adYearsData = null;

async function load2000AD() {
  // Show year grid, hide detail
  document.getElementById('adYearGrid').hidden   = false;
  document.getElementById('adYearDetail').hidden = true;

  if (adYearsData) { render2000ADYears(adYearsData); return; }

  document.getElementById('adYearGrid').innerHTML = '<div class="loading-state">Loading…</div>';
  try {
    adYearsData = await apiFetch('/2000ad/years');
    render2000ADYears(adYearsData);
  } catch (err) {
    document.getElementById('adYearGrid').innerHTML =
      '<div class="empty-state"><div class="empty-icon">⚠️</div><p>Could not load 2000 AD data.</p></div>';
  }
}

function render2000ADYears(years) {
  const grid = document.getElementById('adYearGrid');
  grid.innerHTML = '';

  const frag = document.createDocumentFragment();
  for (const y of years) {
    frag.appendChild(buildYearCard(y));
  }
  grid.appendChild(frag);
}

function buildYearCard(y) {
  const card = el('div', 'year-card');
  card.addEventListener('click', () => load2000ADYear(y.year));

  const coverWrap = el('div', 'year-card-cover');
  if (y.cover_path) {
    const img = el('img');
    img.src     = y.cover_path;
    img.alt     = `${y.year}`;
    img.loading = 'lazy';
    img.onerror = () => { img.style.display = 'none'; };
    coverWrap.appendChild(img);
  }
  card.appendChild(coverWrap);

  const yearLabel = el('div', 'year-card-year', String(y.year));
  card.appendChild(yearLabel);

  const range = y.first_prog && y.last_prog
    ? `#${y.first_prog}–${y.last_prog}`
    : `${y.issue_count} issues`;
  card.appendChild(el('div', 'year-card-range', range));

  return card;
}

function buildAdProgCard(issue) {
  const state = issue.read_status === 'read'    ? 'state-read'
              : issue.read_status === 'reading'  ? 'state-part-read'
              : 'state-unread';

  const card = el('a', `cover-card ${state}${issue.missing ? ' missing' : ''}${issue.favorites ? ' is-favorite' : ''}`);
  card.href  = `/issue/${issue.id}`;
  makeSelectable(card, issue.id);

  const wrap = el('div', 'cover-img-wrap');
  const img  = el('img');
  img.src     = issue.cover_path;
  img.alt     = `Prog #${issue.number}`;
  img.loading = 'lazy';
  img.onerror = () => { wrap.innerHTML = '<div class="cover-placeholder">📖</div>'; };
  wrap.appendChild(img);

  if (state === 'state-part-read' && issue.page_count > 0) {
    const pct = Math.min(100, Math.round((issue.current_page / issue.page_count) * 100));
    const bar = el('div', 'card-progress-bar');
    bar.style.width = `${pct}%`;
    wrap.appendChild(bar);
  }

  const info = el('div', 'cover-info');
  info.appendChild(el('div', 'cover-title', issue.title || `Prog #${issue.number}`));
  if (issue.number)     info.appendChild(el('div', 'cover-count', `Issue #${issue.number}`));
  if (issue.page_count) info.appendChild(el('div', 'cover-count', `${issue.page_count} pages`));

  card.append(wrap, info);
  return card;
}

async function load2000ADYear(year) {
  exitSelectionMode();
  document.getElementById('adYearGrid').hidden   = true;
  document.getElementById('adYearDetail').hidden = false;
  document.getElementById('adYearContent').innerHTML = '<div class="loading-state">Loading…</div>';

  document.getElementById('adBackBtn').onclick = () => {
    document.getElementById('adYearGrid').hidden   = false;
    document.getElementById('adYearDetail').hidden = true;
  };

  try {
    const data = await apiFetch(`/2000ad/year/${year}`);
    const content = document.getElementById('adYearContent');
    content.innerHTML = '';

    content.appendChild(el('h2', 'ad-year-heading', String(year)));

    const grid = el('div', 'cover-grid');
    for (const iss of data.issues) grid.appendChild(buildAdProgCard(iss));
    content.appendChild(grid);
  } catch (err) {
    document.getElementById('adYearContent').innerHTML =
      '<div class="empty-state"><p>Could not load issues for this year.</p></div>';
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  SERIES PAGE
// ══════════════════════════════════════════════════════════════════════════════

async function initSeries() {
  const issueId = window.location.pathname.replace(/^\/series\//, '');
  const from    = new URLSearchParams(location.search).get('from') || '';
  const content = document.getElementById('seriesContent');

  try {
    const data = await apiFetch(`/series/${issueId}`);
    document.title = `${data.series} — ComicVault`;
    content.innerHTML = '';
    content.appendChild(buildSeriesHeader(data));
    content.appendChild(buildIssueList(data, from));
  } catch (_) {
    content.innerHTML =
      '<div class="empty-state" style="padding-top:60px">' +
      '<div class="empty-icon">⚠️</div><p>Series not found.</p></div>';
  }
}

// ── Series header with backdrop (Section 20.6) ───────────────────────────────

function buildSeriesHeader(data) {
  const wrapper = el('div', 'series-hero-wrap');

  // Backdrop image layer
  if (data.cover_path) {
    const backdrop = el('div', 'series-backdrop');
    const bdImg    = el('img', 'series-backdrop-img');
    bdImg.src = data.cover_path;
    bdImg.alt = '';
    bdImg.setAttribute('aria-hidden', 'true');
    backdrop.appendChild(bdImg);
    wrapper.appendChild(backdrop);
  }

  // Content over backdrop
  const hero = el('div', 'series-hero');

  // Top row: back link + mark-all-read
  const _from    = new URLSearchParams(location.search).get('from') || '';
  const _LABELS  = { home: 'Home', series: 'Series', singles: 'Singles', all: 'All' };
  const _label   = _LABELS[_from] || customTabLabel(_from) || 'Library';
  const _backHref = (_from && _from !== 'home') ? `/?surface=${_from}` : '/';

  const topRow = el('div', 'series-hero-top');
  const backLink = el('a', 'btn-primary', `← ${_label}`);
  backLink.href = _backHref;
  topRow.appendChild(backLink);

  const markBtn = el('button', 'btn-primary series-mark-btn', 'Mark all read');
  markBtn.id = 'markAllBtn';
  markBtn.addEventListener('click', () => markAllRead(data.issues));
  topRow.appendChild(markBtn);
  hero.appendChild(topRow);

  // Title
  hero.appendChild(el('h1', 'series-name', data.series));

  // Publisher · Year
  const pubParts = [data.publisher, data.year].filter(Boolean);
  if (pubParts.length) hero.appendChild(el('p', 'series-pub', pubParts.join(' · ')));

  // Genre tags
  if (data.genres && data.genres.length) {
    const tags = el('div', 'genre-tags');
    for (const g of data.genres) tags.appendChild(el('span', 'genre-tag', g));
    hero.appendChild(tags);
  }

  // Issue count
  hero.appendChild(el('p', 'series-stats',
    `${data.issue_count} issue${data.issue_count !== 1 ? 's' : ''}`
  ));

  wrapper.appendChild(hero);
  return wrapper;
}

// ── Issue list — flat by default (Section 20.7) ──────────────────────────────

function buildIssueList(data, from) {
  const wrapper = el('div', 'issue-list');
  const group   = el('div', 'arc-group');
  for (const issue of data.issues) group.appendChild(buildIssueRow(issue, from));
  wrapper.appendChild(group);
  return wrapper;
}

function buildIssueRow(issue, from) {
  const readState = issue.read_status === 'read'    ? 'state-read'
                  : issue.read_status === 'reading' ? 'state-reading' : '';
  const cls = ['issue-row', issue.missing ? 'missing' : '', readState, issue.favorites ? 'is-favorite' : '']
    .filter(Boolean).join(' ');
  const row = el('a', cls);
  row.href  = `/issue/${issue.id}${from ? `?from=${from}` : ''}`;
  makeSelectable(row, issue.id);

  // Thumbnail
  const thumb = el('div', 'issue-thumb');
  const tImg  = el('img');
  tImg.src     = issue.cover_path;
  tImg.alt     = '';
  tImg.loading = 'lazy';
  tImg.onerror = () => { thumb.textContent = ''; };
  thumb.appendChild(tImg);
  row.appendChild(thumb);

  // Issue number
  const numText = issue.number != null && issue.number !== '' ? `#${issue.number}` : '—';
  row.appendChild(el('div', 'issue-num', numText));

  // Detail column: title, year · pages (left-aligned), optional summary, progress
  const detail = el('div', 'issue-detail');
  detail.appendChild(el('div', 'issue-title', issue.title || ''));

  const subParts = [
    issue.year       ? String(issue.year)              : null,
    issue.page_count ? `${issue.page_count} pages`     : null,
  ].filter(Boolean);
  if (subParts.length) detail.appendChild(el('div', 'issue-sub', subParts.join(' · ')));

  if (issue.summary) detail.appendChild(el('div', 'issue-summary', issue.summary));

  if (issue.read_status === 'reading' && issue.page_count > 0) {
    const pct   = Math.min(100, Math.round((issue.current_page / issue.page_count) * 100));
    const track = el('div', 'issue-progress-track');
    const fill  = el('div', 'issue-progress-fill');
    fill.style.width = `${pct}%`;
    track.appendChild(fill);
    detail.appendChild(track);
  }

  row.appendChild(detail);
  row.appendChild(buildStatusButton(issue));

  return row;
}

function buildStatusButton(issue) {
  const STATUS_ICON = { read: '✓', reading: '▶', unread: '' };
  const btn = el('button', `status-btn ${issue.read_status}`, STATUS_ICON[issue.read_status] || '');
  btn.title = `Status: ${issue.read_status}`;

  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const next = issue.read_status === 'read' ? 'unread' : 'read';
    const endpoint = next === 'read'
      ? `/api/progress/${issue.id}/mark-read`
      : `/api/progress/${issue.id}/mark-unread`;
    try {
      await fetch(endpoint, { method: 'POST' });
      issue.read_status    = next;
      btn.className        = `status-btn ${next}`;
      btn.textContent      = STATUS_ICON[next] || '';
      btn.title            = `Status: ${next}`;
    } catch (_) {}
  });

  return btn;
}

// ── Mark all read ─────────────────────────────────────────────────────────────

async function markAllRead(issues) {
  const btn = document.getElementById('markAllBtn');
  btn.disabled    = true;
  btn.textContent = 'Marking…';

  const unread = issues.filter(i => i.read_status !== 'read');
  if (!unread.length) {
    btn.textContent = 'All read ✓';
    return;
  }

  await Promise.allSettled(
    unread.map(i => fetch(`/api/progress/${i.id}/mark-read`, { method: 'POST' }))
  );

  for (const issue of issues) issue.read_status = 'read';

  document.querySelectorAll('.status-btn').forEach(b => {
    b.className   = 'status-btn read';
    b.textContent = '✓';
    b.title       = 'Status: read';
  });

  btn.textContent       = 'All read ✓';
  btn.style.background  = 'var(--green)';
  btn.style.color       = '#000';
}

// ══════════════════════════════════════════════════════════════════════════════
//  ISSUE DETAIL PAGE
// ══════════════════════════════════════════════════════════════════════════════

async function initIssue() {
  const issueId = window.location.pathname.replace(/^\/issue\//, '');
  const from    = new URLSearchParams(location.search).get('from') || '';
  const LABELS  = { home: 'Home', series: 'Series', singles: 'Singles', all: 'All' };
  const content = document.getElementById('issueContent');

  try {
    const data = await apiFetch(`/issue/${issueId}`);

    const numSuffix = data.number ? ` #${data.number}` : '';
    document.title = `${data.series}${numSuffix} — ComicVault`;

    // Back link: singles return to source surface; series issues return to series page
    const backLink = document.getElementById('backLink');
    if (data.format_group === 'Singles') {
      backLink.href        = (from && from !== 'home') ? `/?surface=${from}` : '/';
      backLink.textContent = `← ${LABELS[from] || customTabLabel(from) || 'Library'}`;
    } else {
      backLink.href        = `/series/${data.id}${from ? `?from=${from}` : ''}`;
      backLink.textContent = `← ${data.series}`;
    }

    content.innerHTML = '';
    content.appendChild(buildIssueDetail(data));
  } catch (_) {
    content.innerHTML =
      '<div class="empty-state" style="padding-top:60px">' +
      '<div class="empty-icon">⚠️</div><p>Issue not found.</p></div>';
  }
}

// ── Issue detail layout ───────────────────────────────────────────────────────

function buildIssueDetail(data) {
  const page = document.createDocumentFragment();

  // ── Two-column layout ──
  const layout = el('div', 'issue-layout');

  // Left: cover + actions
  const coverCol = el('div', 'issue-cover-col');

  const img = el('img', 'issue-cover-img');
  img.src     = data.cover_path || '';
  img.alt     = data.series;
  img.onerror = () => { img.style.display = 'none'; };
  coverCol.appendChild(img);

  const actions = el('div', 'issue-actions');
  const readBtn = el('a', 'btn-read', 'Read');
  readBtn.href = `comicvault://read/${data.id}`;
  readBtn.title = 'Open in ComicVault app';
  actions.appendChild(readBtn);
  actions.appendChild(buildStatusToggle(data));
  actions.appendChild(buildFavoriteToggle(data));
  actions.appendChild(buildRatingControl(data));
  const editXmlBtn = el('button', 'btn-edit-xml', 'Edit XML');
  editXmlBtn.type = 'button';
  editXmlBtn.onclick = () => openEditorModal(data.id, () => initIssue());
  actions.appendChild(editXmlBtn);
  coverCol.appendChild(actions);

  // Right: metadata
  const metaCol = el('div', 'issue-meta-col');

  // Series title
  metaCol.appendChild(el('h1', 'issue-series-title', data.series));

  // Badges: issue number (with series count if known), format, B&W
  const badges = el('div', 'badge-row');
  if (data.number != null && data.number !== '') {
    const numText = data.count ? `#${data.number} of ${data.count}` : `#${data.number}`;
    badges.appendChild(el('span', 'issue-num-badge', numText));
  }
  if (data.format) {
    badges.appendChild(el('span', 'format-badge', data.format));
  }
  if (data.black_and_white) {
    badges.appendChild(el('span', 'bw-badge', 'B&W'));
  }
  if (badges.children.length) metaCol.appendChild(badges);

  // Publisher · Year · Language
  const pubParts = [data.publisher, data.year, data.language].filter(Boolean);
  if (pubParts.length) {
    metaCol.appendChild(el('p', 'issue-pub-info', pubParts.join(' · ')));
  }

  // Genres
  if (data.genres && data.genres.length) {
    const tags = el('div', 'genre-tags');
    for (const g of data.genres) tags.appendChild(el('span', 'genre-tag', g));
    metaCol.appendChild(tags);
  }

  // Summary
  if (data.summary) {
    const sec = el('div', 'meta-section');
    sec.appendChild(el('p', 'meta-label', 'Summary'));
    sec.appendChild(el('p', 'summary-text', data.summary));
    metaCol.appendChild(sec);
  }

  // Story arc
  if (data.story_arc) {
    const arcText = data.story_arc_number
      ? `${data.story_arc} (Part ${data.story_arc_number})`
      : data.story_arc;
    const sec = el('div', 'meta-section');
    sec.appendChild(el('p', 'meta-label', 'Story Arc'));
    sec.appendChild(el('p', 'meta-value', arcText));
    metaCol.appendChild(sec);
  }

  // Credits — Writer and Artist (penciller) only; remaining fields stored in DB but not displayed.
  // Each name links to a filtered list of every issue they're credited on
  // (Tier 4 Item 3 — reuses the existing fieldview surface plumbing).
  const creditFields = [
    ['Writer', 'writer', data.writers],
    ['Artist', 'artist', data.pencillers],
  ].filter(([, , people]) => people && people.length);

  if (creditFields.length) {
    const sec = el('div', 'meta-section');
    sec.appendChild(el('p', 'meta-label', 'Credits'));
    const grid = el('div', 'credits-grid');
    for (const [label, fieldName, people] of creditFields) {
      grid.appendChild(el('span', 'credit-label', label));
      const valueCell = el('span', 'credit-value');
      people.forEach((person, idx) => {
        if (idx > 0) valueCell.appendChild(document.createTextNode(', '));
        const link = el('a', 'credit-link', person.name);
        link.href = `/?surface=fieldview&field=${fieldName}&value=${person.person_id}`;
        valueCell.appendChild(link);
      });
      grid.appendChild(valueCell);
    }
    sec.appendChild(grid);
    metaCol.appendChild(sec);
  }

  // Age rating + page count (Characters, Teams, Locations stored in DB but not displayed)
  const extras = [
    data.age_rating ? `Rated: ${data.age_rating}` : null,
    data.page_count ? `${data.page_count} pages` : null,
  ].filter(Boolean);
  if (extras.length) {
    metaCol.appendChild(el('p', 'issue-extras', extras.join(' · ')));
  }

  layout.append(coverCol, metaCol);
  page.appendChild(layout);

  // ── Prev / Next navigation ──
  if (data.prev_issue_id || data.next_issue_id) {
    page.appendChild(buildIssueNav(data));
  }

  return page;
}

// ── Status toggle button ──────────────────────────────────────────────────────

function buildStatusToggle(data) {
  const btn = el('button', 'btn-status-toggle');

  function sync() {
    if (data.read_status === 'read') {
      btn.textContent = '✓ Read';
      btn.classList.add('is-read');
    } else {
      btn.textContent = 'Mark as Read';
      btn.classList.remove('is-read');
    }
  }
  sync();

  btn.addEventListener('click', async () => {
    const next     = data.read_status === 'read' ? 'unread' : 'read';
    const endpoint = next === 'read'
      ? `/api/progress/${data.id}/mark-read`
      : `/api/progress/${data.id}/mark-unread`;
    try {
      await fetch(endpoint, { method: 'POST' });
      data.read_status = next;
      sync();
    } catch (_) {}
  });

  return btn;
}

// ── Favorite toggle + star rating (standalone, independent of multi-select) ───
// Both reuse the same bulk endpoints with a 1-item issue_ids list — one code
// path for multi-select and single-issue use, no separate endpoints needed.

function buildFavoriteToggle(data) {
  const btn = el('button', 'btn-favorite-toggle');

  function sync() {
    btn.textContent = data.favorites ? '★ Favorited' : '☆ Add to Favorites';
    btn.classList.toggle('is-favorite', !!data.favorites);
  }
  sync();

  btn.addEventListener('click', async () => {
    const endpoint = data.favorites ? '/api/progress/bulk/unfavorite' : '/api/progress/bulk/favorite';
    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_ids: [data.id] }),
      });
      data.favorites = !data.favorites;
      sync();
    } catch (_) {}
  });

  return btn;
}

function buildRatingControl(data) {
  const wrap = el('div', 'rating-control');

  function sync() {
    wrap.querySelectorAll('.rating-star').forEach(s => {
      s.classList.toggle('is-filled', Number(s.dataset.value) <= (data.personal_rating || 0));
    });
  }

  for (let i = 1; i <= 5; i++) {
    const star = el('button', 'rating-star', '★');
    star.type = 'button';
    star.dataset.value = i;
    star.title = `Rate ${i}`;
    star.addEventListener('click', async () => {
      try {
        await fetch('/api/progress/bulk/rate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ issue_ids: [data.id], rating: i }),
        });
        data.personal_rating = i;
        sync();
      } catch (_) {}
    });
    wrap.appendChild(star);
  }
  sync();

  return wrap;
}

// ── CSV block (characters, teams, locations) ──────────────────────────────────

function buildCsvSection(label, csv) {
  const sec  = el('div', 'meta-section');
  sec.appendChild(el('p', 'meta-label', label));
  const tags = el('div', 'csv-tags');
  for (const item of csv.split(',').map(s => s.trim()).filter(Boolean)) {
    tags.appendChild(el('span', 'csv-tag', item));
  }
  sec.appendChild(tags);
  return sec;
}

// ── Prev / Next issue navigation ──────────────────────────────────────────────

function buildIssueNav(data) {
  const nav = el('div', 'issue-nav');

  if (data.prev_issue_id) {
    const prev  = el('a', 'nav-issue-btn nav-prev', '← Previous');
    prev.href   = `/issue/${data.prev_issue_id}`;
    nav.appendChild(prev);
  } else {
    nav.appendChild(el('span', 'nav-placeholder'));
  }

  const seriesLink  = el('a', 'nav-series-link', data.series);
  seriesLink.href   = data.format_group === 'Singles' ? '/' : `/series/${data.id}`;
  nav.appendChild(seriesLink);

  if (data.next_issue_id) {
    const next  = el('a', 'nav-issue-btn nav-next', 'Next →');
    next.href   = `/issue/${data.next_issue_id}`;
    nav.appendChild(next);
  } else {
    nav.appendChild(el('span', 'nav-placeholder'));
  }

  return nav;
}
