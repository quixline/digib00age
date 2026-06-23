# ComicVault — v2.3: Build Queue

> **Status: Active — items being scoped/planned.**
>
> **How to use this document**
> Active build queue for v2.3. Paste into a Claude Code session alongside `SPEC.md`,
> `CUSTOM_TABS_SPEC.md`, and any other relevant spec files for context.

---

## Folder View — folder card images (resolved and built, 2026-06-23)

Resolved 2026-06-23, separate from other v2.3 items below. Full detail lives in
`CUSTOM_TABS_SPEC.md` §9.2 — this entry just tracks it as a v2.3 build item.
Built same day — see `progress.md` "Session — 2026-06-23: v2.3 — Folder card
images built" for the build/verification log.

Folder cards in Folder View get a representative image: a random cached issue
thumbnail from anywhere recursively under that folder, re-randomized on every
request. Reuses the existing thumbnail cache directly — no new pipeline, no
`folder.jpg`/`cover.jpg`/`poster.jpg` file convention, no scanner changes.

**Build notes:**
- Extend the folder-contents query (`GET /api/library/tab/{id}/folder?path=`,
  §9.5) to also return one randomly-selected thumbnail path per subfolder, using
  the same subtree scope as the existing recursive issue count.
- Frontend: `buildFolderCard()` (§9.6) renders the returned thumbnail path same
  as an issue card's cover image; falls back to the plain folder icon when a
  folder has no thumbnail (count = 0).
