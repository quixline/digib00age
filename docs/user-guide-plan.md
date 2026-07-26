# User Guide Build Plan — digib00age

> **This document is a Claude Code execution plan.** Read it top-to-bottom before starting any stage. Each stage must be completed in order unless noted otherwise. Do not skip ahead — later stages depend on the inventory and shell files produced by earlier ones.

---

## Quick Reference

| Item | Value |
|---|---|
| **Product name** | digib00age (not ComicVault — rebrand in progress; use digib00age everywhere in guide content) |
| **Repo root** | `D:\workshop\comicvault_v2` |
| **Docs folder** | `D:\workshop\comicvault_v2\docs\` |
| **App server** | `http://localhost:9424` (must be live before Stages 1, 4, 5, 6, 8) |
| **Chrome tool** | `mcp__claude-in-chrome__*` — primary navigation tool for live app |
| **Guide URL base** | `/guide` (final structure: `/guide`, `/guide/library`, `/guide/admin`, `/guide/editor`) |
| **Guide files location** | `frontend/guide.html` (plus future sibling pages, e.g. `frontend/guide-library.html`), served via `FileResponse` routes registered in `backend/main.py` — same pattern as `/`, `/admin`, `/editor`. **Not** a `StaticFiles` mount; `backend/static/guide/` does not exist and isn't the plan here. |
| **Admin placeholder** | Already wired — `frontend/admin.html:41` links to `/guide`. Nothing to build in Stage 3 beyond a verification check. |
| **Tone** | Friendly, plain English, not technical. Assume user knows what a media library is. Admin and Editor sections need full detail. Library sections can be brief but complete. |
| **Key constraint** | No external JS libraries for tooltips — vanilla JS only |
| **Rebrand note** | "digib00age" is always lowercase with a zero (0) in place of the o. Spell it exactly this way every time. The rebrand itself already **shipped** 2026-07-13 (see `DECISIONS.md`) — UI-visible-copy only (header logo, page titles, favicon). "ComicVault" stays the internal/codebase/repo/backend name; don't rename anything outside visible UI text. |
| **Static asset paths** | Real paths are `frontend/js/*.js` and `frontend/css/*.css` — there is no `frontend/static/` subfolder. The `/static` URL prefix (used in `<link>`/`<script>` tags) maps to `frontend/` itself via the mount in `main.py`, not to a literal `frontend/static/` directory on disk. |
| **Skills used in this plan** | `discovery`, `ux-copy`, `design-critique` (flat names, project-scoped under `.claude/skills/` — no plugin namespace exists in this repo, so earlier drafts' `design:ux-copy`/`design:design-critique` naming was wrong) |

---

## Stage 1 — Discovery & Feature Inventory

**Goal:** Build a complete map of every page, feature, button, and action in the app before writing a single word of guide content. Nothing gets written without this foundation.

### Skills/Tools
- Invoke `discovery` skill at the start of this stage (`/discovery` or via Skill tool) — project-scoped, `.claude/skills/discovery/SKILL.md`
- `mcp__claude-in-chrome__*` — navigate the live app
- `Read` tool — read frontend HTML and JS source files
- `Read` tool — read all existing docs in `D:\workshop\comicvault_v2\docs\`

### Steps

1. **Invoke the `discovery` skill.** Use it to scope this project: the deliverable is a user guide, the app is digib00age, the constraint is vanilla JS, the architecture extends the existing `/guide` route (see Quick Reference). Let the skill surface any ambiguities before proceeding.

2. **Load Chrome tools.** Load all tools needed in one call:
   ```
   ToolSearch { query: "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__get_page_text", max_results: 6 }
   ```

3. **Navigate every live page** at `http://localhost:9424`. For each page, record:
   - Page name and URL
   - All visible UI sections
   - Every button, icon, dropdown, toggle, input, and action
   - Any state-dependent UI (e.g., selection bar that appears on multi-select, empty states, loading states)
   - Any modals or overlays triggered by those actions

   Pages to visit (navigate each explicitly):
   - `/` — Library index (grid view and list view if toggle exists)
   - `/folder` or folder view if a separate route exists
   - A series page (click into any series)
   - An issue page (click into any issue)
   - `/admin` — Admin panel (expand every section/accordion)
   - Basic editor — open via an issue's edit button
   - Full editor — open via the full editor button/link
   - Selection bar states — select one issue, select multiple issues, note what actions appear

4. **Read frontend source files** for hidden states, dynamic UI, and features not visible on first load. Key files to read:
   - `frontend/index.html` (or equivalent entry point)
   - `frontend/admin.html`
   - `frontend/js/` — read all JS files, looking for: dynamically injected HTML, conditional UI, keyboard shortcuts, context menus, any feature that only shows under certain conditions
   - `frontend/css/` — note CSS custom properties/tokens already in use (`tokens-base.css`, `tokens-dark.css`, `tokens-light.css`, `style.css` — these are reused directly in Stage 3, not redeclared)

5. **Read all existing docs:**
   - `docs/INDEX.md`
   - `docs/SPEC.md`
   - `docs/EDITOR_SPEC.md`
   - `docs/ADMIN_SPEC.md`
   - `docs/CUSTOM_TABS_SPEC.md`
   - `docs/HOME_STRIPS_SPEC.md`
   - `docs/MENU_BAR_SPEC.md`
   - `docs/v2.6/comicvault-changes-v2.6.md` (or whichever version folder is current per INDEX.md)
   - `docs/BUGS.md` (note any known issues that might affect guide content)

6. **Compile the inventory.** Produce `docs/guide-inventory.md` in the format below.

### Deliverables

`docs/guide-inventory.md` — structured as:

```markdown
# digib00age Feature Inventory

## [Page Name] — [URL]
### [Section Name]
- [Element/Action]: [What it does — one sentence]
- [Element/Action]: [What it does — one sentence]
...

## [Next Page]
...
```

Every page, every section, every button. If an element's behaviour is unclear from the live UI, note it with `[UNCLEAR — check source]` and resolve it before Stage 2.

---

## Stage 2 — Tooltip Data List

**Goal:** While the full feature map is fresh in context from Stage 1, write tooltip text for every actionable control. This is a content deliverable, not an implementation task — do not touch any app code here.

### Skills/Tools
- Invoke `ux-copy` skill — it has specific guidance for writing microcopy and tooltip text
- `guide-inventory.md` from Stage 1 as source of truth
- `Write` tool — produce the output file

### Steps

1. **Invoke the `ux-copy` skill.** Use its guidance for writing good tooltip microcopy: action-oriented, max 10 words, no jargon, no "Click to…" unless necessary for clarity.

2. **Work through `guide-inventory.md` page by page.** For every element marked as a button, icon, toggle, dropdown, or interactive control:
   - Write a tooltip string of max 10 words
   - Be specific — "Mark all selected issues as read" is better than "Mark as read"
   - Use sentence case, no trailing period
   - Skip elements that are obviously self-labelled text buttons with no ambiguity (e.g., a "Save" button that saves and nothing else)

3. **Note any element whose purpose you are uncertain about.** Flag it with `[NEEDS VERIFICATION]` — revisit in Stage 8.

4. **Group by page and component.** Keep the same page order as the inventory.

### Deliverables

`docs/tooltip-data.md` — structured as:

```markdown
# Tooltip Data

> Source for Stage 7 implementation. Do not modify without updating Stage 7.

## [Page Name]

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Grid view toggle | `.view-toggle-grid` or `[data-action="grid-view"]` | Switch to grid layout |
| List view toggle | `.view-toggle-list` | Switch to list layout |
| ...etc | | |

## [Next Page]
...
```

`Selector hint` is a best-guess CSS selector or data attribute — Stage 7 will verify and correct these against the actual DOM. The purpose of the column is to give Stage 7 a starting point, not a guaranteed match.

**Do not implement tooltips. Do not touch any app HTML or JS. This stage produces a data file only.**

---

## Stage 3 — Guide Structure & Shell Pages

**Goal:** Create the complete HTML file structure, FastAPI routing, and linked navigation shell before any content is written. The shell should be fully navigable and styled when this stage ends.

### Skills/Tools
- `Read`/`Write`/`Edit` file tools
- `mcp__workspace__bash` — for verifying the server picks up new routes/files
- Chrome tools — verify shell pages load correctly in browser

### Steps

1. **File serving strategy is already decided — extend the existing pattern.** A
   `/guide` route already exists in `backend/main.py` (registered alongside `/`,
   `/admin`, `/editor`), returning `FileResponse(FRONTEND_DIR / "guide.html")`. This
   is **not** a `StaticFiles` mount, and there is no `backend/static/guide/`
   directory — don't create one. Add one sibling `FileResponse` route per new guide
   page, same pattern as the existing routes in that block of `main.py`.

2. **Add the new routes to `main.py`**, next to the existing `/guide` route (around
   line 176). Example:
   ```python
   @app.get("/guide/library", include_in_schema=False)
   async def guide_library_page():
       return FileResponse(str(FRONTEND_DIR / "guide-library.html"))

   @app.get("/guide/admin", include_in_schema=False)
   async def guide_admin_page():
       return FileResponse(str(FRONTEND_DIR / "guide-admin.html"))

   @app.get("/guide/editor", include_in_schema=False)
   async def guide_editor_page():
       return FileResponse(str(FRONTEND_DIR / "guide-editor.html"))
   ```
   No import changes needed — `FileResponse` is already imported in that block.

3. **Create the new HTML files directly in `frontend/`** (not a subfolder — matches
   every other page in the app):
   ```
   frontend/guide.html          (already exists — becomes the guide index)
   frontend/guide-library.html
   frontend/guide-admin.html
   frontend/guide-editor.html
   ```
   Add further split pages only if Stage 1's inventory shows enough content to
   warrant it (e.g., `guide-editor-basic.html` + `guide-editor-full.html`). Make
   that call now based on the inventory, and note it in the Quick Reference update
   at the bottom of this plan.

4. **Read the app's CSS tokens.** Open `frontend/css/tokens-base.css`,
   `tokens-dark.css`, `tokens-light.css`, and `style.css` — these are the actual
   token/style files already linked by `frontend/guide.html`. Note the custom
   properties in use (colours, font family, radius, spacing) so guide content reads
   as part of the same design system.

5. **No new stylesheet needed.** `frontend/guide.html` already links
   `tokens-base.css`, `tokens-dark.css`, `tokens-light.css`, and `style.css`
   directly — reuse those on every new guide page exactly the same way, rather than
   creating a separate `guide.css`. If guide-specific layout (sidebar nav, callout
   boxes, code/monospace spans) needs styles the main stylesheet doesn't have, add
   a small `<style>` block or a `frontend/css/guide.css` addendum — but check
   `style.css` first, since sidebar/nav/callout patterns may already exist there
   for reuse.

6. **Write all shell HTML files**, following `frontend/guide.html`'s existing
   `<head>`/header structure. Each shell must include:
   - `<head>` with correct title, links to the same token/style CSS as `guide.html`
   - Top navigation bar (matching `guide.html`'s existing `site-header`)
   - Sidebar or top-level nav linking to: guide index, library, admin, editor (and
     sub-pages)
   - A `<main>` content area with an `<h1>` and placeholder text: `<!-- content: Stage N -->`
   - Footer (if the main app has one)
   - Mark the current page as active in the nav

7. **Verify the admin button — already wired, no change needed.**
   `frontend/admin.html:41` already links to `/guide`
   (`<a href="/guide" target="_blank" rel="noopener" class="btn-admin-action">User Guide</a>`).
   Confirm this still works once the guide has real nav — don't add a second
   button or change this one unless something about it is actually broken.

8. **Restart or reload the app server** and use Chrome tools to navigate to
   `/guide`, `/guide/library`, `/guide/admin`, `/guide/editor`. Confirm all shell
   pages load, the nav links work between them, and styling looks correct. Fix any
   broken links or CSS issues before Stage 4.

### Deliverables
- `backend/main.py` — updated with new sibling `/guide/*` `FileResponse` routes
- `frontend/guide.html` — updated as the guide index (existing file, content
  replaced)
- `frontend/guide-library.html` — shell
- `frontend/guide-admin.html` — shell
- `frontend/guide-editor.html` — shell (or split into `guide-editor-basic.html` +
  `guide-editor-full.html`)
- No new stylesheet — reuses existing `frontend/css/tokens-*.css` + `style.css`
- `frontend/admin.html` — verified (already wired, no edit expected)
- All pages navigable and styled in the browser

---

## Stage 4 — Write: Library Section

**Goal:** Write the complete library, series, and issue guide pages. Content should be friendly and assume some media-library familiarity, but cover every feature.

### Skills/Tools
- `mcp__claude-in-chrome__*` — navigate each page, read content, take visual reference
- `guide-inventory.md` (Stage 1) — reference for completeness
- `Edit` tool — fill in the shell HTML

### Steps

1. **Navigate the library index** at `http://localhost:9424`. Use `get_page_text` or `read_page` to capture the current page state. Note the layout, the controls, and the exact label text used in the UI (the guide should use the same terminology the app uses).

2. **Write the library index section.** Cover:
   - What the library shows and how it's organised
   - Grid vs. list view toggle (if present) — how to switch and what each looks like
   - Folder view — what it shows and how it differs from the flat library view
   - Search — how to use it, what it searches across
   - Filters — any filter controls, what they filter by
   - Sort options — what sort modes are available
   - Series cards — what information each card shows (cover, title, read progress, etc.)
   - Reading progress indicators — what the visual states mean (unread, in-progress, complete)

3. **Navigate a series page.** Write the series page section:
   - Series metadata display (title, publisher, year, description, etc.)
   - Issue grid within the series
   - Issue card anatomy — what each card shows
   - How to open an issue for reading vs. opening for editing

4. **Navigate an issue page.** Write the issue page section:
   - Issue metadata display
   - Reading status
   - Navigation controls (previous/next issue, back to series)
   - Any action buttons on the issue page

5. **Trigger the selection bar.** Select one issue, then multiple issues. Write the selection bar section:
   - How to enter selection mode
   - How to select/deselect individual items
   - How to select all
   - Every action available in the selection bar: mark read/unread, rate, flag, any bulk actions — one sub-section per action, explaining what it does and any confirmation steps

6. **Add internal anchors** to every sub-topic so the guide's sidebar nav can deep-link to specific sections (e.g., `#search`, `#selection-bar`, `#filters`).

7. **Update the shell HTML** with the complete written content. Remove all placeholder comments.

8. **Check completeness** against `guide-inventory.md`. Every Library-section item in the inventory should be covered. Note any gaps.

### Deliverables
- `backend/static/guide/library.html` — complete with content and internal anchors
- No inventory gaps remaining for Library section

---

## Stage 5 — Write: Admin Section

**Goal:** Write detailed admin guide pages. Detailed enough that a new admin can set up and manage the app from this guide alone without needing to guess what anything does.

### Skills/Tools
- `mcp__claude-in-chrome__*` — navigate admin, expand every panel
- `docs/ADMIN_SPEC.md` — authoritative reference for admin behaviour
- `guide-inventory.md` (Stage 1)
- `Edit` tool

### Steps

1. **Navigate to `/admin`** and expand every accordion, panel, or section. Use `get_page_text` to capture all visible text and labels. Cross-reference with `ADMIN_SPEC.md` for any behaviour not visible in the UI.

2. **Write each admin section.** For every admin panel/group, write:
   - What this section controls (one sentence)
   - Each setting or action — what it does, when you'd use it, any important caveats
   - Any confirmation dialogs or irreversible actions — flag these explicitly with a callout (e.g., a warning box in the HTML using a CSS class like `.callout-warning`)

3. **Sections to cover** (use the inventory and ADMIN_SPEC.md to verify this list is complete — add anything missing):
   - Library management — adding/removing library paths, rescanning
   - Tab / folder configuration — what custom tabs are, how to create/edit/reorder them
   - Scan and import settings — scan behaviour, import options, metadata fetch settings
   - User settings — any per-user preferences available in admin
   - System config options — any server or app configuration exposed via admin UI
   - PWA install button — what it is, how to use it, what "installing" the app means for the user (this was added recently; confirm it's present in the live admin UI before writing about it)
   - Processing Tools section — cover every action in this panel (ADMIN_SPEC.md §11 is authoritative)

4. **Add internal anchors** to every section heading.

5. **Update the shell HTML** with complete content.

6. **Check completeness** against `guide-inventory.md` Admin section. All items covered.

### Deliverables
- `backend/static/guide/admin.html` — complete with detailed content and anchors
- No inventory gaps remaining for Admin section

---

## Stage 6 — Write: Editor Sections

**Goal:** Write detailed basic editor and full editor guide pages. Editors have significant surface area — cover every field and control.

### Skills/Tools
- `mcp__claude-in-chrome__*` — navigate both editors, trigger every control
- `docs/EDITOR_SPEC.md` — authoritative reference for editor behaviour
- `guide-inventory.md` (Stage 1)
- `Edit` tool

### Steps

1. **Open the basic editor** via an issue's edit button. Navigate every field. Use `get_page_text` or `read_page` to capture labels and structure.

2. **Write the basic editor section:**
   - How to access the basic editor
   - Every field available — what it stores, what format it expects (e.g., comma-separated for tags)
   - Save behaviour — when changes are saved, whether there's autosave, confirmation on exit
   - Any validation — what happens if a required field is missing or a value is invalid
   - How to close/cancel without saving

3. **Open the full editor.** Navigate every field, every tab, every panel. Trigger any metadata fetch controls or cover image upload — observe what happens.

4. **Decide whether to split the editor page.** If basic + full editor content together exceeds ~2000 words of body text, split into `editor-basic.html` and `editor-full.html` and update the nav across all guide pages accordingly. If content fits comfortably in one page with clear section headings, keep it as `editor.html`. Document the decision here.

5. **Write the full editor section:**
   - How to access the full editor (from the basic editor, or directly?)
   - All fields — group them by the tab or panel they appear in
   - Additional panels/tabs beyond the basic editor — what each adds
   - Metadata fetch features — what services are queried, how to trigger a fetch, how to accept/reject fetched data
   - Cover image handling — how to upload, replace, or remove a cover image
   - Issue linking — if the full editor supports linking issues in a series or to other records, explain how
   - Save behaviour — same detail as basic editor

6. **Add internal anchors** to every section and sub-section heading.

7. **Update the shell HTML(s)** with complete content.

8. **Check completeness** against `guide-inventory.md` Editor section and `EDITOR_SPEC.md`. All items covered.

### Deliverables
- `backend/static/guide/editor.html` (or `editor-basic.html` + `editor-full.html`) — complete
- Navigation in all other guide pages updated if editor was split
- No inventory gaps remaining for Editor section

---

## Stage 7 — Tooltip Implementation

**Goal:** Build a lightweight vanilla JS tooltip system and wire all tooltips from `tooltip-data.md` onto the correct elements.

### Skills/Tools
- `Read` tool — read existing JS patterns in the app
- `Edit` tool — add tooltip CSS to `guide.css` and/or the app's main stylesheet, add tooltip JS
- `mcp__claude-in-chrome__*` — verify tooltips appear correctly
- `tooltip-data.md` (Stage 2) — source of all tooltip text

### Steps

1. **Read the app's existing JS patterns.** Read files in `frontend/static/js/` to understand:
   - How the app attaches event listeners (addEventListener vs. delegation)
   - Any existing tooltip or title-attribute usage
   - Whether there's an existing utility pattern to follow (e.g., a `ui.js` or `utils.js`)
   - Preferred attribute naming convention (`data-*` attributes in use)

2. **Design the tooltip system.** Vanilla JS, no library. Recommended approach:
   - Add `data-tooltip="..."` attributes to target elements
   - A single JS module creates one tooltip `<div>` in the DOM on first use
   - On `mouseenter` / `focus`: position and show the tooltip
   - On `mouseleave` / `blur`: hide it
   - Tooltip appears above the element by default, flips below if there's no room at the top
   - Delay: ~500ms before showing (prevents flicker on fast mouse passes)
   - No tooltip on touch/tap — skip on mobile

3. **Write the tooltip CSS** and add it to `guide.css` (or the app's main stylesheet if the tooltips will live on non-guide pages too — use the main stylesheet in that case):
   ```css
   .db-tooltip {
     /* position, background, text, border-radius — match app styling */
     /* fade in with a short transition */
   }
   ```

4. **Write the tooltip JS** as a single self-contained module. Place it in `frontend/static/js/tooltip.js` (or `backend/static/guide/tooltip.js` if tooltips are guide-only). The module should:
   - Export or self-initialise on DOMContentLoaded
   - Use event delegation from `document.body` so dynamically added elements also get tooltips
   - Read the `data-tooltip` value from the event target (or its closest ancestor with that attribute)

5. **Add the `data-tooltip` attributes** to the correct elements. Work through `tooltip-data.md` page by page. For each entry:
   - Find the element using the selector hint column as a starting point
   - Verify the selector in the live DOM (use Chrome tools if needed)
   - Add `data-tooltip="[tooltip text]"` to the element in the relevant HTML template or JS-generated HTML
   - Check the element off in `tooltip-data.md` (add a ✓ column or inline note)

6. **Load the tooltip JS** in every page that needs it. Add a `<script>` tag or import, depending on whether the app already uses ES modules.

7. **Test in Chrome.** Navigate to each page and hover over every element that should have a tooltip:
   - Tooltip appears after ~500ms delay
   - Tooltip text matches `tooltip-data.md`
   - Tooltip positions correctly and doesn't overflow the viewport
   - No console errors

8. **Fix any `[NEEDS VERIFICATION]` items** flagged in Stage 2. If a tooltip couldn't be written then, write it now and add it to `tooltip-data.md`.

### Deliverables
- `frontend/static/js/tooltip.js` (or `backend/static/guide/tooltip.js`)
- Tooltip CSS in `guide.css` or main app stylesheet
- All `data-tooltip` attributes wired to elements listed in `tooltip-data.md`
- `tooltip-data.md` updated with verification status for each entry
- All tooltips verified live in Chrome, no console errors

---

## Stage 8 — Review & Polish

**Goal:** End-to-end review before declaring the guide complete. Catch broken links, styling inconsistencies, missing content, and any remaining gaps.

### Skills/Tools
- Optionally invoke `design-critique` skill for a structured final-pass review of the guide's usability and clarity
- `mcp__claude-in-chrome__*` — navigate the complete guide
- `Read`/`Edit` tools — fix any issues found

### Steps

1. **Optionally invoke `design-critique`.** If there's any uncertainty about the guide's usability or clarity, invoke this skill and let it review the guide as a UI surface. Not mandatory — use judgement based on how the content looks.

2. **Navigate the complete guide in Chrome,** clicking every nav link and every in-page anchor:
   - All internal nav links resolve correctly
   - All internal anchors (`#section-name`) scroll to the right place
   - No 404s, no broken images, no missing CSS
   - The guide looks correct on a normal browser window width

3. **Styling consistency check:**
   - Guide pages look visually consistent with the main app (font, colours, spacing)
   - All guide pages look consistent with each other
   - Callout boxes (tips, warnings) render correctly
   - Code/monospace spans render correctly

4. **Content completeness check:**
   - Open `guide-inventory.md` and scan every entry — confirm it is covered somewhere in the guide
   - Check that the product is referred to as **digib00age** (not ComicVault) throughout all guide pages
   - Check that tone is friendly and non-technical throughout

5. **Tooltip completeness check:**
   - Open `tooltip-data.md` — confirm all entries are marked verified
   - Spot-check five tooltips live in Chrome: correct text, correct positioning, no errors

6. **Admin placeholder button check:**
   - Navigate to `/admin` in Chrome
   - Confirm the user guide button is present and links to `/guide`
   - Confirm clicking it opens the guide index page

7. **Fix all issues found.** Do not close this stage with outstanding issues unless they are explicitly noted as deferred (see below).

8. **Append completion notes** to this plan file. For each stage, note: `done`, `done with caveats`, or `deferred — [reason]`. Use the template below.

### Deliverables
- All guide pages fully navigable with correct content
- Tooltips wired and verified
- Admin button wired and verified
- Completion notes appended to this file (Stage 9 below)

---

## Stage 9 — Completion Notes

| Stage | Status | Notes |
|---|---|---|
| Stage 1 — Discovery & Inventory | done with caveats | `docs/guide-inventory.md` produced (2026-07-25/26); its 3 `[UNCLEAR]` items and one outright wrong entry (Folder View's "← Back"/"Mark all read" — removed from the app 2026-07-17, before this pass ran) all resolved during Stage 7/8 (2026-07-26). |
| Stage 2 — Tooltip Data List | done | `docs/tooltip-data.md` produced (101 entries); rewritten during Stage 7 once real selectors were verified — see that stage's notes. |
| Stage 3 — Guide Structure & Shell Pages | done | 6 routes (`/guide`, `/guide/library`, `/guide/admin`, `/guide/editor`, `/guide/editor-basic`, `/guide/editor-full`) added to `backend/main.py`; shells built reusing existing token CSS + `style.css`, plus a small `frontend/css/guide.css` addendum. |
| Stage 4 — Write: Library | done with caveats | Content written and verified 2026-07-26; the Folder View section's two false claims (see Stage 1) were corrected during Stage 8, same day. |
| Stage 5 — Write: Admin | done | ~2,800–3,000 words, every settings category + Processing Tools sub-tool covered, warning callouts on destructive actions. |
| Stage 6 — Write: Editor | done with caveats | Split into hub + Basic + Full pages as planned; Stage 8 added two gaps found during tooltip verification to `guide-editor-full.html`: the fuzzy-credit-match confirm dialog (Basic Editor's guide already had it; Full Editor's didn't) and the undocumented double-click-to-confirm gesture in the ComicVine issue-search step. |
| Stage 7 — Tooltip Implementation | done | `frontend/js/tooltip.js` (delegated, ~500ms delay, flip-below near viewport top) + `.db-tooltip` CSS in `style.css`; wired across every page in `tooltip-data.md`. Almost every original selector guess was wrong and got corrected against the live DOM/source. Manually spot-checked and confirmed by Tez 2026-07-26. |
| Stage 8 — Review & Polish | done | Programmatic link/anchor crawl across all 6 guide pages (0 broken links, 0 missing anchor targets); confirmed no literal "ComicVault" on any guide page; confirmed the Admin "User Guide" button opens `/guide` in a new tab; visual spot-checks via screenshot. `design-critique` skill not invoked — no usability/clarity concerns surfaced during the pass. |

**Deferred items:**
- `docs/meta/build-plan.html` — referenced by `docs/INDEX.md`/`CLAUDE.md` as the place to mark build-plan items done, but the file doesn't exist in `docs/meta/` (only `about-me.md`, `roadmap.html`, `voice-and-style.md`, `working-rules.md` do). Not created as part of this close-out — flagging the doc/reality mismatch rather than guessing at a format for a file that was never actually made.
- Full Editor's 8 viewer/thumb-strip controls (`#feZoomInBtn` etc.) deliberately kept their native `title` instead of `data-tooltip` — see `tooltip-data.md`'s implementation notes for why (disabled-by-default, converting would've been a regression).
- Folder Processing's script `<select>` options have no tooltip — not technically possible for native dropdown options; the info already lives in the admin-card-hint text and the guide.

**Guide URL summary (final structure):**
`/guide`, `/guide/library`, `/guide/admin`, `/guide/editor` (hub), `/guide/editor-basic`, `/guide/editor-full` — 6 routes total, all `FileResponse`-served from `backend/main.py`, same pattern as `/`, `/admin`, `/editor`.

---

*Plan written 2026-07-25. Execute stages in order. Update the Quick Reference table if any file paths or URL structure decisions change during execution.*
