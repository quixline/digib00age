# CSS Theme-Token Refactor — Plan (pending review, not yet executed)

**Status: drafted 2026-07-17, not started.** Saved for review and picked up
in a future session — no CSS or HTML changes have been made yet.

# CSS Refactor Plan: Split Theme Tokens Out of `style.css`

## Context

Recent sessions have focused entirely on the main grid pages. Looking at other
areas (admin, editor, series/issue detail) and the light theme specifically,
there's visible unfinished work — some component styling was only ever
tuned against dark theme and breaks or looks wrong in light. Before doing
that visual cleanup, the standing request is to refactor `frontend/css/style.css`
(currently one 3777-line file, the only stylesheet loaded by all 6 pages) so
theme concerns live in their own files instead of being interleaved with
everything else. This plan is a **first, scoped pass**: pull the theme-variable
system out into 3 files, fix the concrete light-theme gaps that surface along
the way (you can't cleanly separate "light theme values" from code that never
had any), and explicitly defer the larger page/component split (admin.css,
editor.css, grid.css, etc.) to a later pass — "go from there," not now.

This is new territory: no doc currently governs CSS file architecture in this
repo (`docs/SPEC.md` documents theme *behavior* — OS auto-match + Admin
Appearance override — not file structure). Execution should close with a
`docs/DECISIONS.md` entry, since there's no existing precedent to point back to.

## Current state (confirmed by direct read of `frontend/css/style.css`)

Single stylesheet, loaded via one `<link>` at line 9 of `admin.html`,
`editor_full.html`, `guide.html`, `index.html`, `issue.html`, `series.html`.
No inline `<style>` blocks anywhere.

**Theming mechanism**: CSS custom properties. Dark is the default, defined
directly on `:root` (lines 8-121). Light overrides ~16 of those vars via two
near-duplicate blocks (lines 137-156 `@media (prefers-color-scheme: light) {
:root:not([data-theme]) {...} }`, and lines 157-174 `:root[data-theme="light"]
{...}`) that must be hand-kept in sync. `data-theme="light"` is set by a
render-blocking inline `<head>` script reading an Admin Appearance setting;
falls back to OS preference if unset. No `.light-theme`/`.dark-theme` classes
exist — purely attribute + media query.

**Confirmed theme-dependent vars** (redefined with different values in the
light block): `--bg`, `--surface`, `--surface-2`, `--surface-3`,
`--accent-hover`, `--accent-press`, `--accent-tint`, `--accent-text`, `--text`,
`--text-2`, `--text-3`, `--green`, `--danger`, `--border` (14 vars).
`--accent` and `--blue` are also re-declared in the light block but currently
resolve to the *same* hex (`#0A5FFF`) in both themes — kept as explicit
per-theme entries anyway so a future value change stays a one-line edit.
**`--on-accent` and `--favourite` are never touched by the light block at
all** — they're genuinely theme-neutral today and should move to the base
file, not be duplicated into both theme files.

**Section inventory** (file has clear `── Name ──` comment headers
throughout — low risk to split later):
- 1-174: theme variables (dark root + light overrides)
- 176-432: reset/scrollbars, layout, page-bg, site header, sidebar, search
- 432-701: app sidebar, unified menu bar
- 702-759: home strips
- 760-1418: cover grid (legacy card styles 760-1040, "redesigned CoverCard"
  1104-1360, Folder View 1360-1417)
- 1418-1487: search results/loading/empty states
- 1488-1767: series page header/hero, issue list rows
- 1768-2145: issue detail page (backdrop, redesigned cover frame, progress,
  star rating, nav)
- 2146-2701: admin page (stat grid, settings nav, folders, custom tabs, bulk
  toolbar, pagination, toast)
- 2702-2936: basic editor popup / login modal
- 2937-3644: full editor 4-column layout (EDITOR_SPEC §5-9)
- 3645-3777: processing tools panel

**Known gaps, confirmed by direct read:**
1. `.cover-card--redesign` (~1104-1360) and `.issue-cover-link--redesign`
   (~1830-1870) are **documented, intentional exceptions** — SPEC.md §20.20:
   "dark-only, fixed regardless of the site's light/dark theme setting." Fixed
   hex literals on purpose. Must NOT be tokenized or theme-split.
