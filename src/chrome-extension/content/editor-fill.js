// Persistent content script on http://localhost:9424/editor* — injects a
// "Paste from GR" button next to the existing GoodReads/ComicVine buttons.
// Mirrors editor_full.js's setField(id, value) pattern: these are plain
// <input>/<textarea> elements with no input/change listeners, so a direct
// .value write is picked up correctly the next time collectFormFields() runs.

const FIELD_MAP = {
  writer: 'fe-writer',
  penciller: 'fe-penciller',
  publisher: 'fe-publisher',
  year: 'fe-year',
  language: 'fe-language',
  summary: 'fe-summary',
};

let grButton = null;

function setField(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value;
}

function applyScrape(scrape) {
  // Full overwrite for fields the scrape actually produced a value for; a
  // field the scraper found nothing for is left untouched rather than blanked.
  for (const [scrapeKey, fieldId] of Object.entries(FIELD_MAP)) {
    const value = scrape[scrapeKey];
    if (value) setField(fieldId, value);
  }
}

// setGenres()/selectedGenres live in the page's own (main-world) script scope —
// this (isolated-world) content script has a separate `window` and can't call
// window.setGenres directly. Dispatching a CustomEvent for genre-bridge-main.js
// (a separate "world": "MAIN" content script, see manifest.json) to pick up
// crosses the isolated/main-world boundary without executing inline script —
// injecting a <script> tag was the original approach here but localhost:9424's
// CSP (script-src with no 'unsafe-inline') blocks that outright.
function callPageSetGenres(genres) {
  window.dispatchEvent(new CustomEvent('gr-bridge-set-genres', { detail: genres }));
}

async function applyGenres(genresRaw) {
  if (!genresRaw || !genresRaw.length) {
    console.warn('[GR-bridge] no genresRaw on this scrape (empty, or stored before the Genre feature was added) — nothing to paste. Re-scrape the GoodReads page and try again.');
    return;
  }

  let validGenres;
  try {
    validGenres = await fetch('/api/editor/genres').then((r) => r.json());
  } catch (e) {
    console.warn('[GR-bridge] could not fetch /api/editor/genres, skipping genre paste:', e);
    return;
  }

  // Case-insensitive match only (no synonym table) — always paste the
  // canonical genres.json casing, since digib00age's validation is
  // case-sensitive and a raw GoodReads casing could still fail it.
  const canonicalByLower = new Map(validGenres.map((g) => [g.toLowerCase(), g]));
  const matched = [];
  const skipped = [];
  for (const raw of genresRaw) {
    const canonical = canonicalByLower.get(raw.toLowerCase());
    if (canonical) matched.push(canonical);
    else skipped.push(raw);
  }

  if (skipped.length) {
    console.warn("[GR-bridge] genres skipped (no match in digib00age's list):", skipped.join(', '));
  }

  // Nothing matched — leave the existing genre selection untouched rather
  // than clearing it, same "only overwrite what we actually have" rule as
  // the plain fields above.
  if (!matched.length) return;

  callPageSetGenres([...new Set(matched)]);
}

function updateButton(scrape) {
  if (!grButton) return;
  if (scrape) {
    grButton.disabled = false;
    grButton.textContent = scrape.title ? `Paste from GR: ${scrape.title}` : 'Paste from GR';
  } else {
    grButton.disabled = true;
    grButton.textContent = 'Paste from GR';
  }
}

function injectButton() {
  const toolbar = document.querySelector('.fe-header-actions');
  if (!toolbar) return;

  grButton = document.createElement('button');
  grButton.type = 'button';
  grButton.id = 'gr-bridge-paste-btn';
  grButton.className = 'btn-admin-action btn-admin-action--ghost';
  grButton.disabled = true;
  grButton.textContent = 'Paste from GR';
  grButton.dataset.tooltip = 'Pastes the last GoodReads scrape into Writer / Penciller / Publisher / Year / Language / Summary and matching Genres (overwrites existing values)';

  grButton.addEventListener('click', async () => {
    const { grScrape } = await chrome.storage.local.get('grScrape');
    if (!grScrape) return;
    applyScrape(grScrape);
    await applyGenres(grScrape.genresRaw);
    await chrome.storage.local.remove(['grScrape', 'grScrapeAt']);
    updateButton(null);
  });

  const goodreadsLink = document.getElementById('fe-search-goodreads-link');
  if (goodreadsLink && goodreadsLink.parentNode) {
    goodreadsLink.parentNode.insertBefore(grButton, goodreadsLink.nextSibling);
  } else {
    toolbar.appendChild(grButton);
  }
}

async function init() {
  injectButton();
  const { grScrape } = await chrome.storage.local.get('grScrape');
  updateButton(grScrape || null);

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local' || !('grScrape' in changes)) return;
    updateButton(changes.grScrape.newValue || null);
  });
}

init();
