## SCOPE: Goodreads-to-Editor Data Capture Extension

Scoped 2026-07-30 (Cowork discovery session). **Built same day** via `/eng-review` —
open questions below resolved with Tez, implemented, and manually verified working.
See `docs/v2.6/progress.md` "GoodReads data capture extension built" and
`docs/DECISIONS.md` for the resolved design calls.

**The actual problem:** Populating Writer, Artist, Publisher, Year, and Summary in
the Full Editor currently means manually visiting goodreads.com, searching,
reading the book page, and re-typing each field by hand. It's slow and invites
transcription mistakes, and today's "Search GoodReads" link in the editor
(`frontend/editor_full.html`) just opens a blank search page — it doesn't even
carry over the Series text.

**Who it's for:** Just you — personal library, personal Chrome profile, a few
lookups a week. Not designing for other digib00age installs or users yet.

**Status quo today:** Click the existing blank GoodReads link → manually search →
manually read the book page → manually type each field into the editor. No
automation at any step.

**Smallest version:**
- GoodReads link in the editor is updated to prefill the GR search box with the
  Series field's current text, instead of opening blank.
- You manually pick the correct result from GR's search results (no fuzzy-match
  automation).
- A Chrome extension icon, clicked on the GR book page, scrapes: Writer, Artist
  (mapped to the editor's Penciller field), Publisher, Year, Summary.
- The extension holds that scraped data (background script + `chrome.storage.local`)
  and, on the ComicVault editor tab, runs a second content script that fills the
  fields directly by DOM id — `fe-writer`, `fe-penciller`, `fe-publisher`,
  `fe-year`, `fe-summary` — either on tab focus or via a small "Paste from GR"
  button the content script injects. No clipboard step, no manual re-typing.
- All of this logic lives inside the extension. Nothing is added to digib00age's
  own codebase — this mirrors how "Search ComicVine" (`EDITOR_SPEC.md` §9) already
  populates fields from an external source, except ComicVine does it server-side
  via a real API and this has to happen client-side since Goodreads has none.
- Extension's target URL (which tab counts as "the editor") is hardcoded to your
  own digib00age instance.

**Deliberately excluded (for now):**
- Cover image extraction.
- ISBN, series, and volume-number scraping.
- Auto-selecting the "correct" GR search result — you still eyeball it.
- Bulk/batch lookups across multiple books in one pass.
- Any resilience against Goodreads changing its page markup — v1 just breaks and
  gets manually patched when that happens.
- Configurable/portable target URL for other digib00age installs — this stays a
  personal, single-instance tool until (if ever) it's bundled as an optional
  companion for the public release.

**Kill signal:** If Goodreads' page structure changes often enough that you're
fixing the scraper more than you're using it, this was the wrong build — either
the selector strategy needs to be more durable (see Open Questions) or the whole
approach isn't worth maintaining.

**Fit check:** On-strategy — direct extension of the existing editor data-capture
workflow (parallel to the ComicVine integration), not a tangent. Public-repo
concerns are already satisfied by keeping all extension logic outside the
digib00age codebase (see `PUBLIC_REPO_PLAN.md` if cross-checking).

**Open questions for eng review:**
- DOM selector strategy on the Goodreads side: raw CSS selectors against the
  rendered page vs. reading GR's embedded schema.org/JSON-LD book markup, if
  Goodreads still ships it — the latter is more durable against the "breaks
  often" kill signal and should be checked first before committing to brittle
  selectors.
- Handoff timing: does the content script fill the editor fields automatically
  the moment that tab regains focus, or only on an explicit "Paste from GR"
  action? Auto-fill risks silently overwriting fields you'd already edited by
  hand; an explicit action is safer but adds a click.
- Field collision behavior: if `fe-writer`/`fe-publisher`/etc. already have values
  when the paste happens (partially-edited file), does it overwrite, skip
  populated fields, or prompt? Needs an explicit rule, not implicit last-write-wins.
- Manifest permissions: scoping `host_permissions` to your specific instance URL
  vs. Goodreads' domain — confirm the narrowest permission set that still lets
  both content scripts run, given this is a personal tool with no review/store
  distribution planned.
