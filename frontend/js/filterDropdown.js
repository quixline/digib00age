/* ComicVault — filterDropdown.js (v2.6 Item 1 Phase D follow-up)
   Styled open-dropdown panel for the Browse filter bar's <select>
   elements, matching Design's own custom Dropdown component
   (components/library/Dropdown.jsx) — a browser's native <select> popup
   can't be restyled via CSS at all, so this layers a custom trigger+panel
   on top of each real <select>. The <select> stays in the DOM, hidden but
   fully functional, as the single source of truth — app.js is completely
   unmodified, every read/write it already does (change listeners,
   programmatic `.value =`, dynamic option rebuilding via addOpts(),
   `.active`/`.hidden` toggling) keeps working exactly as before. */

(function () {
  function buildDropdown(select) {
    if (select.dataset.fdBound) return;
    select.dataset.fdBound = '1';

    const wrap = document.createElement('div');
    wrap.className = 'fd-wrap';
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = select.className + ' fd-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    wrap.appendChild(trigger);
    select.classList.add('fd-native');

    const panel = document.createElement('div');
    panel.className = 'fd-panel';
    panel.hidden = true;
    panel.setAttribute('role', 'listbox');
    wrap.appendChild(panel);

    function currentLabel() {
      const opt = select.options[select.selectedIndex];
      return opt ? opt.textContent : '';
    }
    function syncLabel() {
      trigger.textContent = currentLabel();
    }
    // app.js toggles `.active`/`.hidden` on the select itself via plain
    // classList/property calls (e.g. clearAllFilters() does `.value = ''`
    // then a separate `.classList.remove('active')`) — rather than guess
    // at call ordering, mirror the select's own real classList/hidden
    // state onto the trigger/wrapper whenever either actually changes.
    function syncFromSelect() {
      syncLabel();
      trigger.classList.toggle('active', select.classList.contains('active'));
      wrap.hidden = select.hidden;
    }

    function closePanel() {
      panel.hidden = true;
      panel.innerHTML = '';
      trigger.setAttribute('aria-expanded', 'false');
      document.removeEventListener('mousedown', onDocMouseDown);
      document.removeEventListener('keydown', onDocKeyDown);
    }

    function onDocMouseDown(e) {
      if (!wrap.contains(e.target)) closePanel();
    }
    function onDocKeyDown(e) {
      if (e.key === 'Escape') closePanel();
    }

    function openPanel() {
      panel.innerHTML = '';
      Array.from(select.options).forEach((opt) => {
        if (opt.hidden) return;
        const row = document.createElement('div');
        row.className = 'fd-opt' +
          (opt.disabled ? ' fd-opt-disabled' : '') +
          (opt.value === select.value ? ' selected' : '');
        row.setAttribute('role', 'option');
        row.textContent = opt.textContent;
        if (!opt.disabled) {
          row.addEventListener('click', () => {
            select.value = opt.value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
            closePanel();
          });
        }
        panel.appendChild(row);
      });
      panel.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      document.addEventListener('mousedown', onDocMouseDown);
      document.addEventListener('keydown', onDocKeyDown);
    }

    trigger.addEventListener('click', () => {
      if (panel.hidden) openPanel(); else closePanel();
    });

    // Programmatic-set sync — app.js sets `.value =` directly in a couple
    // of places (clearAllFilters(), sort-option suppression); a native
    // <select> doesn't fire 'change' for scripted assignment, so the
    // trigger's displayed label needs its own hook into the value setter.
    const nativeDesc = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
    Object.defineProperty(select, 'value', {
      get() { return nativeDesc.get.call(select); },
      set(v) { nativeDesc.set.call(select, v); syncLabel(); },
      configurable: true,
    });

    select.addEventListener('change', syncLabel);

    // `.active` and `.hidden` are both real DOM attribute mutations
    // (classList.add/remove, `.hidden =`), so one MutationObserver
    // reliably catches both regardless of statement ordering inside
    // functions like clearAllFilters().
    const mo = new MutationObserver(syncFromSelect);
    mo.observe(select, { attributes: true, attributeFilter: ['class', 'hidden'] });

    syncFromSelect();
  }

  function init() {
    document.querySelectorAll('#menuBar .filter-select').forEach(buildDropdown);
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Defer a tick past app.js's own DOMContentLoaded handler so dynamic
    // option lists (genreFilter etc., built by addOpts()) and initial
    // filter state are already in place before the panels are built.
    setTimeout(init, 0);
  });
})();
