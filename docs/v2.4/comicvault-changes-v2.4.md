# ComicVault — v2.4: Build Plan

> **Status: Active.** 14 items, closed list — agreed in full 2026-06-29, nothing
> added after this point. Items 1–3 are small standalone changes, ready to build.
> Items 4–8 are scope-then-build pairs, one tool at a time (Tez's call: build → test
> → fix before moving to the next, not all-scope-then-all-build). Item 10 (File
> Rename) needs no scoping — already fully designed — and has no dependency on
> Items 4–8/9/11–14, so it can be picked up whenever convenient relative to them.
>
> **How to use this document**
> This is the single ordered build queue for v2.4. Paste into a Claude Code session
> alongside the referenced spec files. Work top to bottom (except Item 10, which can
> move freely — see above). Items are marked ✅ when built and verified. Bugs and
> minor fixes are tracked separately in `BUGS.md` — don't add them here unless they
> block a build item.
>
> **Always reference items from other docs as "v2.4 Item N", never bare "Item N"**
> — see `meta/working-rules.md` "Version-qualified references."
>
> **Scoping convention (settled 2026-06-29):** scope output for Items 4, 5, 6, 7, 8
> goes directly into its permanent home doc (`ADMIN_SPEC.md` for Items 4/6/7/8,
> `SPEC.md` for Item 5's scanner/format implications) — not into a new standalone
> scoping fragment. See `meta/working-rules.md` "Version lifecycle."
>
> **Specs to paste for most sessions:** `ADMIN_SPEC.md`, `SPEC.md`, and
> `admin-spec-section-12-processing-tools.md` as relevant per item.

---

## Item 1 — Admin: restrict all admin access for remote users when Remote Administration is off ✅

**Change.** When "Allow Remote Administration" is unchecked, the Admin cog
link/page should have no function at all for a non-local request — not just the
individual destructive actions already gated by `is_local_request()` (Clear
Database, Restore Database, the folder/file dialogs, etc.). Needs a quick look at
what's currently gated vs. what isn't before Code starts, since "no function
remotely" is broader than today's per-endpoint gating — likely also means the cog
link/page navigation itself, not just specific buttons within it.

---

## Item 2 — Admin: change the default server port to 9424 ✅

**Change.** Resolves the recurring Windows port-exclusion conflict (`archive/
bugs-fixed-archive.md` BUG-004) at the source, rather than relying on the
user-configurable port workaround (`ADMIN_SPEC.md` §7.3, already built) only being
discovered after a failure. 9424 chosen as a port unlikely to fall inside a
WSL2/Hyper-V dynamic-port exclusion range. Once built, `ROADMAP.md`'s "Resolved
(kept for context)" note on this should be tightened to reflect the new default.

---

## Item 3 — Library: replace the empty-results emoji with the logo image ✅

**Change.** On the no-matching-results state ("No comics match these filters."),
replace `<div class="empty-icon">📚</div>` with the image at
`D:\workshop\comicvault_v2\images\logo1.png`. File confirmed present on disk.

**Built beyond this scope, Tez's call:** the same swap was extended to the other
10 emoji-based empty/error states in `app.js` once the pattern was proven
working — see `progress.md` and `DECISIONS.md` for the rationale.

---

## Item 4 — Scope: Favourites as a Custom Tab category

**Scope.** Not a new feature so much as an extension of something already partly
in place (the `favorites` field/badge exist; Custom Tabs exist) — but genuinely
needs scoping, not a default. Custom Tabs today are folder-scoped only (`CustomTab`
model has no basis-type concept, unlike `HomeStrip`'s field/folder split). Needs a
real design decision: is a Favourites tab scoped to a folder *and* filtered to
favourites, or library-wide regardless of folder? Resolves `ROADMAP.md`'s deferred
"Favorites browse surface/tab" item once scoped and built — note for whoever
revisits `ROADMAP.md`/`roadmap.html` at v2.4's close, not touched now per Tez's
explicit hold.

**Spec destination:** `ADMIN_SPEC.md` (Custom Tabs config) + `CUSTOM_TABS_SPEC.md`
(behaviour) — write scope output directly into both, not a new file.

---

## Item 5 — Scope: allow other formats to be added and indexed (CBR, PDF, EPUB)

**Scope.** Flagged going in as the biggest of the four CAPT-area scoping sessions —
touches the scanner, thumbnail generation, and possibly the reader, not just an
isolated Processing Tools utility. Each format is a genuinely separate technical
problem, not one decision: CBR is RAR-based (no built-in Python support — likely
shares a 7-Zip dependency with `ROADMAP.md`'s still-unscoped Processing Folder
automation item, worth raising there rather than reaching for a RAR-specific
library); PDF needs page-rendering for cover extraction (e.g. PyMuPDF); EPUB needs
actual content-extraction (e.g. ebooklib). File Rename Tool (Item 10) is already
format-agnostic by design and needs no changes here.

**Spec destination:** `SPEC.md` (scanner/library behaviour) — write scope output
directly there.

---

## Item 6 — Scope: Convert Files

**Scope.** CAPT's standalone Convert tool — code exists in
`comic_file_editing_toolkit/src/cap_toolkit/`, to be ported following the same
pattern as File Rename Tool's already-completed scoping (local-only gating, in-app
folder-tree picker, audit log).

**Spec destination:** `ADMIN_SPEC.md` §12 (Processing Tools) — write scope output
directly there as a new §12.x, not a new file. (This also gives Item 10's eventual
build session the right shape to follow when `admin-spec-section-12-processing-
tools.md`'s content gets folded into `ADMIN_SPEC.md` proper — see `INDEX.md`.)

---

## Item 7 — Scope: Convert Images

**Scope.** CAPT's standalone Convert Images tool, same porting pattern as Item 6.

**Spec destination:** `ADMIN_SPEC.md` §12 (Processing Tools).

---

## Item 8 — Scope: Flatten Archive

**Scope.** CAPT's standalone Flatten Archive tool, same porting pattern as Item 6.

**Spec destination:** `ADMIN_SPEC.md` §12 (Processing Tools).

---

## Item 9 — Build: Favourites as a Custom Tab category

**Implement.** Depends on Item 4's scoping being complete.

---

## Item 10 — Build: File Rename Tool

**Implement.** Already fully scoped — no dependency on any other v2.4 item, can be
picked up whenever convenient. **Spec:** `ADMIN_SPEC.md` §11.1 ·
`admin-spec-section-12-processing-tools.md` §12.1 — full design there, this item is
a pointer only.

Batch/single-file renaming based on parsed Series/Issue/Title/Year. In-app
folder-tree picker (not a native dialog — works correctly under Remote
Administration), no recursion, per-field File/All checkbox independence, narrow
auto-increment scope (Issue→All only), live preview with no explicit Preview
button, audit log (`rename_log.md`), no undo.

**On build:** fold `admin-spec-section-12-processing-tools.md`'s content into
`ADMIN_SPEC.md` §12 directly as part of this session's doc updates — retires the
standalone file per the resolution plan in `INDEX.md`.

---

## Item 11 — Build: other formats (CBR, PDF, EPUB)

**Implement.** Depends on Item 5's scoping being complete.

---

## Item 12 — Build: Convert Files

**Implement.** Depends on Item 6's scoping being complete.

---

## Item 13 — Build: Convert Images

**Implement.** Depends on Item 7's scoping being complete.

---

## Item 14 — Build: Flatten Archive

**Implement.** Depends on Item 8's scoping being complete.
