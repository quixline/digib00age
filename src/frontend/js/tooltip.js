// digib00age — tooltip.js
// Lightweight vanilla-JS tooltip system (Stage 7, docs/user-guide-plan.md).
// Delegated from document.body so it works for dynamically-added elements
// (cards, admin stat rows, editor queue items, etc.) without re-binding.
// Source text: docs/tooltip-data.md. Attach with data-tooltip="..." on any
// element (or an ancestor of the hovered/focused target).

(function () {
  const SHOW_DELAY_MS = 500;
  const VIEWPORT_MARGIN = 8;

  let tipEl = null;
  let showTimer = null;
  let activeTarget = null;

  function ensureTipEl() {
    if (tipEl) return tipEl;
    tipEl = document.createElement('div');
    tipEl.className = 'db-tooltip';
    tipEl.setAttribute('role', 'tooltip');
    document.body.appendChild(tipEl);
    return tipEl;
  }

  function findTarget(node) {
    return node && node.nodeType === 1 ? node.closest('[data-tooltip]') : null;
  }

  function position(target) {
    const tip = tipEl;
    const targetRect = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();

    let top = targetRect.top - tipRect.height - 8;
    let flipped = false;
    if (top < VIEWPORT_MARGIN) {
      top = targetRect.bottom + 8;
      flipped = true;
    }

    let left = targetRect.left + (targetRect.width - tipRect.width) / 2;
    left = Math.max(VIEWPORT_MARGIN, Math.min(left, window.innerWidth - tipRect.width - VIEWPORT_MARGIN));

    tip.style.top = `${Math.round(top + window.scrollY)}px`;
    tip.style.left = `${Math.round(left + window.scrollX)}px`;
    tip.classList.toggle('db-tooltip--below', flipped);
  }

  function show(target) {
    const text = target.getAttribute('data-tooltip');
    if (!text) return;
    const tip = ensureTipEl();
    tip.textContent = text;
    tip.classList.add('db-tooltip--visible');
    // Two rAFs: the tooltip needs a laid-out size (post-visible) before
    // position() can measure it, and a size change from a previous longer
    // string needs a frame to settle first.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (activeTarget === target) position(target);
    }));
  }

  function hide() {
    clearTimeout(showTimer);
    showTimer = null;
    activeTarget = null;
    if (tipEl) tipEl.classList.remove('db-tooltip--visible');
  }

  function scheduleShow(target) {
    if (activeTarget === target) return;
    clearTimeout(showTimer);
    activeTarget = target;
    showTimer = setTimeout(() => {
      if (activeTarget === target) show(target);
    }, SHOW_DELAY_MS);
  }

  // Touch devices: no hover tooltip — a tap should just activate the control.
  let lastPointerWasTouch = false;
  document.addEventListener('pointerdown', (e) => {
    lastPointerWasTouch = e.pointerType === 'touch';
  }, true);

  document.body.addEventListener('mouseover', (e) => {
    if (lastPointerWasTouch) return;
    const target = findTarget(e.target);
    if (target) scheduleShow(target);
  });

  document.body.addEventListener('mouseout', (e) => {
    const target = findTarget(e.target);
    if (target && !target.contains(e.relatedTarget)) hide();
  });

  document.body.addEventListener('focusin', (e) => {
    const target = findTarget(e.target);
    if (target) scheduleShow(target);
  });

  document.body.addEventListener('focusout', (e) => {
    const target = findTarget(e.target);
    if (target) hide();
  });

  // Any scroll/resize can move the anchor out from under a positioned
  // tooltip — simplest correct behaviour is to just dismiss it.
  window.addEventListener('scroll', hide, true);
  window.addEventListener('resize', hide);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hide(); });
})();
