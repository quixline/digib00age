# ComicVault — v2.4: Build Plan

> **Status: Active.** Item 1 (File Rename Tool) is fully scoped and ready to hand to
> Claude Code. No items built yet.
>
> **How to use this document**
> This is the single ordered build queue for v2.4. Paste into a Claude Code session
> alongside the referenced spec files. Work top to bottom. Items are marked ✅ when
> built and verified. Bugs and minor fixes are tracked separately in `BUGS.md` —
> don't add them here unless they block a build item.
>
> **Specs to paste for most sessions:** `ADMIN_SPEC.md`,
> `admin-spec-section-12-processing-tools.md` as relevant per item.

---

## Item 1 — Admin: Processing Tools — File Rename

**Spec:** `admin-spec-section-12-processing-tools.md` §12.1 — fully scoped
2026-06-27, ready to build. Full design there; this item is a pointer only.

Batch/single-file renaming based on parsed Series/Issue/Title/Year. In-app
folder-tree picker (not a native dialog — works correctly under Remote
Administration), no recursion, per-field File/All checkbox independence, narrow
auto-increment scope (Issue→All only), live preview with no explicit Preview
button, audit log (`rename_log.md`), no undo.

---
