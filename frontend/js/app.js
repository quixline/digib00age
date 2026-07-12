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

// Personal-rating pill (bottom-right of card/cover) — vertical stack of gold
// stars, one per rating point. Inbox 2026-07-11.
function buildRatingPill(rating) {
  const pill = el('div', 'card-rating-pill');
  for (let i = 0; i < rating; i++) pill.appendChild(el('span', 'rating-star', '★'));
  return pill;
}

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// ══════════════════════════════════════════════════════════════════════════════
//  MULTI-SELECT — long-press to select, short tap to add more
//  Attached to single-issue elements (Singles cards, series-detail issue
//  rows, Folder View flat file cards) and, as of DECISIONS.md's 2026-06-23
//  scope correction, Series-aggregate cards too. A selection entry's kind
//  ('issue' | 'series') is tracked in selectedIds so a bulk action can
//  expand a selected series into all its issue ids server-side, while still
//  patching just the one series card's own DOM node + cached counts
//  afterward — see resolveBulkIssueIds().
// ══════════════════════════════════════════════════════════════════════════════

const LONG_PRESS_MS         = 500;
const PRESS_MOVE_TOLERANCE  = 10;  // px — a drag/scroll cancels the long-press

let selectionActive = false;
const selectedIds   = new Map();   // id -> 'issue' | 'series'

// Shared by the long-press gesture (makeSelectable()) and the CoverCard
// select-dot's click handler — either enters selection mode (first pick)
// or toggles this id within an already-active selection.
function selectOrToggle(id, kind = 'issue') {
  if (!selectionActive) enterSelectionMode(id, kind);
  else toggleSelected(id, kind);
}

// Hover-reveal selection circle (grid view only, hidden via CSS in list
// view) — a discoverable, single-click alternative to the long-press
// gesture above. Appended into a card's .cover-img-wrap, same parent as
// the unread-badge/card-progress-bar.
function buildSelectDot(id, kind = 'issue') {
  const dot = el('span', 'select-dot');
  dot.setAttribute('role', 'checkbox');
  dot.setAttribute('aria-label', 'Select');
  dot.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    selectOrToggle(id, kind);
  });
  return dot;
}

function makeSelectable(element, issueId, kind = 'issue') {
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
      selectOrToggle(issueId, kind);
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
      if (!firedLongPress) toggleSelected(issueId, kind);  // short tap while already selecting
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

function enterSelectionMode(firstId, kind) {
  selectionActive = true;
  showSelectionToolbar();
  toggleSelected(firstId, kind);
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

function toggleSelected(id, kind = 'issue') {
  if (selectedIds.has(id)) selectedIds.delete(id);
  else selectedIds.set(id, kind);

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
  mkBtn('selFavorite',   '★ Favorite', () => {
    const ids = Array.from(selectedIds.keys());
    const allFavorited = ids.length > 0 && ids.every(id => {
      const node = document.querySelector(`[data-issue-id="${id}"]`);
      return node && node.classList.contains('is-favorite');
    });
    const path = allFavorited ? '/progress/bulk/unfavorite' : '/progress/bulk/favorite';
    runBulkAction(path, {}, idsApplied => applyFavoriteToDom(idsApplied, !allFavorited));
  });

  const rateWrap = el('div', 'selection-rate');
  const clearStar = el('button', 'rating-star rating-clear', '✕');
  clearStar.type  = 'button';
  clearStar.title = 'Clear rating';
  clearStar.addEventListener('click', () =>
    runBulkAction('/progress/bulk/rate', { rating: 0 }, ids => applyRatingToDom(ids, 0)));
  rateWrap.appendChild(clearStar);
  for (let i = 1; i <= 5; i++) {
    const star = el('button', 'rating-star', '★');
    star.type  = 'button';
    star.title = `Rate ${i}`;
    star.addEventListener('click', () =>
      runBulkAction('/progress/bulk/rate', { rating: i }, ids => applyRatingToDom(ids, i)));
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

// Expands any selected series-aggregate entries into every issue id under
// that series (via the same /series/{id} endpoint the series-detail page
// already uses), so the server-side bulk action actually applies to the
// whole series — not just its cover issue. Plain issue selections pass
// through unchanged.
async function resolveBulkIssueIds() {
  const ids = new Set();
  await Promise.all(Array.from(selectedIds.entries()).map(async ([id, kind]) => {
    if (kind === 'series') {
      const data = await apiFetch(`/series/${id}`);
      for (const issue of data.issues) ids.add(issue.id);
    } else {
      ids.add(id);
    }
  }));
  return Array.from(ids);
}

async function runBulkAction(path, extraBody, applyFn) {
  const originalIds = Array.from(selectedIds.keys());
  if (!originalIds.length) return;
  try {
    const issueIds = await resolveBulkIssueIds();
    await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ issue_ids: issueIds, ...extraBody }),
    });
    // Patch DOM/cache using the originally selected ids (series cards and
    // their cached aggregate counts), not the expanded per-issue ids —
    // there's no individual DOM node for issues inside an unopened series.
    if (applyFn) applyFn(originalIds);
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
    _patchFavoritesInCaches(id, value);
  }

  // CUSTOM_TABS_SPEC.md §10.5 — un-favouriting while viewing the Favourites
  // tab (or with the All-tab Favourites filter active) must remove the card
  // live, not just toggle its star. Fixed once here so both surfaces benefit.
  if (!value) {
    // A favourites-tab's cached pool was already scoped server-side at fetch
    // time (§10.3) — patching the flag alone doesn't re-exclude an entry the
    // way the client-side activeFavorites filter below does on every render,
    // so drop it from the cache outright (best-effort, same tolerance the
    // rest of this bulk-patch family already accepts — a reload reflects
    // true server state, e.g. if another issue in the same series is still
    // favourited).
    for (const tabId of Object.keys(tabLibraryCache)) {
      if (tabBasisTypes[tabId] !== 'favorites') continue;
      tabLibraryCache[tabId] = tabLibraryCache[tabId].filter(s => !ids.includes(s.series_anchor_id));
    }
  }

  if (!value && (activeFavorites || isFavoritesTab(activeSurface))) {
    renderBrowse();
  }
}

// Every cache getFilteredLibrary() might read favorites from — a bulk
// favourite/unfavourite only has a DOM node for series-aggregate cards
// (series_anchor_id), so this patches every pool that could contain one.
function _patchFavoritesInCaches(id, value) {
  const pools = [allLibrary, ...Object.values(tabLibraryCache),
    ...Object.values(viewLibraryCache), ...Object.values(searchLibraryCache)];
  for (const pool of pools) {
    const lib = (pool || []).find(s => s.series_anchor_id === id);
    if (lib) lib.favorites = value;
  }
}

// Bulk star rating — mirrors applyFavoriteToDom/_patchFavoritesInCaches.
// Swaps the .card-rating-pill in place so the selection toolbar's rating
// widget reflects immediately, without depending on a full reload.
function applyRatingToDom(ids, rating) {
  for (const id of ids) {
    const node = document.querySelector(`[data-issue-id="${id}"]`);
    const wrap = node && node.querySelector('.cover-img-wrap');
    if (wrap) {
      const existing = wrap.querySelector('.card-rating-pill');
      if (existing) existing.remove();
      if (rating > 0) wrap.appendChild(buildRatingPill(rating));
    }
    _patchRatingInCaches(id, rating);
  }
}

