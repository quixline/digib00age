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
  grButton.dataset.tooltip = 'Pastes the last GoodReads scrape into Writer/Penciller/Publisher/Year/Summary (overwrites existing values)';

  grButton.addEventListener('click', async () => {
    const { grScrape } = await chrome.storage.local.get('grScrape');
    if (!grScrape) return;
    applyScrape(grScrape);
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
