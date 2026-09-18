// digib00age — standalone comic-page reader (Windows browser-popout reader).
// Page nav only — no Scroll mode (dropped 2026-07-29, see docs/DECISIONS.md and
// docs/v2.6/progress.md "Windows reader review"). Loaded standalone by
// reader.html, not alongside app.js — duplicates the small `el()` helper
// rather than sharing it.

(function () {
  'use strict';

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  const ZOOM_MIN = 0.5;
  const ZOOM_MAX = 3;
  const ZOOM_STEP = 0.25;
  const TOOLBAR_HIDE_MS = 3000;
  const ARROW_FLASH_MS = 1100;

  // /reader/{id} — issue.html/app.js's window.open() call and direct
  // navigation for verification both resolve to this same URL shape.
  const issueId = parseInt(location.pathname.split('/').filter(Boolean).pop(), 10);

  const state = {
    issue: null,
    pageUrls: [],
    currentPage: 0,
    zoom: 1,
  };

  let toolbarHideTimer = null;
  let img, frame, zonesEl, pageInfoEl, sliderEl, toolbarTop, toolbarBottom;
  let arrowLeftEl, arrowRightEl;

  async function init() {
    if (!issueId) { showError('No issue specified.'); return; }
    try {
      const [issue, pagesData] = await Promise.all([
        fetch(`/api/issue/${issueId}`).then((r) => {
          if (!r.ok) throw new Error('Issue not found.');
          return r.json();
        }),
        fetch(`/api/issue/${issueId}/pages`).then((r) => {
          if (!r.ok) throw new Error('Could not load pages.');
          return r.json();
        }),
      ]);
      state.issue = issue;
      state.pageUrls = pagesData.pages;
      const maxPage = Math.max(state.pageUrls.length - 1, 0);
      state.currentPage = Math.min(Math.max(issue.current_page || 0, 0), maxPage);

      document.title = issue.number
        ? `${issue.series} #${issue.number} — digib00age`
        : `${issue.series} — digib00age`;

      buildUI();
      showPage(state.currentPage, { skipSave: true });
      scheduleToolbarHide();
      wirePan();
      wireKeyboard();
    } catch (e) {
      showError(e.message || 'Failed to load issue.');
    }
  }

  function showError(msg) {
    const root = document.getElementById('readerRoot');
    root.innerHTML = '';
    const box = el('div', 'reader-error');
    box.appendChild(el('div', 'reader-error-msg', msg));
    const retry = el('button', 'reader-btn reader-btn--wide', 'Retry');
    retry.onclick = () => location.reload();
    box.appendChild(retry);
    root.appendChild(box);
  }

  // ── UI construction ─────────────────────────────────────────────────────

  function buildUI() {
    const root = document.getElementById('readerRoot');
    root.innerHTML = '';

    frame = el('div', 'reader-frame');
    img = el('img', 'reader-img');
    img.draggable = false;
    img.alt = '';
    frame.appendChild(img);
    root.appendChild(frame);

    // Click zones: 25% left / 50% middle / 25% right — same split as the
    // Flutter reader's tap zones (toolbar_overlay.dart).
    zonesEl = el('div', 'reader-zones');
    const zoneLeft = el('div', 'reader-zone reader-zone--left');
    const zoneMiddle = el('div', 'reader-zone reader-zone--middle');
    const zoneRight = el('div', 'reader-zone reader-zone--right');
    zoneLeft.addEventListener('click', () => { leftAction(); flashArrow('left'); });
    zoneRight.addEventListener('click', () => { rightAction(); flashArrow('right'); });
    zoneMiddle.addEventListener('click', toggleToolbar);
    zonesEl.append(zoneLeft, zoneMiddle, zoneRight);
    root.appendChild(zonesEl);

    arrowLeftEl = el('div', 'reader-arrow-hint reader-arrow-hint--left', '‹');
    arrowRightEl = el('div', 'reader-arrow-hint reader-arrow-hint--right', '›');
    root.append(arrowLeftEl, arrowRightEl);

    // Top bar
    toolbarTop = el('div', 'reader-toolbar reader-toolbar--top');
    const closeBtn = el('button', 'reader-btn reader-close-btn', '✕');
    closeBtn.title = 'Close';
    closeBtn.onclick = () => window.close();
    toolbarTop.appendChild(closeBtn);
    const title = state.issue.number
      ? `${state.issue.series} #${state.issue.number}`
      : state.issue.series;
    toolbarTop.appendChild(el('div', 'reader-title', title));
    pageInfoEl = el('div', 'reader-page-info');
    toolbarTop.appendChild(pageInfoEl);
    root.appendChild(toolbarTop);

    // Bottom bar
    toolbarBottom = el('div', 'reader-toolbar reader-toolbar--bottom');

    sliderEl = document.createElement('input');
    sliderEl.type = 'range';
    sliderEl.className = 'reader-slider';
    sliderEl.min = '0';
    sliderEl.max = String(Math.max(state.pageUrls.length - 1, 0));
    sliderEl.addEventListener('input', () => {
      showPage(parseInt(sliderEl.value, 10));
      showToolbar();
    });
    toolbarBottom.appendChild(sliderEl);

    const controls = el('div', 'reader-controls');
    const zoomOutBtn = el('button', 'reader-btn', '−');
    zoomOutBtn.title = 'Zoom out';
    zoomOutBtn.onclick = () => setZoom(state.zoom - ZOOM_STEP);
    const fitBtn = el('button', 'reader-btn reader-btn--wide', 'Fit');
    fitBtn.title = 'Reset zoom';
    fitBtn.onclick = () => setZoom(1);
    const zoomInBtn = el('button', 'reader-btn', '+');
    zoomInBtn.title = 'Zoom in';
    zoomInBtn.onclick = () => setZoom(state.zoom + ZOOM_STEP);
    const fullscreenBtn = el('button', 'reader-btn', '⛶');
    fullscreenBtn.title = 'Fullscreen';
    fullscreenBtn.onclick = toggleFullscreen;
    controls.append(zoomOutBtn, fitBtn, zoomInBtn, fullscreenBtn);
    toolbarBottom.appendChild(controls);
    root.appendChild(toolbarBottom);
  }

  // ── Manga-aware navigation ──────────────────────────────────────────────
  // Right-to-left titles reverse which tap zone / arrow key means "forward",
  // same as Flutter's ComicPageView(reversePages: issue.isManga).

  function goNext() {
    if (state.currentPage >= state.pageUrls.length - 1) {
      maybeShowNextIssuePrompt();
      return;
    }
    showPage(state.currentPage + 1);
  }
  function goPrev() {
    if (state.currentPage <= 0) return;
    showPage(state.currentPage - 1);
  }
  // manga is a ComicInfo-style string ("No"/"Yes"/"YesAndRightToLeft"), not a
  // bool — only the right-to-left value reverses direction, matching
  // Issue.isManga in flutter_app/lib/models/issue.dart ("Yes" alone doesn't).
  function isRightToLeft() { return state.issue.manga === 'YesAndRightToLeft'; }
  function leftAction() { (isRightToLeft() ? goNext : goPrev)(); }
  function rightAction() { (isRightToLeft() ? goPrev : goNext)(); }

  function showPage(n, opts) {
    opts = opts || {};
    n = Math.max(0, Math.min(n, state.pageUrls.length - 1));
    const isLast = n === state.pageUrls.length - 1;
    state.currentPage = n;
    setZoom(1);
    img.src = state.pageUrls[n];
    sliderEl.value = String(n);
    pageInfoEl.textContent = `${n + 1} / ${state.pageUrls.length}`;

    if (!opts.skipSave) {
      postProgress(n, isLast);
    }
  }

  function postProgress(page, isLast) {
    const body = { current_page: page };
    if (isLast) body.status = 'read';
    fetch(`/api/progress/${issueId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch(() => {});
  }

  function maybeShowNextIssuePrompt() {
    const nextId = state.issue.next_issue_id;
    if (!nextId) return;
    fetch(`/api/issue/${nextId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((next) => { if (next) showNextIssueModal(next); })
      .catch(() => {});
  }

  function showNextIssueModal(next) {
    const overlay = el('div', 'reader-modal-overlay');
    const modal = el('div', 'reader-modal');
    modal.appendChild(el('div', 'reader-modal-title', 'Issue complete'));
    const label = next.number ? `Up next: ${next.series} #${next.number}` : `Up next: ${next.series}`;
    modal.appendChild(el('div', 'reader-modal-sub', label));
    const btnRow = el('div', 'reader-modal-actions');
    const stayBtn = el('button', 'reader-btn reader-btn--wide', 'Stay here');
    stayBtn.onclick = () => overlay.remove();
    const nextBtn = el('button', 'reader-btn reader-btn--wide reader-btn--primary', 'Next issue →');
    nextBtn.onclick = () => { location.href = `/reader/${next.id}`; };
    btnRow.append(stayBtn, nextBtn);
    modal.appendChild(btnRow);
    overlay.appendChild(modal);
    document.getElementById('readerRoot').appendChild(overlay);
  }

  // ── Zoom (ported from editor_full.js's Column 3 comic viewer) ──────────

  function setZoom(v) {
    state.zoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, v));
    applyZoom();
  }

  function applyZoom() {
    if (state.zoom === 1) {
      img.style.width = '';
      img.style.maxWidth = '';
      img.style.maxHeight = '';
    } else {
      img.style.width = `${100 * state.zoom}%`;
      img.style.maxWidth = 'none';
      img.style.maxHeight = 'none';
    }
    const zoomed = state.zoom !== 1;
    frame.classList.toggle('reader-frame--zoomed', zoomed);
    // Tap zones would otherwise fight with dragging to pan a zoomed page —
    // disable page-turn-by-click while zoomed; slider/keyboard still work.
    zonesEl.classList.toggle('reader-zones--disabled', zoomed);
  }

  function wirePan() {
    let dragging = false;
    let startX = 0, startY = 0, startLeft = 0, startTop = 0;

    frame.addEventListener('pointerdown', (e) => {
      if (state.zoom === 1 || e.button !== 0) return;
      dragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startLeft = frame.scrollLeft;
      startTop = frame.scrollTop;
      frame.classList.add('reader-frame--dragging');
      frame.setPointerCapture(e.pointerId);
      e.preventDefault();
    });
    frame.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      frame.scrollLeft = startLeft - (e.clientX - startX);
      frame.scrollTop = startTop - (e.clientY - startY);
    });
    const endDrag = (e) => {
      if (!dragging) return;
      dragging = false;
      frame.classList.remove('reader-frame--dragging');
      if (e && frame.hasPointerCapture(e.pointerId)) frame.releasePointerCapture(e.pointerId);
    };
    frame.addEventListener('pointerup', endDrag);
    frame.addEventListener('pointercancel', endDrag);
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
    else document.exitFullscreen();
  }

  // ── Toolbar auto-hide (ported from toolbar_overlay.dart's 3s timer) ─────

  function scheduleToolbarHide() {
    clearTimeout(toolbarHideTimer);
    toolbarHideTimer = setTimeout(hideToolbar, TOOLBAR_HIDE_MS);
  }
  function showToolbar() {
    toolbarTop.classList.remove('reader-toolbar--hidden');
    toolbarBottom.classList.remove('reader-toolbar--hidden');
    scheduleToolbarHide();
  }
  function hideToolbar() {
    toolbarTop.classList.add('reader-toolbar--hidden');
    toolbarBottom.classList.add('reader-toolbar--hidden');
  }
  function toggleToolbar() {
    if (toolbarTop.classList.contains('reader-toolbar--hidden')) showToolbar();
    else { clearTimeout(toolbarHideTimer); hideToolbar(); }
  }

  function flashArrow(side) {
    const arrowEl = side === 'left' ? arrowLeftEl : arrowRightEl;
    arrowEl.classList.add('reader-arrow-hint--visible');
    clearTimeout(arrowEl._hideTimer);
    arrowEl._hideTimer = setTimeout(() => {
      arrowEl.classList.remove('reader-arrow-hint--visible');
    }, ARROW_FLASH_MS);
  }

  // ── Keyboard (desktop parity for the Flutter reader's arrow/Escape handling) ──

  function wireKeyboard() {
    document.addEventListener('keydown', (e) => {
      switch (e.key) {
        case 'ArrowLeft':
        case 'ArrowUp':
          leftAction(); flashArrow('left'); showToolbar();
          break;
        case 'ArrowRight':
        case 'ArrowDown':
        case ' ':
          rightAction(); flashArrow('right'); showToolbar();
          e.preventDefault();
          break;
        case 'Home':
          showPage(0); showToolbar();
          break;
        case 'End':
          showPage(state.pageUrls.length - 1); showToolbar();
          break;
        case 'Escape':
          if (document.fullscreenElement) document.exitFullscreen();
          else window.close();
          break;
        case 'f':
        case 'F':
          toggleFullscreen();
          break;
      }
    });
    // Only reset the auto-hide timer on movement, don't force the toolbar
    // back open — that would fight with a deliberate middle-click hide.
    document.addEventListener('mousemove', () => {
      if (!toolbarTop.classList.contains('reader-toolbar--hidden')) scheduleToolbarHide();
    });
  }

  init();
})();