function _patchRatingInCaches(id, rating) {
  const pools = [allLibrary, ...Object.values(tabLibraryCache),
    ...Object.values(viewLibraryCache), ...Object.values(searchLibraryCache)];
  for (const pool of pools) {
    const lib = (pool || []).find(s => s.series_anchor_id === id);
    if (lib) lib.personal_rating = rating;
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
let activeSurface   = 'home';   // home | series | singles | all
let activeStatus    = '';       // '' | unread | reading | read
let activeGenre     = '';
let activeFormat    = '';
let activeDecade    = '';
let activeYear      = '';
let activeRating    = '';
let activeBW        = '';       // '' | yes | no
let activeSort       = 'alpha'; // alpha | newest | recent | issues | pages
let activeSortDir    = 'asc';   // asc | desc — MENU_BAR_SPEC.md §2.1
let activeStars      = '';      // '' | 1-5 — personal star rating, MENU_BAR_SPEC.md §2.2
let activeFavorites  = false;   // MENU_BAR_SPEC.md §2.3
let activeGroupBy   = '';       // '' | year | genre | publisher | writer | format
let activeSearch    = '';

// 'fieldview'/'folderview' surfaces — transient, opened from a home strip's
// clickable heading (HOME_STRIPS_SPEC.md 5.2), not part of the persistent nav.
let viewField       = '';
let viewFieldValue  = '';
let viewFieldLabel  = '';   // BUG-015: display label for viewFieldValue when the raw value
                             // isn't human-readable (writer/artist Person.id) — '' when the
                             // value is already self-describing (genre/publisher/etc.)
let viewFolderPath  = '';

// BUG-015: mirrors admin.js's HS_FIELD_LABELS (admin.js) — duplicated rather
// than shared because index.html and admin.html load separate, non-module
// script sets. Keep both in sync if a field is ever added/renamed.
const FIELDVIEW_LABELS = {
  genre: 'Genre', publisher: 'Publisher', writer: 'Writer', artist: 'Artist',
  format: 'Format', decade: 'Decade', year: 'Year', rating: 'Rating', bw: 'Black & White',
};

function fieldviewValueDisplay(field, value, label) {
  if (label) return label;                                        // writer/artist, when resolved
  if (field === 'decade') return `${value}s`;                      // "1990" -> "1990s"
  if (field === 'bw')     return value === 'yes' ? 'Yes' : 'No';
  if (field === 'writer' || field === 'artist') return `#${value}`; // unresolved id fallback
  return value;                                                    // genre/publisher/format/year/rating
}

let viewLibraryCache = {};      // cache key (see loadBrowse) -> /api/library response
let searchLibraryCache = {};    // query (lowercased) -> /api/library?q=… response (BUG-010:
                                 // server-scoped so issue_count reflects only matching issues,
                                 // not the whole series, unlike the old client-side aggregate filter)

// Folder View (Custom Tabs, view_mode='folder' — CUSTOM_TABS_SPEC.md §9)
let tabViewModes        = {};   // custom tab id (string) -> 'flat' | 'folder', from /nav/config
let tabBasisTypes       = {};   // custom tab id (string) -> 'folder' | 'favorites', from /nav/config
let viewTabPath         = '';   // relative path within the active folder-view tab
let folderViewCache     = {};   // cache key `${tabId}:${path}` -> folder-contents response
let folderViewSearchActive = false;
let folderViewReturnPath   = '';   // path to restore when search is cleared

let viewMode = localStorage.getItem('cv_view_mode') || 'grid';

let currentPage = 1;
let pageSize    = parseInt(localStorage.getItem('cv_page_size') || '50', 10);

// Card size control (library view) — percent labels are presets, not literal
// scale factors; 25% matches the original fixed --card-min (120px) so the
// default look is unchanged until a user picks a different size.
const CARD_SIZE_PX = { '10': '90px', '25': '120px', '50': '160px', '75': '190px', '100': '220px' };
let cardSize = localStorage.getItem('cv_card_size') || '25';

function applyCardSize(size) {
  document.documentElement.style.setProperty('--card-min', CARD_SIZE_PX[size] || CARD_SIZE_PX['25']);
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function initLibrary() {
  try {
    bindSidebarToggle();
    bindSidebarNav();
    bindFilterEvents();
    bindSearchEvents();
    await loadCustomTabsNav();
    // Honour ?surface= so the back button from detail pages returns to the
    // right tab. replace:true (not fromPopstate) so switchSurface() still
    // annotates this very first history entry via replaceState — otherwise
    // bare `/` (or a `/?surface=…` URL reached via a real link, e.g. a
    // fieldview strip) is never distinguishable from "no surface was ever
    // recorded" (BUG-014).
    const st = parseSurfaceState(new URLSearchParams(location.search));
    if (st.status) activeStatus = st.status;
    await switchSurface(st.surface, {
      path: st.path, field: st.field, value: st.value, label: st.label, folder: st.folder,
      keepStatus: !!st.status, replace: true,
    });
  } catch (err) {
    console.error('initLibrary failed:', err);
    const homeStrips = document.getElementById('homeStrips');
    if (homeStrips) {
      homeStrips.innerHTML =
        '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt="">' +
        `<p>Failed to initialise.<br><small>${err.message}</small></p>` +
        '<p><button onclick="loadHome()">Retry</button></p></div>';
    }
  }
}

// ── Surface navigation ────────────────────────────────────────────────────────

// BUG-014 fix — single shared URL<->state parser, used by both initLibrary()
// (first load) and the popstate listener (Back/Forward). Two independent
// parsers drifting out of sync with each other is exactly how BUG-014
// happened, so there is deliberately only one now.
const VALID_SURFACES = ['home', 'series', 'singles', 'all', 'fieldview', 'folderview'];

function parseSurfaceState(params) {
  const reqSurface = params.get('surface') || 'home';
  const known = VALID_SURFACES.includes(reqSurface) || reqSurface.startsWith('tab-');
  return {
    surface: known ? reqSurface : 'home',
    path:    params.get('path')   || '',
    field:   params.get('field')  || '',
    value:   params.get('value')  || '',
    label:   params.get('label')  || '',
    folder:  params.get('folder') || '',
    status:  params.get('status') || '',
  };
}

// v2.6 Item 1 Phase B — app-wide sidebar, shared across index.html/
// series.html/issue.html (one shared script, see the DOMContentLoaded
// dispatch below). Delegated (rather than bound per-button) so the
// Libraries items injected later by loadCustomTabsNav() work without a
// second bind pass.
function bindSidebarToggle() {
  const btn = document.getElementById('sidebarToggleBtn');
  if (!btn) return;
  document.body.classList.toggle('sidebar-collapsed', localStorage.getItem('cv_sidebar_collapsed') === '1');
  btn.addEventListener('click', () => {
    const collapsed = document.body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('cv_sidebar_collapsed', collapsed ? '1' : '0');
  });
}

// Only index.html (data-page="library") runs the SPA surface-switching
// machinery — series.html/issue.html aren't part of it, so a sidebar click
// there is a real page navigation back to the library page.
function bindSidebarNav() {
  const sidebar = document.getElementById('appSidebar');
  if (!sidebar) return;
  const onLibraryPage = document.body.dataset.page === 'library';

  sidebar.addEventListener('click', (e) => {
    const surfaceBtn = e.target.closest('[data-surface]');
    if (surfaceBtn) {
      if (onLibraryPage) switchSurface(surfaceBtn.dataset.surface);
      else location.href = `/?surface=${encodeURIComponent(surfaceBtn.dataset.surface)}`;
      return;
    }
    const tabBtn = e.target.closest('[data-tab-surface]');
    if (tabBtn) {
      if (onLibraryPage) switchSurface(tabBtn.dataset.tabSurface);
      else location.href = `/?surface=${encodeURIComponent(tabBtn.dataset.tabSurface)}`;
      return;
    }
    const statusBtn = e.target.closest('[data-quick-status]');
    if (statusBtn) {
      const status = statusBtn.dataset.quickStatus;
      if (onLibraryPage) {
        activeStatus = status;
        switchSurface('all', { keepStatus: true });
      } else {
        location.href = `/?surface=all&status=${encodeURIComponent(status)}`;
      }
    }
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
// surfaced in the sidebar's "Libraries" section (v2.6 Item 1 Phase B UI
// copy — CUSTOM_TABS_SPEC.md's own "Custom Tabs" terminology is unchanged
// internally), in created_at order. Runs on all three pages (library,
// series, issue) so the Libraries list is always populated. Expanded state
// is plain text, no marker — confirmed against the live Design canvas, not
// just the (slightly behind) handoff files. Collapsed rail shows a single-
// letter badge instead, "#" for a name starting with a digit.
function libraryBadgeChar(name) {
  const ch = (name || '').trim().charAt(0);
  return /[0-9]/.test(ch) ? '#' : (ch ? ch.toUpperCase() : '?');
}

async function loadCustomTabsNav() {
  try {
    const nav = await apiFetch('/nav/config');
    const container = document.getElementById('sidebarLibraries');
    if (!container) return;
    (nav.custom_tabs || []).forEach((tab) => {
      const btn = el('button', 'app-sidebar-item');
      btn.dataset.tabSurface = `tab-${tab.id}`;
      btn.title = tab.name;
      btn.appendChild(el('span', 'app-sidebar-lib-badge', libraryBadgeChar(tab.name)));
      btn.appendChild(el('span', 'app-sidebar-item-label', tab.name));
      container.appendChild(btn);
      tabViewModes[String(tab.id)] = tab.view_mode || 'flat';
      tabBasisTypes[String(tab.id)] = tab.basis_type || 'folder';
    });
    sizeSidebarToContent();
  } catch (_) {
    // Sidebar still works without a Libraries list if this fails; not fatal.
  }
}

// Expanded sidebar width fits its widest row (longest Libraries name
// included) instead of a fixed guess. Measured once after Libraries loads,
// synchronously (no await in between reads/writes) so toggling
// sidebar-collapsed off and back on to force labels visible for the
// measurement never actually paints — no flash. Clamped so one absurdly
// long custom-tab name can't blow the sidebar out to an unreasonable width.
function sizeSidebarToContent() {
  const sidebar = document.getElementById('appSidebar');
  if (!sidebar) return;
  const wasCollapsed = document.body.classList.contains('sidebar-collapsed');
  if (wasCollapsed) document.body.classList.remove('sidebar-collapsed');
  const prevInlineWidth = sidebar.style.width;
  sidebar.style.width = 'max-content';
  const measured = sidebar.getBoundingClientRect().width;
  sidebar.style.width = prevInlineWidth;
  if (wasCollapsed) document.body.classList.add('sidebar-collapsed');
  const clamped = Math.min(Math.max(Math.ceil(measured), 140), 320);
  document.documentElement.style.setProperty('--sidebar-w', clamped + 'px');
}

function isFolderViewTab(surface) {
  return surface.startsWith('tab-') && tabViewModes[surface.slice(4)] === 'folder';
}

function isFavoritesTab(surface) {
  return surface.startsWith('tab-') && tabBasisTypes[surface.slice(4)] === 'favorites';
}

// Menu bar controls (sort/rated/favourites) act on whichever surface is
// active — Flat View re-renders the cover grid, Folder View re-fetches/
// re-filters the current folder level (MENU_BAR_SPEC.md §3).
function renderActiveSurface() {
  if (isFolderViewTab(activeSurface)) {
    renderFolderView(activeSurface.slice(4), viewTabPath);
  } else {
    renderBrowse();
  }
}

// MENU_BAR_SPEC.md §2.1 — "# of Pages" is suppressed on surfaces showing
// aggregate cards: Series/Singles (page_count there is just the cover
// issue's page count, not series-wide) and all of Folder View.
function updateSortPagesOption(surface) {
  const opt = document.getElementById('sortPagesOpt');
  if (!opt) return;
  const suppress = surface === 'series' || surface === 'singles' || isFolderViewTab(surface);
  opt.hidden = suppress;
  opt.disabled = suppress;
  if (suppress && activeSort === 'pages') {
    activeSort = 'alpha';
    const sel = document.getElementById('sortSelect');
    if (sel) sel.value = 'alpha';
  }
}

// Search copy unified with the All tab — Home's search bar searches the same
// flat library All does (see redirectHomeSearchToAll()), so it carries the
// same label. Surfaces not listed here (fieldview/folderview, custom tabs)
// keep the generic placeholder — out of this backlog item's scope.
const SEARCH_PLACEHOLDERS = { home: 'Search All', all: 'Search All', singles: 'Search Singles', series: 'Search Series' };

function updateSearchPlaceholder(surface) {
  const input = document.getElementById('searchInput');
  if (input) input.placeholder = SEARCH_PLACEHOLDERS[surface] || 'Search…';
}

// BUG-014 fix — builds the `/?surface=…` URL for a given surface + state,
// same convention pushFolderViewUrl() already uses for Folder View.
function buildSurfaceUrl(surface, { path = '', field = '', value = '', label = '', folder = '', status = '' } = {}) {
  let href = `/?surface=${encodeURIComponent(surface)}`;
  if (path)   href += `&path=${encodeURIComponent(path)}`;
  if (field)  href += `&field=${encodeURIComponent(field)}`;
  if (value)  href += `&value=${encodeURIComponent(value)}`;
  if (label)  href += `&label=${encodeURIComponent(label)}`;
  if (folder) href += `&folder=${encodeURIComponent(folder)}`;
  if (status) href += `&status=${encodeURIComponent(status)}`;
  return href;
}

function writeSurfaceUrl(surface, { replace = false, ...urlOpts } = {}) {
  const href = buildSurfaceUrl(surface, urlOpts);
  if (replace) history.replaceState(null, '', href);
  else         history.pushState(null, '', href);
}

async function switchSurface(surface, opts = {}) {
  const {
    fromPopstate = false, path = '', keepStatus = false,
    field = '', value = '', label = '', folder = '', search,
    replace = false,
  } = opts;
  exitSelectionMode();
  activeSurface = surface;
  // Read-status filtering only exists as the sidebar's "jump to All,
  // filtered" shortcut now (v2.6 Item 1 Phase B — no more per-surface
  // status-pill row) — any other way of reaching switchSurface() drops it,
  // so it never lingers invisibly on Series/Singles/a custom tab.
  if (!keepStatus) activeStatus = '';
  const isBrowse  = isBrowseSurface(surface);
  const folderTab = isFolderViewTab(surface);
  // BUG-014 fix — these three are now fully derived from THIS call, never
  // carried over from whatever surface was previously active, so popping
  // back into a fieldview/folderview never renders with stale filter state.
  viewField      = surface === 'fieldview'  ? field  : '';
  viewFieldValue = surface === 'fieldview'  ? value  : '';
  viewFieldLabel = surface === 'fieldview'  ? label  : '';
  viewFolderPath = surface === 'folderview' ? folder : '';

  // Update sidebar active state — primary items, Libraries items, and the
  // Unread/Reading/Read shortcuts (only ever "active" together with the
  // All surface, since that's the only surface they can filter).
  document.querySelectorAll('.app-sidebar-item[data-surface], .app-sidebar-item[data-tab-surface]').forEach(b => {
    const key = b.dataset.surface || b.dataset.tabSurface;
    b.classList.toggle('active', key === surface);
  });
  document.querySelectorAll('[data-quick-status]').forEach(b => {
    b.classList.toggle('active', surface === 'all' && b.dataset.quickStatus === activeStatus);
  });

  // Show/hide major views
  document.getElementById('homeView').hidden   = surface !== 'home';
  document.getElementById('browseView').hidden = !isBrowse || folderTab;
  document.getElementById('folderView').hidden = !folderTab;
  document.getElementById('searchWrap').hidden = !(isBrowse || surface === 'home');
  document.getElementById('menuBar').hidden    = !isBrowse;
  document.getElementById('groupBySelect').hidden = !isBrowse || folderTab;
  document.getElementById('browseFilters').hidden = !isBrowse;
  document.getElementById('browseCount').hidden   = !isBrowse;
  updateSearchPlaceholder(surface);
  updateSortPagesOption(surface);

  if (surface === 'home') {
    // Clear search when switching surface
    const input = document.getElementById('searchInput');
    if (input) { input.value = ''; activeSearch = ''; }
    document.getElementById('searchClear').style.display = 'none';
    if (!fromPopstate) writeSurfaceUrl(surface, { replace });
    await loadHome();
  } else if (folderTab) {
    const input = document.getElementById('searchInput');
    if (input) { input.value = ''; activeSearch = ''; }
    document.getElementById('searchClear').style.display = 'none';
    folderViewSearchActive = false;
    viewTabPath = path;
    const tabId = surface.slice(4);
    if (!fromPopstate) pushFolderViewUrl(surface, path, { replace });
    await renderFolderView(tabId, viewTabPath);
  } else if (isBrowse) {
    const input = document.getElementById('searchInput');
    const q = search || '';
    if (input) input.value = q;
    activeSearch = q;
    document.getElementById('searchClear').style.display = q ? 'block' : 'none';
    if (!fromPopstate) {
      writeSurfaceUrl(surface, {
        field: viewField, value: viewFieldValue, label: viewFieldLabel, folder: viewFolderPath,
        status: activeStatus, replace,
      });
    }
    await loadBrowse();
    // BUG-015 bonus (Tez's call) — cosmetic, one-time-per-switch sync of the
    // Genre dropdown's displayed value when landing on a genre fieldview, so
    // it doesn't just show the placeholder while a genre is actually active.
    // Deliberately NOT touching activeGenre (see hasActiveFilters()/
    // clearAllFilters() comments) and deliberately done only here — once per
    // switchSurface() call, not on every _renderBrowsePage() re-render —
    // so a manual dropdown pick while already on a genre fieldview isn't
    // fought/reverted by a subsequent secondary-filter re-render. Runs after
    // loadBrowse() resolves so genreFilter's <option>s (populated by
    // populateFilterDropdowns(), awaited inside loadBrowse()) already exist.
    const genreSelect = document.getElementById('genreFilter');
    if (genreSelect) {
      const isGenreFieldview = surface === 'fieldview' && viewField === 'genre' && !!viewFieldValue;
      genreSelect.value = isGenreFieldview ? viewFieldValue : activeGenre;
      genreSelect.classList.toggle('active', isGenreFieldview || !!activeGenre);
    }
  }
}

window.addEventListener('popstate', () => {
  const st = parseSurfaceState(new URLSearchParams(location.search));
  if (st.status) activeStatus = st.status;
  switchSurface(st.surface, {
    fromPopstate: true, path: st.path, field: st.field, value: st.value, label: st.label,
    folder: st.folder, keepStatus: !!st.status,
  });
});

// Home's search bar has no list of its own to filter (it shows curated
// strips) — typing a query redirects to the All tab with that query already
// applied, since "Search All" is the label Home's search bar shows.
async function redirectHomeSearchToAll(q) {
  await switchSurface('all', { search: q });
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
        '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt=""><p>No content yet.</p></div>';
    }
  } catch (err) {
    clearTimeout(timerId);
    const msg   = err.name === 'AbortError' ? 'Server took too long to respond.' : err.message;
    homeStrips.innerHTML =
      '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt="">' +
      `<p>${msg}<br><button onclick="loadHome()">Retry</button></p></div>`;
  }
}

function stripViewAllHref(strip) {
  // Defaults (basis_type 'builtin') don't get a listing page in this round —
  // HOME_STRIPS_SPEC.md only requires this for admin-added field/folder strips.
  if (strip.basis_type === 'field') {
    // BUG-015: writer/artist strips carry a Person.id value — field_value_label
    // (resolved server-side, backend/routers/home.py) supplies the display name.
    const label = strip.field_value_label ? `&label=${encodeURIComponent(strip.field_value_label)}` : '';
    return `/?surface=fieldview&field=${encodeURIComponent(strip.field_name)}&value=${encodeURIComponent(strip.field_value)}${label}`;
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
  const href = `/issue/${item.id}`;

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
        '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt="">' +
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
          '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt="">' +
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
          '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt="">' +
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
  const years      = [...new Set(allLibrary.map(s => s.year).filter(Boolean))].sort((a,b) => b-a);
  const decades    = [...new Set(years.map(y => Math.floor(y/10)*10))].sort((a,b) => b-a);
  const formats    = [...new Set(allLibrary.flatMap(s => s.formats  || []))].sort();
  const ratings    = [...new Set(allLibrary.flatMap(s => s.age_ratings || []))].sort();

  addOpts('genreFilter',     genres,     null);
  addOpts('yearFilter',      years,      null);
  addOpts('decadeFilter',    decades,    d => `${d}s`);
  addOpts('formatFilter',    formats,    null);
  addOpts('ratingFilter',    ratings,    null);
}

// ── Filter + sort + render ────────────────────────────────────────────────────

function getFilteredLibrary() {
  let pool;
  let needsLocalSearchFilter = false;

  if (activeSurface.startsWith('tab-')) {
    // Custom tab — already folder-scoped server-side; flat like 'all' (no
    // format_group split), per CUSTOM_TABS_SPEC.md 5.3.
    pool = tabLibraryCache[activeSurface.slice(4)] || [];
    needsLocalSearchFilter = true;
  } else if (activeSurface === 'fieldview' || activeSurface === 'folderview') {
    // Home strip "view all" — already field/folder-scoped server-side,
    // flat like 'all', per HOME_STRIPS_SPEC.md 5.2.
    const cacheKey = activeSurface === 'fieldview' ? `field:${viewField}:${viewFieldValue}` : `folder:${viewFolderPath}`;
    pool = viewLibraryCache[cacheKey] || [];
    needsLocalSearchFilter = true;
  } else if (activeSearch) {
    // BUG-010: server-scoped search (GET /library?q=) — issue_count on each
    // series here already reflects only the matching issues, not the whole
    // series, unlike the old client-side aggregate substring filter below.
    pool = searchLibraryCache[activeSearch] || [];
    if (activeSurface === 'series')  pool = pool.filter(s => s.format_group === 'Series');
    if (activeSurface === 'singles') pool = pool.filter(s => s.format_group === 'Singles');
  } else {
    pool = allLibrary;
    if (activeSurface === 'series')  pool = pool.filter(s => s.format_group === 'Series');
    if (activeSurface === 'singles') pool = pool.filter(s => s.format_group === 'Singles');
    // 'all' = both
  }

  // Inline search — only for surfaces not already server-scoped above
  // (custom tabs / fieldview / folderview don't have a search-aware backend
  // call wired up here, so they keep the old aggregate substring filter).
  if (activeSearch && needsLocalSearchFilter) {
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
  if (activeFormat)    pool = pool.filter(s => (s.formats    || []).includes(activeFormat));
  if (activeRating)    pool = pool.filter(s => (s.age_ratings|| []).includes(activeRating));
  if (activeDecade)    pool = pool.filter(s => s.year && Math.floor(s.year/10)*10 === parseInt(activeDecade));
  if (activeYear)      pool = pool.filter(s => String(s.year) === String(activeYear));
  if (activeBW === 'yes') pool = pool.filter(s => s.has_bw);
  if (activeBW === 'no')  pool = pool.filter(s => !s.has_bw);

  // Menu bar — star rating + favourites (MENU_BAR_SPEC.md §2.2, §2.3)
  if (activeStars)     pool = pool.filter(s => String(s.personal_rating || '') === activeStars);
  if (activeFavorites) pool = pool.filter(s => !!s.favorites);

  pool = [...pool].sort(sortComparator);
  return pool;
}

// MENU_BAR_SPEC.md §2.1 — unified sort dropdown + ascend/descend toggle.
// 'recent' has no date_added field in the /library response, so it falls
// through to alpha (same gap as before this item; not new).
const SORT_KEY_FNS = {
  alpha:  s => s.series.replace(/^['"]/, '').toLowerCase(),
  newest: s => s.year || 0,
  recent: s => s.series.replace(/^['"]/, '').toLowerCase(),
  issues: s => s.issue_count || 0,
  pages:  s => s.page_count  || 0,
};

function sortComparator(a, b) {
  const keyFn = SORT_KEY_FNS[activeSort] || SORT_KEY_FNS.alpha;
  const ka = keyFn(a), kb = keyFn(b);
  const cmp = typeof ka === 'string' ? ka.localeCompare(kb) : ka - kb;
  return activeSortDir === 'desc' ? -cmp : cmp;
}

// BUG-015: deliberately blind to viewField/viewFieldValue (fieldview scoping)
// — see clearAllFilters()'s matching comment for why.
function hasActiveFilters() {
  return activeSearch || activeStatus || activeGenre ||
    activeFormat || activeDecade ||
    activeYear || activeRating || activeBW || activeStars || activeFavorites;
}

function clearAllFilters() {
  // BUG-015: deliberately does NOT touch viewField/viewFieldValue. Blanking
  // them here without also changing activeSurface would make
  // getFilteredLibrary() look up viewLibraryCache['field::'] — undefined —
  // and render an empty grid, not an unfiltered one. Leaving a fieldview
  // requires a real navigation; see the fieldview banner's own "Clear
  // filter" link (renderFieldviewBanner()) for that path. This function
  // still correctly clears a secondary dropdown filter (e.g. Format) layered
  // on top of a fieldview while leaving the fieldview scoping itself intact
  // — that's deliberate, not an oversight.
  activeStatus = activeGenre =
    activeFormat = activeDecade = activeYear = activeRating = activeBW = activeSearch = activeStars = '';
  activeFavorites = false;

  ['genreFilter',
   'formatFilter','decadeFilter','yearFilter','ratingFilter','bwFilter','starRatingFilter'].forEach(id => {
    const el_ = document.getElementById(id);
    if (el_) { el_.value = ''; el_.classList.remove('active'); }
  });

  const favBtn = document.getElementById('favFilterBtn');
  if (favBtn) favBtn.classList.remove('active');

  document.querySelectorAll('[data-quick-status]').forEach(b => b.classList.remove('active'));

  const input = document.getElementById('searchInput');
  if (input) { input.value = ''; }
  document.getElementById('searchClear').style.display = 'none';
}

function renderBrowse() {
  currentPage = 1;
  _renderBrowsePage();
}

// BUG-015: generic "you're filtered, here's how to clear it" indicator for
// the fieldview surface (genre tags / writer+artist credit links / admin
// home-strip "view all" links can all land here). Called from
// _renderBrowsePage() (not loadBrowse()) so it stays correct when a
// secondary dropdown filter is layered on top via renderActiveSurface(),
// and gets cleanup-on-navigate-away for free — every surface's render pass
// hides it when activeSurface isn't 'fieldview'. Clear link is a real
// navigation (not a JS state reset) — see series-filter-banner precedent
// (BUG-010) and the reasoning in DECISIONS.md for why that matters here.
function renderFieldviewBanner() {
  const banner = document.getElementById('fieldviewBanner');
  if (!banner) return;
  if (activeSurface !== 'fieldview' || !viewField || !viewFieldValue) {
    banner.hidden = true;
    banner.textContent = '';
    return;
  }
  const fieldLabel   = FIELDVIEW_LABELS[viewField] || viewField;
  const valueDisplay = fieldviewValueDisplay(viewField, viewFieldValue, viewFieldLabel);
  banner.textContent = `${fieldLabel}: ${valueDisplay} `;
  const clearLink = el('a', 'fieldview-banner-clear', 'Clear Filter');
  clearLink.href = '/?surface=all';
  banner.appendChild(clearLink);
  banner.hidden = false;
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
  renderFieldviewBanner();
  clearBtn.style.display = hasActiveFilters() ? 'inline-block' : 'none';

  grid.innerHTML = '';

  if (!filtered.length) {
    // CUSTOM_TABS_SPEC.md §10.6 — a Favourites tab with nothing in it yet
    // reads as broken with the generic filters message; give it its own.
    const emptyMsg = isFavoritesTab(activeSurface)
      ? 'No favourites yet — star some issues to see them here.'
      : 'No comics match these filters.';
    grid.innerHTML =
      '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt="">' +
      `<p>${emptyMsg}</p></div>`;
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
    if (activeGroupBy === 'format')    key = (s.formats && s.formats[0]) || 'Unknown';
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
  // BUG-010: a series card reached via a fieldview filter (e.g. a Writer
  // credit link) or an active search should carry that filter into the
  // series page, so it lists only the matching issues instead of the whole
  // series.
  const fieldQs  = activeSurface === 'fieldview' && viewField && viewFieldValue
    ? `field=${encodeURIComponent(viewField)}&value=${encodeURIComponent(viewFieldValue)}`
    : '';
  const searchQs = !fieldQs && activeSearch ? `q=${encodeURIComponent(activeSearch)}` : '';
  const qs       = [fieldQs, searchQs].filter(Boolean).join('&');
  const suffix   = qs ? `?${qs}` : '';
  const href     = isSingle
    ? `/issue/${s.series_anchor_id}${suffix}`
    : `/series/${s.series_anchor_id}${suffix}`;
  const state    = seriesReadState(s);

  const card = el('a', `cover-card ${state}${s.favorites ? ' is-favorite' : ''}`);
  card.href  = href;

  // Multi-select: Singles cards select their one underlying issue directly;
  // Series-aggregate cards select the whole series (DECISIONS.md 2026-06-23
  // scope correction — previously series-aggregate cards were navigation-only).
  const selectKind = isSingle ? 'issue' : 'series';
  makeSelectable(card, s.series_anchor_id, selectKind);

  const wrap = el('div', 'cover-img-wrap');
  const img  = el('img');
  img.src     = s.cover_path;
  img.alt     = s.series;
  img.loading = 'lazy';
  img.onerror = () => { wrap.innerHTML = '<div class="cover-placeholder">📖</div>'; };
  wrap.appendChild(img);
  wrap.appendChild(buildSelectDot(s.series_anchor_id, selectKind));

  if (s.unread_count > 0 && s.unread_count < s.issue_count) {
    wrap.appendChild(el('span', 'unread-badge', s.unread_count));
  }

  if (s.personal_rating > 0) wrap.appendChild(buildRatingPill(s.personal_rating));

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

  const doSearch = debounce(async q => {
    if (activeSurface === 'home') {
      if (q) redirectHomeSearchToAll(q);
      return;
    }
    if (isFolderViewTab(activeSurface)) {
      const tabId = activeSurface.slice(4);
      if (q) startFolderViewSearch(tabId, q);
      else clearFolderViewSearch(tabId);
      return;
    }
    // BUG-010: scope search server-side (GET /library?q=) so a series with
    // only one matching issue out of many shows issue_count=1, not the whole
    // series — rather than the old client-side aggregate substring match.
    if (q && !searchLibraryCache[q]) {
      try {
        searchLibraryCache[q] = await apiFetch(`/library?q=${encodeURIComponent(q)}`);
      } catch (_) {
        searchLibraryCache[q] = [];
      }
    }
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
    if (isFolderViewTab(activeSurface)) {
      clearFolderViewSearch(activeSurface.slice(4));
      return;
    }
    activeSearch = '';
    input.focus();
    renderBrowse();
  });
}

// ── Filter events ─────────────────────────────────────────────────────────────

function bindFilterEvents() {
  // Status is no longer a per-surface filter-bar control — it's the
  // sidebar's Unread/Reading/Read shortcut now (bindSidebarNav()), which
  // always targets the All surface. Nothing to bind here for it.

  // Dropdown helpers
  const bindSelect = (id, setter) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.addEventListener('change', e => {
      setter(e.target.value);
      e.target.classList.toggle('active', !!e.target.value);
      renderActiveSurface();
    });
  };

  bindSelect('genreFilter',     v => activeGenre     = v);
  bindSelect('formatFilter',    v => activeFormat    = v);
  bindSelect('decadeFilter',    v => activeDecade    = v);
  bindSelect('yearFilter',      v => activeYear      = v);
  bindSelect('ratingFilter',    v => activeRating    = v);
  bindSelect('bwFilter',        v => activeBW        = v);

  document.getElementById('filterClear').addEventListener('click', () => {
    clearAllFilters();
    renderActiveSurface();
  });

  // Menu bar — sort dropdown + ascend/descend toggle (MENU_BAR_SPEC.md §2.1)
  document.getElementById('sortSelect').addEventListener('change', e => {
    activeSort = e.target.value;
    renderActiveSurface();
  });
  document.getElementById('sortDirBtn').addEventListener('click', () => {
    activeSortDir = activeSortDir === 'asc' ? 'desc' : 'asc';
    document.getElementById('sortDirBtn').innerHTML = activeSortDir === 'asc' ? '&#8593;' : '&#8595;';
    renderActiveSurface();
  });

  // Menu bar — star rating filter (MENU_BAR_SPEC.md §2.2). Reset to "all" is
  // the dropdown's own empty "Rated" option, not a same-value reselect — a
  // native <select> doesn't fire 'change' when the value doesn't change, so
  // "second click on active resets" isn't reproducible via this control type.
  document.getElementById('starRatingFilter').addEventListener('change', e => {
    activeStars = e.target.value;
    e.target.classList.toggle('active', !!activeStars);
    renderActiveSurface();
  });

  // Menu bar — favourites filter toggle (MENU_BAR_SPEC.md §2.3)
  document.getElementById('favFilterBtn').addEventListener('click', () => {
    activeFavorites = !activeFavorites;
    document.getElementById('favFilterBtn').classList.toggle('active', activeFavorites);
    renderActiveSurface();
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

  // Card size is set via Admin → Pagination; just apply whatever's stored.
  applyCardSize(cardSize);
}

// ══════════════════════════════════════════════════════════════════════════════
//  FOLDER VIEW (Custom Tabs, view_mode='folder' — CUSTOM_TABS_SPEC.md §9)
// ══════════════════════════════════════════════════════════════════════════════

// URL convention: surface=tab-{id}&path=<relative path>. Folder/file drill-down
// links explicitly pushState (rather than relying on a real <a> navigation the
// way Issue/Series back-links do) since this SPA never does a real page load
// on a surface switch — an explicit pushState per drill-down is needed for
// forward-navigation deep links to work, paired with the popstate listener
// near switchSurface(). This is a deliberate departure from the simpler
// history.back()-only pattern used elsewhere.
function pushFolderViewUrl(surface, path, { replace = false } = {}) {
  const href = `/?surface=${surface}${path ? `&path=${encodeURIComponent(path)}` : ''}`;
  if (replace) history.replaceState(null, '', href);
  else         history.pushState(null, '', href);
}

function goToFolderPath(tabId, newPath) {
  viewTabPath = newPath;
  pushFolderViewUrl(`tab-${tabId}`, newPath);
  renderFolderView(tabId, newPath);
}

async function renderFolderView(tabId, path) {
  const grid = document.getElementById('folderGrid');
  grid.innerHTML = '<div class="loading-state">Loading…</div>';
  document.getElementById('folderMarkAllBtn').hidden = false;
  document.getElementById('folderSearchLabel').hidden = true;

  // Secondary filter dropdowns (genre/format/decade/year/rating/B&W) are
  // global across the whole library — populate them here too, since
  // Folder View can be the first surface a session ever loads.
  if (!allLibrary.length) {
    try { allLibrary = await apiFetch('/library'); } catch (_) { /* dropdowns just stay empty */ }
  }
  if (!filtersReady && allLibrary.length) {
    await populateFilterDropdowns();
    filtersReady = true;
  }

  // Real browser history, not a guessed destination — same pattern as the
  // Series/Issue "← Back" buttons (BUG-014 fix).
  const folderBackBtn = document.getElementById('folderBackBtn');
  folderBackBtn.onclick = (e) => {
    if (window.history.length > 1) {
      e.preventDefault();
      window.history.back();
    }
  };

  const cacheKey = `${tabId}:${path}`;
  let data;
  try {
    if (!folderViewCache[cacheKey]) {
      folderViewCache[cacheKey] = await apiFetch(`/library/tab/${tabId}/folder?path=${encodeURIComponent(path)}`);
    }
    data = folderViewCache[cacheKey];
  } catch (err) {
    grid.innerHTML =
      '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt=""><p>Could not load this folder.</p></div>';
    return;
  }

  // Menu bar filters (MENU_BAR_SPEC.md §2.2, §2.3). Folder cards aren't
  // individually rated, so the star filter only narrows flat file cards;
  // a folder stays visible if any descendant issue is favourited (§2.3),
  // using the has_favorite flag computed server-side.
  let folders = data.folders;
  let files   = data.files;
  if (activeFavorites) {
    folders = folders.filter(f => f.has_favorite);
    files   = files.filter(f => !!f.favorites);
  }
  if (activeStars) {
    files = files.filter(f => String(f.personal_rating || '') === activeStars);
  }
  // Secondary filters (MENU_BAR_SPEC.md / browse-filters) — apply to direct
  // file cards only; folders have no precomputed per-field aggregate to test
  // against, so they stay navigable regardless of these filters.
  if (activeGenre)     files = files.filter(f => (f.genres || []).includes(activeGenre));
  if (activeFormat)    files = files.filter(f => f.format === activeFormat);
  if (activeRating)    files = files.filter(f => f.age_rating === activeRating);
  if (activeDecade)    files = files.filter(f => f.year && Math.floor(f.year / 10) * 10 === parseInt(activeDecade));
  if (activeYear)      files = files.filter(f => String(f.year) === String(activeYear));
  if (activeBW === 'yes') files = files.filter(f => f.black_and_white);
  if (activeBW === 'no')  files = files.filter(f => !f.black_and_white);
  // Sort applies to flat file cards; folder cards stay in the server's
  // alphabetical order — most sort criteria (newest/issues/pages) don't map
  // cleanly onto a folder aggregate the way they do a series aggregate.
  files = [...files].sort(sortComparator);

  grid.innerHTML = '';
  for (const folder of folders) grid.appendChild(buildFolderCard(tabId, path, folder));
  for (const file of files) grid.appendChild(buildFolderFileCard(file));

  const countEl = document.getElementById('browseCount');
  const total = folders.length + files.length;
  countEl.textContent = `${total.toLocaleString()} Item${total === 1 ? '' : 's'}`;
  document.getElementById('filterClear').style.display = hasActiveFilters() ? 'inline-block' : 'none';

  if (!folders.length && !files.length) {
    grid.appendChild(el('div', 'empty-state', 'This folder is empty.'));
  }

  document.getElementById('folderMarkAllBtn').onclick = () => markFolderViewRead(tabId, path);
}

function buildFolderCard(tabId, currentPath, folder) {
  const hasCover = !!folder.cover_path;
  const card = el('div', `folder-card${hasCover ? ' has-cover' : ''}`);
  const nameEl = el('div', 'folder-card-name', folder.name);
  const countEl = el('div', 'folder-card-count', `${folder.issue_count} issue${folder.issue_count === 1 ? '' : 's'}`);

  if (hasCover) {
    const wrap = el('div', 'cover-img-wrap');
    const img = el('img');
    img.src = folder.cover_path;
    img.alt = folder.name;
    img.loading = 'lazy';
    img.onerror = () => { wrap.innerHTML = '<div class="folder-card-icon">📁</div>'; };
    wrap.appendChild(img);
    card.appendChild(wrap);
    const info = el('div', 'folder-card-info');
    info.appendChild(nameEl);
    info.appendChild(countEl);
    card.appendChild(info);
  } else {
    card.appendChild(el('div', 'folder-card-icon', '📁'));
    card.appendChild(nameEl);
    card.appendChild(countEl);
  }

  const newPath = currentPath ? `${currentPath}/${folder.name}` : folder.name;
  card.addEventListener('click', () => goToFolderPath(tabId, newPath));
  return card;
}

// Folder View's flat file card — same shape as the old 2000 AD prog card
// (cover-card + makeSelectable), generalised with non-2000AD-specific labels
// so it works for any custom tab's loose files.
function buildFolderFileCard(issue) {
  const state = issue.read_status === 'read'    ? 'state-read'
              : issue.read_status === 'reading'  ? 'state-part-read'
              : 'state-unread';

  const card = el('a', `cover-card ${state}${issue.missing ? ' missing' : ''}${issue.favorites ? ' is-favorite' : ''}`);
  card.href  = `/issue/${issue.id}`;
  makeSelectable(card, issue.id);

  const wrap = el('div', 'cover-img-wrap');
  const img  = el('img');
  img.src     = issue.cover_path;
  img.alt     = issue.title || issue.series || '';
  img.loading = 'lazy';
  img.onerror = () => { wrap.innerHTML = '<div class="cover-placeholder">📖</div>'; };
  wrap.appendChild(img);
  wrap.appendChild(buildSelectDot(issue.id));

  if (issue.personal_rating > 0) wrap.appendChild(buildRatingPill(issue.personal_rating));

  if (state === 'state-part-read' && issue.page_count > 0) {
    const pct = Math.min(100, Math.round((issue.current_page / issue.page_count) * 100));
    const bar = el('div', 'card-progress-bar');
    bar.style.width = `${pct}%`;
    wrap.appendChild(bar);
  }

  const info = el('div', 'cover-info');
  info.appendChild(el('div', 'cover-title', issue.title || issue.series || `#${issue.number}`));
  if (issue.number)     info.appendChild(el('div', 'cover-count', `#${issue.number}`));
  if (issue.page_count) info.appendChild(el('div', 'cover-count', `${issue.page_count} pages`));
  if (issue.relative_folder) info.appendChild(el('div', 'folder-result-path', issue.relative_folder));

  card.append(wrap, info);
  return card;
}

async function markFolderViewRead(tabId, path) {
  const btn = document.getElementById('folderMarkAllBtn');
  btn.disabled    = true;
  btn.textContent = 'Marking…';
  try {
    await fetch(`${API}/library/tab/${tabId}/folder/mark-read?path=${encodeURIComponent(path)}`, { method: 'POST' });
    delete folderViewCache[`${tabId}:${path}`];
    await renderFolderView(tabId, path);
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Mark all read';
  }
}

// ── Search mode — swaps the folder grid for flat, depth-agnostic results ──────

async function startFolderViewSearch(tabId, q) {
  if (!folderViewSearchActive) {
    folderViewReturnPath = viewTabPath;
    folderViewSearchActive = true;
  }
  document.getElementById('folderMarkAllBtn').hidden = true;
  const searchLabel = document.getElementById('folderSearchLabel');
  searchLabel.textContent = `Search results for "${q}"`;
  searchLabel.hidden = false;

  const resultsGrid = document.getElementById('folderGrid');
  resultsGrid.innerHTML = '<div class="loading-state">Loading…</div>';
  try {
    const data = await apiFetch(`/library/tab/${tabId}/search?q=${encodeURIComponent(q)}`);
    resultsGrid.innerHTML = '';
    if (!data.results.length) {
      resultsGrid.appendChild(el('div', 'empty-state', 'No matches.'));
      return;
    }
    for (const issue of data.results) resultsGrid.appendChild(buildFolderFileCard(issue));
  } catch (err) {
    resultsGrid.innerHTML =
      '<div class="empty-state"><img class="empty-logo" src="/static/images/logo1.png" alt=""><p>Search failed.</p></div>';
  }
}

function clearFolderViewSearch(tabId) {
  folderViewSearchActive = false;
  viewTabPath = folderViewReturnPath;
  renderFolderView(tabId, viewTabPath);
}

// ══════════════════════════════════════════════════════════════════════════════
//  SERIES PAGE
// ══════════════════════════════════════════════════════════════════════════════

async function initSeries() {
  bindSidebarToggle();
  bindSidebarNav();
  loadCustomTabsNav();
  const issueId   = window.location.pathname.replace(/^\/series\//, '');
  const urlParams = new URLSearchParams(location.search);
  // BUG-010: a series reached from a credit/field-filtered context (e.g. a
  // Writer credit link) should only list the issues matching that filter,
  // not the whole series.
  const field     = urlParams.get('field') || '';
  const value     = urlParams.get('value') || '';
  // BUG-010: a series reached from an active inline search hit should also
  // only list the issues that actually matched, same as the field+value case.
  const q         = urlParams.get('q') || '';
  const content   = document.getElementById('seriesContent');

  try {
    const qs   = field && value
      ? `?field=${encodeURIComponent(field)}&value=${encodeURIComponent(value)}`
      : q ? `?q=${encodeURIComponent(q)}` : '';
    const data = await apiFetch(`/series/${issueId}${qs}`);
    document.title = `${data.series} — digib00age`;
    content.innerHTML = '';
    content.appendChild(buildSeriesHeader(data));
    content.appendChild(buildIssueList(data));
  } catch (_) {
    content.innerHTML =
      '<div class="empty-state" style="padding-top:60px">' +
      '<img class="empty-logo" src="/static/images/logo1.png" alt=""><p>Series not found.</p></div>';
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
  // Real browser history, not a guessed destination — see initIssue()'s
  // matching back link for why this replaced the old from-param logic.
  const topRow = el('div', 'series-hero-top');
  const backLink = el('a', 'btn-primary', '← Back');
  backLink.href = '/';
  backLink.addEventListener('click', (e) => {
    if (window.history.length > 1) {
      e.preventDefault();
      window.history.back();
    }
  });
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

  // Genre tags — each links to a filtered list of every issue with that
  // genre (same fieldview plumbing as the Issue detail page's genre tags).
  if (data.genres && data.genres.length) {
    const tags = el('div', 'genre-tags');
    for (const g of data.genres) {
      const link = el('a', 'genre-tag', g);
      link.href = `/?surface=fieldview&field=genre&value=${encodeURIComponent(g)}`;
      tags.appendChild(link);
    }
    hero.appendChild(tags);
  }

  // Issue count
  hero.appendChild(el('p', 'series-stats',
    `${data.issue_count} issue${data.issue_count !== 1 ? 's' : ''}`
  ));

  // BUG-010: scoped (credit/field-filtered or search-matched) view banner,
  // with a way back to the full series.
  if (data.filtered_field || data.filtered_query) {
    const reason = data.filtered_field
      ? `filtered by ${data.filtered_field}`
      : `matching "${data.filtered_query}"`;
    const banner = el('p', 'series-filter-banner',
      `Showing ${data.issue_count} of ${data.total_issue_count} issues — ${reason}. `
    );
    const clearLink = el('a', 'series-filter-clear', 'View full series');
    clearLink.href = window.location.pathname;
    banner.appendChild(clearLink);
    hero.appendChild(banner);
  }

  wrapper.appendChild(hero);
  return wrapper;
}

// ── Issue list — flat by default (Section 20.7) ──────────────────────────────

function buildIssueList(data) {
  const wrapper = el('div', 'issue-list');
  const group   = el('div', 'arc-group');
  for (const issue of data.issues) group.appendChild(buildIssueRow(issue));
  wrapper.appendChild(group);
  return wrapper;
}

function buildIssueRow(issue) {
  const readState = issue.read_status === 'read'    ? 'state-read'
                  : issue.read_status === 'reading' ? 'state-reading' : '';
  const cls = ['issue-row', issue.missing ? 'missing' : '', readState, issue.favorites ? 'is-favorite' : '']
    .filter(Boolean).join(' ');
  const row = el('a', cls);
  row.href  = `/issue/${issue.id}`;
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
  bindSidebarToggle();
  bindSidebarNav();
  loadCustomTabsNav();
  const issueId = window.location.pathname.replace(/^\/issue\//, '');
  const content = document.getElementById('issueContent');

  try {
    const data = await apiFetch(`/issue/${issueId}`);

    const numSuffix = data.number ? ` #${data.number}` : '';
    document.title = `${data.series}${numSuffix} — digib00age`;

    // Back link: real browser history, not a guessed destination — see series
    // header's matching comment for why this replaced the old from-param logic.
    const backLink = document.getElementById('backLink');
    backLink.href        = '/';
    backLink.textContent = '← Back';
    backLink.addEventListener('click', (e) => {
      if (window.history.length > 1) {
        e.preventDefault();
        window.history.back();
      }
    });

    content.innerHTML = '';
    content.appendChild(buildIssueDetail(data));
  } catch (_) {
    content.innerHTML =
      '<div class="empty-state" style="padding-top:60px">' +
      '<img class="empty-logo" src="/static/images/logo1.png" alt=""><p>Issue not found.</p></div>';
  }
}

// ── Issue detail layout ───────────────────────────────────────────────────────

function buildIssueDetail(data) {
  const page = document.createDocumentFragment();

  // Faint cover backdrop (v2.6 Item 1 Phase E) — sits behind everything
  // below via #issueContent's positioning context; the rest of this
  // function's output goes into .issue-content (position:relative) so it
  // stacks above it.
  if (data.cover_path) {
    const backdrop = el('div', 'issue-backdrop');
    const bdImg     = el('img', 'issue-backdrop-img');
    bdImg.src = data.cover_path;
    bdImg.alt = '';
    bdImg.setAttribute('aria-hidden', 'true');
    backdrop.appendChild(bdImg);
    backdrop.appendChild(el('div', 'issue-backdrop-fade'));
    page.appendChild(backdrop);
  }

  const contentWrap = el('div', 'issue-content');

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

  // Genres — each tag links to a filtered list of every issue with that genre
  // (reuses the same fieldview surface plumbing as the Writer/Artist credit links).
  if (data.genres && data.genres.length) {
    const tags = el('div', 'genre-tags');
    for (const g of data.genres) {
      const link = el('a', 'genre-tag', g);
      link.href = `/?surface=fieldview&field=genre&value=${encodeURIComponent(g)}`;
      tags.appendChild(link);
    }
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
        // BUG-015: value is a Person.id, not human-readable — carry the
        // display name along so the fieldview banner can show it.
        link.href = `/?surface=fieldview&field=${fieldName}&value=${person.person_id}` +
          `&label=${encodeURIComponent(person.name)}`;
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
  contentWrap.appendChild(layout);

  // ── Prev / Next navigation ──
  if (data.prev_issue_id || data.next_issue_id) {
    contentWrap.appendChild(buildIssueNav(data));
  }

  page.appendChild(contentWrap);
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
      // Clicking the already-highlighted star clears to Unrated (BUG-009).
      const newRating = data.personal_rating === i ? 0 : i;
      try {
        await fetch('/api/progress/bulk/rate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ issue_ids: [data.id], rating: newRating }),
        });
        data.personal_rating = newRating;
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
