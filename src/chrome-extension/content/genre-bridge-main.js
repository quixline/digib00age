// Runs in the page's own MAIN world (declared via manifest's "world": "MAIN"),
// unlike editor-fill.js's default isolated world. This is a proper
// extension-provided script file, so it isn't subject to the page's CSP the
// way an inline <script> injected via document.createElement would be —
// that's the whole reason this exists as a separate file instead of the
// inline-script bridge technique (which localhost:9800's CSP blocks).
//
// editor-fill.js (isolated world) can't call window.setGenres directly since
// it has its own separate `window`. It dispatches a CustomEvent instead;
// DOM events cross the isolated/main-world boundary fine without touching CSP.
window.addEventListener('gr-bridge-set-genres', (event) => {
  if (typeof window.setGenres === 'function') {
    window.setGenres(event.detail);
  }
});