2. `.state-read` / `.state-part-read` (lines 947-1039, confirmed) is an
   **unflagged** gap: `background: #000`, `linear-gradient(..., #000)`,
   `color: #fff`, `rgba(255,255,255,*)` with no theme tokens at all — a
   partially-read card will render as a near-black block with white text
   regardless of site theme, which reads as broken (not "intentionally fixed
   dark" like item 1 — no SPEC citation, comment at line 949 says "same as
   before," suggesting pre-light-theme legacy code nobody revisited). This is
   the concrete example motivating "light theme needs more work."
3. Scattered un-tokenized error/danger-adjacent hex literals despite
   `--danger` already existing (e.g. line 944 `#e05252`, and others reported
   around lines 889, 2364, 2409, 2590, 2910-2913 — re-grep at execution time
   to get exact current line numbers, since line numbers will shift once the
   token blocks above them are removed).

## 1. Target files

- `frontend/css/tokens-base.css` — theme-neutral vars: `--radius*`,
  `--card-min`, `--control-md`, all `--space-*`, `--header-h`, `--sidebar-w`,
  `--pagebg-blur`, `--pagebg-blob-opacity`, all typography vars (`--font-*`,
  `--weight-*`, `--text-2xs`…`--text-3xl`, `--leading-*`, `--tracking-*`),
  all `--shadow-*`, backdrop recipe vars (`--blur-backdrop`,
  `--backdrop-opacity`, `--backdrop-overlay` — comment at 107-109 confirms
  identical in both themes), motion vars (`--ease*`, `--dur*`, `--lift`,
  including the `prefers-reduced-motion` block at 123-130), `--focus-ring`,
  `--scrim`, **`--on-accent`, `--favourite`** (never overridden by light —
  see correction above), and the semantic aliases (lines 42-52:
  `--surface-card`, `--text-primary`, `--state-read`, etc. — these just
  reference other vars, so their *definitions* are theme-neutral even though
  they resolve to theme-dependent colors; cascade doesn't care which file
  defines an alias vs. what it points to, as long as all three token files
  load before `style.css` uses them). Keep the Google Fonts `@import` (line 6)
  at the top of this file too — it's a shared prerequisite, not theme-specific.
- `frontend/css/tokens-dark.css` — the 14 confirmed theme-dependent vars at
  their current dark (default `:root`) values, plus `--accent`/`--blue` for
  symmetry.
- `frontend/css/tokens-light.css` — the same var set at their light values,
  both selector forms (media-query-gated and attribute-gated) consolidated
  into one file, adjacent, with a comment: "keep these two blocks' properties
  identical — same palette, different trigger (OS preference vs. explicit
  Admin Appearance override)."
- `frontend/css/style.css` — stays as the remaining component/layout file.
  All of lines 1-174 (fonts import, `:root`, reduced-motion block, both light
  blocks) get deleted from here once migrated.

## 2. Fixing `.state-read` / `.state-part-read` (lines 947-1039)

Add two new theme-dependent tokens, defined in both `tokens-dark.css` and
`tokens-light.css`:
- `--read-overlay` — replaces the literal `#000` (background, gradient stops).
  Dark: `#000` (unchanged). Light: needs a real value chosen at execution
  time by checking against `--surface`/`--surface-3` so the card still reads
  as "shaded/read" without looking like a rendering bug on a white page —
  don't guess the hex now, pick it visually during implementation.
- `--read-overlay-text` — replaces literal `#fff` / `rgba(255,255,255,0.82)`.
  Since the overlay itself likely stays dark-ish in both themes (this reads
  as a "darkened chip" component, not a mirrored light/dark surface), the
  text may need to stay light-colored in both themes — confirm by eye rather
  than assuming symmetry.

Rewrite lines 950-995 to consume these tokens instead of literals. This
component code stays in `style.css` — only the *values* it references move to
the new token files.

## 3. Scattered danger/error hex literals

Fix in the same pass (not deferred) — these are one-line swaps to
`var(--danger)` or `color-mix(in srgb, var(--danger) X%, ...)`, and skipping
them leaves visible red-on-red/pink contrast bugs in light mode, which is the
same complaint driving this whole refactor. Re-grep for hex literals near
`.needs-review`, toast/error states, and validation styling once the token
blocks above them are removed (line numbers will have shifted) — check each
call site's visual weight before substituting; a hover state that's a darker
red than the base `--danger` needs a `color-mix` toward black, not a flat
swap.

## 4. HTML `<link>` changes (all 6 pages)

Replace the single line (currently line 9 in each):
```html
<link rel="stylesheet" href="/static/css/style.css">
```
with 4 lines, in cascade order (base defines neutral vars → dark sets
defaults → light's media-query/attribute selectors override dark's plain
`:root` → style.css consumes the vars):
```html
<link rel="stylesheet" href="/static/css/tokens-base.css">
<link rel="stylesheet" href="/static/css/tokens-dark.css">
<link rel="stylesheet" href="/static/css/tokens-light.css">
<link rel="stylesheet" href="/static/css/style.css">
```
Apply identically across `admin.html`, `editor_full.html`, `guide.html`,
`index.html`, `issue.html`, `series.html`.

**No JS changes required.** The existing inline `<head>` script only sets
`data-theme="light"` on the root element — it doesn't reference file paths
or use `@import`. Plain `<link>` tags all load and apply before first paint
the same way a single file would (same specificity, same cascade order), so
there's no flash-of-wrong-theme risk introduced by the split.

## 5. `.cover-card--redesign` / `.issue-cover-link--redesign` — untouched

Per SPEC.md §20.20, these stay exactly as fixed-dark hardcoded rules,
relocated as-is (not tokenized, not split) into `style.css` where they
already live — they are not part of the token migration. Keep/add a one-line
comment at each block: "fixed-dark by design, SPEC.md §20.20 — do not
theme-ify."

## 6. Execution order (safe, incremental)

1. Create the 3 new token files empty (header comments only). Add the 4
   `<link>` lines to all 6 HTML pages. `style.css` still has everything —
   verify all 6 pages render identically before touching content (this step
   should be a visual no-op).
2. Move theme-neutral vars (§1) into `tokens-base.css`; delete from
   `style.css`'s `:root`. Reload each page in both light and dark — inert if
   done right, since none of these vars differ by theme; any visible diff
   means something was miscategorized.
3. Move the 14 theme-dependent vars' dark values into `tokens-dark.css`.
   Verify dark theme unchanged across all 6 pages.
4. Move the light override blocks into `tokens-light.css`, consolidated per
   the note in §1. Verify light theme (both via OS preference and via Admin
   Appearance override) unchanged across all 6 pages.
5. Confirm `style.css`'s old `:root` and light blocks are now empty; delete
   the dead selectors.
6. Fix `.state-read`/`.state-part-read` (§2): add the two new tokens to both
   theme files, rewrite the component rules in `style.css`. Visually verify a
   partially-read and a fully-read card in both themes, on the home grid and
   series page — the one real content change in this pass, check it most
   carefully.
7. Fix the danger/error literals (§3), one call site at a time, checking each
   visually (error toast, validation states in admin/editor).
8. Spot-check `.cover-card--redesign`/`.issue-cover-link--redesign` weren't
   accidentally touched — grep both class names in `style.css`, confirm hex
   counts inside those blocks are unchanged from before the refactor.
9. Final diff review: `style.css` should be shorter by roughly the size of
   the old lines 1-174, plus a small net change from the read-state/danger
   literal-to-token rewrites.

## 7. Verification plan (matches this repo's standing bar — manual, not just automated)

Manual visual check across both dark AND light theme (toggle via Admin
Appearance, and separately via OS `prefers-color-scheme` with no override
stored), on all 6 pages:
- `index.html` — cover grid, read/part-read/unread card states, search
- `series.html` — hero, issue list rows
- `issue.html` — backdrop, redesigned cover frame, star rating
- `admin.html` — stat grid, settings nav, folders, bulk toolbar, toast,
  error/danger states
- `editor_full.html` — 4-column layout, basic editor popup, login modal,
  needs-review red outline
- `guide.html` — baseline sanity check (least themed page)

Specifically confirm:
- No flash-of-unstyled/wrong-theme content on load, any page.
- Partially-read and fully-read cards are legible (not a black-on-white
  looking rendering bug) in light theme.
- `.cover-card--redesign` / `.issue-cover-link--redesign` render identically
  in both themes — this is the regression check; they must show zero theme
  variance.
- Error/danger states have visible contrast against their surface in both
  themes.
- DevTools Network tab: exactly 4 stylesheet requests per page, in order
  base → dark → light → style, no 404s.

## 8. Documentation (close-of-session, per CLAUDE.md)

- `docs/DECISIONS.md` — new entry: why the split happened now (light-theme
  gaps surfaced while working other areas beyond the grid pages), why this
  pass is token-only with the component split deferred, and the
  `--read-overlay`/`--read-overlay-text` addition as the concrete motivating
  example.
- Add a deferred item — "split `style.css` further by page/component
  (admin.css, editor.css, grid.css, series/issue.css — boundaries already
  marked by existing comment headers)" — to `docs/ROADMAP.md` or
  `docs/INBOX.md`, not detailed further now.
- `docs/v2.6/progress.md` + `docs/CHANGELOG.md` — standard narrative/one-line
  entries per the normal close-of-session ritual.

### Critical files
- `frontend/css/style.css`
- `frontend/css/tokens-base.css` (new)
- `frontend/css/tokens-dark.css` (new)
- `frontend/css/tokens-light.css` (new)
- `frontend/index.html`, `admin.html`, `editor_full.html`, `guide.html`,
  `issue.html`, `series.html` (each line 9)
- `docs/DECISIONS.md`, `docs/ROADMAP.md` or `docs/INBOX.md`,
  `docs/v2.6/progress.md`, `docs/CHANGELOG.md`
