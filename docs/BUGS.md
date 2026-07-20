# ComicVault — Known Bugs Log

Tracks real, currently-open defects. Separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration
design). Add new entries at the top. **Fixed entries move out of this file** —
see `archive/bugs-fixed-archive.md` (split out 2026-06-29 to keep this file lean;
not version-scoped, since a bug found in one version can get fixed during a later
one).

---

## OPEN

### BUG-032 — HTML/CSS page routes send no `Cache-Control` header; browser can silently serve a stale page on normal navigation

**Found:** 2026-07-20, during manual testing of the CSS theme-token refactor
(`docs/v2.6/code-handoffs/css-theme-token-refactor-plan.md`).

**Where:** `backend/main.py` — the 6 page routes (`/`, `/admin`, `/guide`,
`/editor`, `/series/{id}`, `/issue/{id}`) all use plain `FileResponse`; the
`/static` mount uses plain `StaticFiles`. Neither sets `Cache-Control` —
only `Last-Modified`/`ETag` are sent (FastAPI/Starlette defaults).

**What happened:** After editing all 6 HTML pages (adding new `<link>` tags
for the CSS token split) and `style.css` itself, navigating between pages
(e.g. home → issue detail) sometimes rendered with only the *old* cached
HTML — missing the new stylesheet links entirely, so theme CSS variables
resolved to nothing and the page rendered unstyled/washed-out. Confirmed via
DOM inspection: the live page's `<link>` tags didn't match a fresh
`fetch(..., {cache:'no-store'})` of the same URL, which returned the
correct up-to-date HTML immediately. A hard refresh (bypassing the HTTP
cache) always fixes it.

**Root cause (confirmed):** with no explicit `Cache-Control`, browsers apply
heuristic freshness caching and can reuse a cached response for a same-URL
navigation without revalidating against the server, even though the
underlying file changed. This isn't new behaviour introduced by the CSS
refactor — it's how these routes have always been served — it just wasn't
previously noticeable because edits to these particular HTML files were
rare/small. A session that edits several of these pages substantively (as
the CSS refactor did) makes the staleness obvious.

**Suggested fix (not yet built):** add `Cache-Control: no-cache` to the page
routes and/or the `/static` mount, forcing revalidation via the existing
ETag on every load (still allows 304 Not Modified for genuinely unchanged
content — this is a correctness fix, not a full cache-disable).
