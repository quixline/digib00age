# ComicVault — Decisions Log

Rationale log — *why*, not *what*. Only non-obvious calls go here; routine
implementation choices are covered in `SPEC.md` / `EDITOR_SPEC.md` / the feature
specs and aren't repeated. Newest first.

### docs/ rebrand sweep: current-state docs only, narrative logs and archive/ left as "ComicVault"

**Decided:** 2026-07-29.

**Why:** the 2026-07-28 rebrand close-out deliberately deferred the full
`docs/` text sweep as a separate future pass (see the rebrand entry
below). When that pass came up this session, a blind find-replace turned
out to be the wrong shape: `docs/` mixes two very different kinds of text
under the same "ComicVault" string — living reference docs describing
what the app *is* today, and narrative/rationale logs (`progress.md`,
`DECISIONS.md`, dated "Change Log" sections embedded inside `SPEC.md`/
`ADMIN_SPEC.md`/`EDITOR_SPEC.md`) recording what was *true when written*.
Rewriting the latter would misrepresent history — e.g. a 2026-06-17
changelog entry describing the original Windows Startup shortcut as
`ComicVault.lnk` is a factual record of what that file was actually
named that day; silently changing it to `digib00age.lnk` would directly
contradict `tray_app.py`'s own migration-function comment, which exists
specifically to explain why an old `ComicVault.lnk` needed removing.

**Scope — renamed:** `SPEC.md`, `ADMIN_SPEC.md`, `EDITOR_SPEC.md` (each
minus their own embedded dated Change Log section), `CUSTOM_TABS_SPEC.md`,
`HOME_STRIPS_SPEC.md`, `MENU_BAR_SPEC.md`, `INDEX.md`, `BUGS.md`,
`TESTING.md`, `meta/about-me.md`, `meta/roadmap.html`,
`meta/working-rules.md`. `ROADMAP.md` and `PERFORMANCE.md` were checked
line-by-line and needed no edits — every occurrence in both sat inside a
closed/dated-historical section already.

**Scope — deliberately left as "ComicVault":** `progress.md` (all
versions), `DECISIONS.md` (this file), `CHANGELOG.md`, `INBOX.md`, the
Change Log sections inside the three specs above, and all of
`docs/archive/`. If a future pass wants full historical rewrite (treating
this as pure branding regardless of when the text was written), that's a
distinct, larger decision — not something to infer from this entry.

**One current-state fix fell out of this pass, not just a text swap:**
`SPEC.md` §14 described the Startup shortcut as `ComicVault.lnk` and the
tray menu item as "Start ComicVault at login" — both were actually stale
against the live code (the 2026-07-28 rebrand session had already renamed
both in `tray_app.py`), corrected to match reality rather than swept
along mechanically.

### ComicVault → digib00age rebrand: close-out pass, brand strings only

**Decided:** 2026-07-28.

**Why:** the rebrand had already landed piecemeal and undocumented — new
brand assets (`frontend/images/lockup-dark.png`/`lockup-light.png`,
`favicon.png`, `icon-192.png`/`icon-512.png`) existed, and most frontend
page `<title>` tags and logo references already read "digib00age", along
with `Runner.rc`'s `FileDescription`/`ProductName`. But this had happened
inline during other feature sessions with no tracking, so it was
inconsistent: the tray app, Flutter app, PWA manifest, README, and
`CLAUDE.md` still said "ComicVault", and `tray_app.py` even carried a
comment from a prior session explicitly deciding to *keep* "ComicVault" as
the tray's process/menu name while only its glyph changed (that decision is
superseded by this entry — the rebrand now covers every surface). A full
repo audit (session 2026-07-28, prior to this one) confirmed zero
occurrences of "digib00age" anywhere in code at that point, which is what
surfaced the gap in the first place.

**Scope — what changed:** every user-facing string that displayed
"ComicVault" now reads "digib00age": `frontend/manifest.json`
(name/short_name), `frontend/admin.html` password-recovery help text,
`tray/tray_app.py` (menu items, tooltip, log lines, Start Menu shortcut
filename), `flutter_app/lib/main.dart` (window title), `shell_screen.dart`
(app bar), `settings_screen.dart` (server-URL label, version string),
`flutter_app/pubspec.yaml` (description), `flutter_app/android/app/src/main/AndroidManifest.xml`
(`android:label`, the Android home-screen/app-drawer name), README.md
(title), and this file's own project-context lines in `CLAUDE.md`.

**Scope — deliberately left alone (internal identifiers, not brand text):**
- Repo folder name (`comicvault_v2`), git history, db filename
  (`comicvault_v2.db`), the `CustomTab` model/table name — all pre-existing
  exclusions, unchanged from the original scoping conversation.
- The `comicvault://` custom URI scheme (both Windows registry
  registration in `protocol_handler_service.dart` and the matching Android
  intent-filter `android:scheme="comicvault"`) — this is a functional
  protocol identifier, not a displayed string. Renaming it would require
  also updating whatever web-frontend code generates
  `comicvault://read/{id}` links and re-registering the Windows handler;
  treated as out of scope for this pass, not silently decided either way —
  flagging it back to Tez as a real open question if full-surface
  consistency is wanted later.
- Flutter's Dart class names (`ComicVaultApp`, `_ComicVaultAppState`) and
  the `pubspec.yaml` `name:` package key (`comicvault`) — internal
  identifiers, same bucket as `CustomTab`.
- Android `applicationId`/`namespace` (`com.comicvault.comicvault`) and the
  Kotlin package directory (`android/app/src/main/kotlin/com/comicvault/comicvault/`)
  — deliberately *not* renamed here. Unlike the Windows exe rename below,
  Android treats an `applicationId` change as a different app entirely: any
  existing install on a phone would need to be uninstalled (losing local
  downloads/sync state) rather than updated in place. Flagged back to Tez
  rather than assumed; needs an explicit yes before touching it.
- Every other project doc under `docs/` (SPEC.md, EDITOR_SPEC.md, INDEX.md,
  this file's own title, etc.) still says "ComicVault" in places — Tez only
  confirmed CLAUDE.md and README.md for this pass; a full docs/ sweep is a
  separate, larger job not attempted here.

**Accepted, not avoided — the Windows exe/app-identity rename:**
`flutter_app/windows/CMakeLists.txt` (`project()`, `BINARY_NAME`) and
`Runner.rc` (`CompanyName`, `InternalName`, `LegalCopyright`,
`OriginalFilename`) were renamed from `comicvault`/`com.comicvault` to
`digib00age`/`com.digib00age`. This changes the on-disk name of the built
Windows executable from `comicvault.exe` to `digib00age.exe` on the next
build. Real consequences Tez should know about, not just a code diff:
- Any existing Desktop/Start Menu/taskbar shortcut pointing at the old
  `comicvault.exe` path will break (file not found) after the next build
  replaces it with `digib00age.exe` at a new path — needs manual
  recreation.
- The `comicvault://` protocol handler registered in the Windows registry
  points at the *old* exe path. `protocol_handler_service.dart`'s
  `isRegistered()` already checks whether the registered command contains
  `Platform.resolvedExecutable`, so post-rebuild it will correctly report
  "not registered" rather than silently pointing at a dead path — Tez just
  needs to re-trigger registration (Settings screen's reader-registration
  tile) once after the first rebuild. This is existing, pre-built-in
  behavior, not something added for this change.

**Superseded:** the `tray_app.py` comment (previously citing "SPEC.md
Section 1's 2026-07-07 scope note") that kept the tray process/menu name as
"ComicVault" while only the icon glyph rebranded — that carve-out no longer
applies.

### Installed PWAs don't pick up a manifest name/icon change automatically

**Decided (process gotcha, not a code decision):** 2026-07-28.

**Why:** after the digib00age rebrand, `frontend/manifest.json` and both
icon files were confirmed correct server-side (checked live via
`curl localhost:9424/static/manifest.json`), yet Tez's already-installed
Brave PWA still showed "ComicVault" with the old icon. Chromium-family
browsers snapshot an installed PWA's name/icon at install time for the
OS-level shortcut/taskbar entry and don't re-read it just because the
manifest changed later — this is a browser platform limitation, not a
caching bug in this app's service worker (`sw.js`'s cache-bust hash
correctly rotated, confirmed).

**How to apply:** a manifest name/icon change only shows correctly for
*new* installs going forward. Any already-installed PWA needs a manual
uninstall + reinstall (`brave://apps` or `chrome://apps` → remove →
revisit site → "Install app" again) to pick up the new branding — there
is no code-side fix. Don't spend time trying to force this via SW/cache
changes if it recurs.

### `flutter install` can silently reinstall a stale prebuilt APK instead of rebuilding

**Decided (process gotcha, not a code decision):** 2026-07-28.

**Why:** `flutter install -d <device> --debug` reported "Success" and even
showed "Uninstalling old version... Installing..." — but it had reused a
4-day-old APK already sitting in `build/app/outputs/flutter-apk/` rather
than rebuilding from current source. It does not appear to reliably trigger
a rebuild the way `flutter run` does. This produced a real false-confidence
incident: multiple source changes appeared "deployed and verified" on the
tablet when none of them were actually present in the running app, and it
wasn't caught until the installed package's `lastUpdateTime` (fresh) was
compared against the built APK file's own mtime (stale) via `adb shell
dumpsys package` and a plain file timestamp check.

**How to apply:** for any Flutter tablet deploy going forward, always run
`flutter build apk --debug` explicitly first, confirm the resulting APK's
mtime postdates every source file being tested, and only then
`adb install -r build/app/outputs/flutter-apk/app-debug.apk`. Don't trust
`flutter install`'s own "Success" output as proof a rebuild happened —
verify the artifact's timestamp, not the command's exit status.

### Adaptive icon glyph sizing: trust the on-device check, not the calculation

**Decided:** 2026-07-28 (Android launcher icon fix, same session as above).

**Why:** Three different ways of predicting how big the icon's foreground
glyph would render — a synthetic circle-mask crop, a synthetic
rounded-square-mask crop, and a manual GIMP measurement of the original
flat artwork's margins (which implied ~75% width) — all turned out wrong
once checked on the actual tablet: 75% width visibly overflowed the masked
container on-device despite clearing every synthetic clipping check. The
value that actually worked (57.2% width / 30.8% height) was reached by
directly building, installing, and looking at the real device, twice,
after the calculated approaches failed.

**How to apply:** if this icon (or any Android adaptive icon on this
project) needs resizing again, don't re-derive a target percentage from
first principles or from measuring the source artwork — build, install on
a real device, and look. The gap between "correct by the adaptive-icon
spec" and "correct on this specific launcher" was large enough here that
calculation wasn't a reliable shortcut.

### Service Worker: page navigations go network-first, static assets stay cache-first

**Decided:** 2026-07-28 (BUG-032 fix).

**Why:** `frontend/sw.js` originally used cache-first for everything except
`/api/*`, including the HTML page itself. That's what actually caused
BUG-032's stale-page symptom — not the missing `Cache-Control` header the
bug was originally filed against (see `archive/bugs-fixed-archive.md`
BUG-032 for the full mechanism: an SW update installs/activates/claims
asynchronously, so cache-first can still serve the *previous* HTML shell on
the very navigation that should have picked up an edit). The fix only
changes the strategy for navigation requests
(`event.request.mode === 'navigate'`); CSS/JS/image requests are untouched
and stay cache-first. Deliberately not made global: navigations are cheap,
single requests where "always try network first, fall back to cache only
if offline" costs nothing noticeable and directly fixes the freshness
problem; static assets are numerous, already eventually-consistent via the
existing content-hash `CACHE_NAME` versioning, and don't benefit from the
same treatment enough to justify losing their offline-cache-first
performance. If a similar staleness complaint ever surfaces for CSS/JS
specifically (not just HTML), revisit this split rather than assuming it
still holds.

### Tooltips on disabled buttons need a wrapping element, not the attribute on the button itself

**Decided:** 2026-07-26 (Stage 7, `docs/user-guide-plan.md`).

**Why:** A native HTML `disabled` button doesn't fire `mouseover`/`mouseenter`
in Chromium — confirmed empirically while wiring the tooltip system, not
assumed. A `data-tooltip` attribute placed directly on a button that's
sometimes disabled (Basic Editor's Save button, Full Editor's Process
Queue/Clear Queue/Process All) would silently never show while disabled,
which is exactly when the explanatory tooltip matters most (e.g. "Save is
enabled once a genre, format and age rating are set"). Fixed by wrapping the
button in a `<span data-tooltip="...">` instead, and toggling the wrap's
tooltip text/presence in the same place the disabled state itself gets
toggled (`editorSaveWrap` in `frontend/js/editor_basic.js`; the new
`.fe-queue-action-wrap` CSS class in `frontend/editor_full.html`, added so
the wrapper doesn't break the 3-button equal-width flex layout). Full
Editor's 8 viewer/thumb-strip buttons hit the identical issue but were
deliberately left on their pre-existing native `title` instead of wrapped —
they already worked correctly via `title`, so converting to `data-tooltip`
would have been a net regression (silent while disabled) purely for visual
consistency, not worth the trade. Future tooltip work on any control that's
sometimes `disabled` should check this first rather than re-discovering it.

### User guide extends the existing `/guide` `FileResponse` route, not a new `StaticFiles` mount

**Decided:** 2026-07-26.

**Why:** `docs/user-guide-plan.md` (written 2026-07-25) assumed a greenfield
build — a new `backend/static/guide/` directory mounted via FastAPI's
`StaticFiles`, with fresh multi-page HTML and its own `guide.css`. Investigation
before starting Stage 1 found a `/guide` route already exists in `backend/main.py`
(`FileResponse`-based, the same pattern used by `/`, `/admin`, `/editor`), already
serving a real stub `frontend/guide.html`, already linked from
`frontend/admin.html:41`. Tez chose to extend that existing route/pattern (sibling
routes like `/guide/library`, new HTML files directly in `frontend/`, reusing the
app's existing token CSS with no separate guide stylesheet) rather than build the
plan's parallel structure — it matches how every other page in the app is served,
and avoids maintaining two separate static-serving mechanisms for no functional
gain. `docs/user-guide-plan.md` was corrected in place (Quick Reference table,
Stage 3) so later stages inherit this instead of the original assumption.

### Admin "Open Editor" link opens in the same tab, not a new one

**Decided:** 2026-07-25.

**Why:** The link (`admin.html`, "Open Editor" → `/editor`) originally used
`target="_blank" rel="noopener"`, opening the Full Editor in a new browser
tab. Now that the app runs as an installed PWA, Tez wants everything
contained within that single PWA window rather than spawning bare browser
tabs alongside it — a new tab opened from an installed PWA window opens in
the regular browser chrome, breaking the app-window feel. Removed
`target="_blank"`/`rel="noopener"` so it navigates in place, same as the
wordmark and admin-cog links already do; `editor_full.html` already has both
of those for getting back out, so no other nav changes were needed.

**Follow-up, same day:** the "→ Send to Full Editor" bulk-selection action
(`app.js`) originally used `window.open('/editor', '_blank')` too, for a
different reason — it had to open the tab synchronously with the click (a
popup-blocker rule: `window.open()` calls made after an `await` get
blocked) and then reload that tab once a background API call
(`add-by-issues`) finished adding the selected files. Tez asked whether this
could be brought in line with the same-tab pattern too. Since the point of
the popup workaround was only to have somewhere to reload once the add
finished, removing `window.open()` entirely and just deferring
`window.location.href = '/editor'` until after the `await` resolves works
with no popup-blocker concern (there's no `window.open()` call left to
block) — verified live: selecting a title and clicking "Send to Full
Editor" shows the "Sending files…" toast, then the same tab navigates to
`/editor` once the add completes, with the file present in the working set.
Tradeoff accepted knowingly: the library selection page is no longer usable
in parallel while the add is running (a few seconds for a large selection,
per the original code comment) — the tab is occupied until the navigation
happens, rather than the old flow where the editor tab loaded immediately
and the library tab stayed free. `User Guide` still opens in a new tab —
un-asked, so left as-is.

**Gotcha hit while verifying:** the service worker (`sw.js`,
`comicvault-shell-v1`) does cache-first for "HTML shells" as well as static
assets, and its registration/scope covers the whole origin (`/`) — so once
it's registered from visiting any reader page, it also intercepts `/admin`
even though `admin.js` never calls `register()` itself. A plain reload
wasn't enough to see the fix live; needed `caches.delete()` +
`unregister()` in the page **and** a hard reload (`ctrl+shift+r`) to clear
both the SW's Cache Storage and the browser's separate HTTP cache. Same
class of issue as the caching gotcha noted in the 2026-07-24 Custom Tabs
session — this will bite Tez's own day-to-day PWA usage too after any
future static-file deploy, not just this testing session, since the SW has
no cache-busting/versioning tied to actual content changes
(`CACHE_NAME = 'comicvault-shell-v1'` is static). Not fixed here — out of
scope for this change — but worth a future session if stale-after-update
becomes a recurring annoyance.

### Service worker cache now versions itself from a content hash, not a hardcoded string

**Decided:** 2026-07-25 (same day as the two entries above — the stale-cache
gotcha hit while verifying those made this worth fixing properly rather than
letting it recur on every future deploy).

**Why:** `sw.js` cache-first-serves static assets *and* HTML shells, keyed
under `CACHE_NAME`. That was a hardcoded literal (`'comicvault-shell-v1'`)
that never changed, so the service worker had no way to know any served file
had changed — it kept answering from its original cache indefinitely,
surviving even a hard reload, until someone manually unregistered it via
devtools. This isn't just a testing inconvenience: it affects Tez's actual
installed PWA the same way after every future UI deploy, not just this
session's testing.

**What changed:** `frontend/sw.js`'s `CACHE_NAME` now ends in a placeholder
token (`ASSET_VERSION_TOKEN`) instead of a literal version number.
`backend/main.py`'s `/sw.js` route (already a dedicated FastAPI route rather
than plain `StaticFiles`, needed for root-scope control) now reads the file
and substitutes that token with a SHA-256 hash (first 12 hex chars) of every
file under `frontend/` (relative path + mtime + size), computed fresh on
every request — cheap enough not to bother caching (36 files, ~7ms) for a
single-user home server. Any frontend file changing — not just the files
explicitly listed in `APP_SHELL` — changes the hash, which changes the bytes
`/sw.js` serves, which is exactly what the browser's built-in SW update
check compares to decide whether to install a new worker. The existing
`activate` handler already deleted any cache key that didn't match the
current `CACHE_NAME` (that logic was already correct) — it just never had a
`CACHE_NAME` that actually changed to trigger it.

**Considered and rejected:** manually bumping a version string by hand each
release. Rejected because it depends on human memory every single time
static files change — exactly the failure mode that caused today's
confusion, and this project doesn't tag/version every session (only
`docs/vN.M/` closures get git tags), so a lot of small UI-tweak sessions
like today's would fall through the cracks. A content hash is automatic and
self-correcting with no ongoing discipline required. Considered switching
navigation requests to network-first instead of cache-first (also solves
staleness, arguably more standard for HTML) but that's a bigger behavioral
change to the offline story than the fix actually called for — content
hashing solves the reported problem with a much smaller diff.

**Caught during implementation:** the first draft's explanatory comment in
`sw.js` above the `CACHE_NAME` line literally spelled out the placeholder
token name in prose — `str.replace()` doesn't care about context, so it
also rewrote the comment text into nonsense (`// 7fc4304bffc6 is
substituted server-side...`) alongside the real substitution. Fixed by
picking a token name that only appears once in the file, on the actual code
line.

**Verified live** (two rounds, matching the two backend restarts this
change needed): confirmed via `curl /sw.js` that touching any frontend file
(a scratch single-space append + revert to `style.css`, checked byte-equal
to `HEAD` afterward via `git hash-object` before moving on) changes the
served hash with **no server restart required** — only the Python route
logic itself needs a restart to deploy, not each individual frontend edit
after that. In the browser: cleared the leftover `comicvault-shell-v1`
cache from before this fix existed, did a clean reload (installed
`comicvault-shell-<hash>`), touched a file again, called
`registration.update()` to force the browser's update check, and confirmed
the cache automatically flipped to the new hash with no stuck "waiting"
worker (`skipWaiting()`/`clients.claim()` already in the existing
lifecycle code took effect immediately) and no console errors.

### Custom Tabs: removed the 4-visible-tab cap entirely, not raised

**Decided:** 2026-07-24.

**Why:** The cap (`MAX_VISIBLE_CUSTOM_TABS = 4`, `CUSTOM_TABS_SPEC.md` §3) dated
from the original v2.1 design, when custom tabs rendered as a top tab bar with
genuinely limited horizontal space. The nav moved to a left sidebar in v2.6
(Item 1 Phase B), and the sidebar has scrolled vertically (`overflow-y: auto`
on `.app-sidebar`) since that redesign — the space constraint the cap existed
to protect against no longer applies, so there was no reason to raise the
number instead of removing it. The immediate driver was Genre Library tabs
(§10.9) competing with Favourites/Reading Queue/folder tabs for the same 4
slots, which blocked using more than a couple of genre-grouped libraries at
once — most noticeably on the Flutter mobile reader, where a Genre tab is the
only way to see a genre grouping without extra filter UI, and the cap (not
missing functionality) was the only thing preventing several from being
visible together.

Verified live rather than assumed: pushed the web sidebar to 15 visible tabs
via the admin UI and direct API calls with no 409s, confirmed the existing
whole-sidebar scroll handles it with no clipping; built and ran the Flutter
Windows-desktop target with 14 extra tabs live, confirming the nav rail
scrolls and a Genre tab routes correctly. No scroll code needed writing on
either platform — both already had it (`overflow-y: auto` on web,
`SingleChildScrollView` in Flutter's `NavRail`) from before this change.

**Where:** `backend/routers/admin.py` (`create_custom_tab()`,
`update_custom_tab()`); `frontend/js/admin.js` (`renderCustomTabs()`);
`frontend/admin.html` (Add/Remove Libraries section); `CUSTOM_TABS_SPEC.md`
§3/§5.1/§6.

### Reading Queue: boolean column + singleton tab (Favourites pattern), not a join table

**Decided:** 2026-07-24.

**Why:** Reading Queue needed explicit per-issue "add/remove" membership —
unlike every existing Custom Tab type (folder/favourites/genre), which are
all computed/virtual filters over existing issue metadata at query time, with
no concept of an issue being explicitly placed into a tab. A join table
(`custom_tab_issues` or similar) would be the generic solution and would
support things Reading Queue doesn't currently need — arbitrary tabs with
arbitrary membership, ordering, "date added" metadata. But the actual ask is
narrower: one singleton "read later" flag per issue, functionally identical
in shape to `Issue.favorites` (also a boolean, also surfaced through exactly
one singleton `CustomTab` row). Rather than build new schema for a shape that
already has a working precedent, Reading Queue reuses the Favourites pattern
end-to-end: `Issue.queued_for_reading` boolean column,
`basis_type = 'reading_queue'` singleton tab, same bulk-endpoint/toggle-button
wiring. If a future ask needs real membership semantics (multiple queues,
ordering, "date added") that's a different, larger feature — not something to
speculatively build into this one.

**Where:** `backend/models.py` `Issue.queued_for_reading`;
`backend/routers/progress.py` bulk queue/unqueue endpoints;
`backend/routers/admin.py` `create_custom_tab()`'s `reading_queue` branch;
`CUSTOM_TABS_SPEC.md` §10.10.

### Genre Library: one `field_value` column, no `field_name` pair; dedup per-genre-value, not one-ever

**Decided:** 2026-07-24.

**Why:** Genre Library (`CUSTOM_TABS_SPEC.md` §10.9) needed a way to remember
which genre a `custom_tabs` row is scoped to. `HomeStrip` already has a
precedent for this — `field_name`/`field_value` pair, since a Home Strip can be
scoped by any of several dimensions (genre, publisher, writer, ...). Custom
Tabs' new type only ever means genre, though — `basis_type = 'genre'` already
tells you the dimension, so a `field_name` column would just always hold the
string `"genre"` and add nothing. Went with a single `field_value` column
instead, reusing the name for consistency with `HomeStrip` but not the pair.
Also decided duplicates are prevented per-genre-*value* (can't add "Horror"
twice, but "Horror" and "Cyberpunk" can coexist) rather than Favourites' "one
row ever" rule — Favourites has exactly one meaning so one row is the whole
feature, but Genre is explicitly meant to have several tabs, one per genre Tez
actually wants pinned to the sidebar.

**Where:** `backend/models.py` `CustomTab.field_value`;
`backend/routers/admin.py` `create_custom_tab()`'s `genre` branch;
`CUSTOM_TABS_SPEC.md` §10.9.

### Flutter library background: static color-glow blobs, not a ported blurred-photo backdrop

**Decided:** 2026-07-24.

**Why:** `mobile-reader-changes.txt` asked for the web's "cloudy/alien blur"
library background — several real cover images blurred and masked into soft
circles (`frontend/css/style.css`'s `.page-bg`). The literal port
(`ImageFiltered` Gaussian blur + `ShaderMask`/`RadialGradient` soft-circle
mask over `CachedNetworkImage`, in a new `page_backdrop.dart`) rendered as
hard-edged "patchwork" rectangles on Tez's real tablet instead of a soft
cloud. First fix attempt (the gradient's stop order was inverted, giving a
mostly-opaque disc instead of a gradual fade) didn't resolve it — the
remaining hard edges point to the image-filter chain not compositing
cleanly under this device's Impeller/Vulkan renderer, not just the gradient
math. Rather than keep iterating blind against a live device (each attempt
costs a full rebuild+install cycle), asked Tez whether literal web parity
mattered here; he confirmed it didn't ("doesn't have to change like the web
UI, just give a little depth"), so switched to a technique that can't
produce this failure mode at all: static, low-opacity `RadialGradient`-filled
circles tinted from existing theme colors, no blur filters or network
images involved. Light theme uses the same blob layout with RGB-inverted
tints, per a later Tez request, so it doesn't read as a washed-out copy of
the dark version.

**Where:** `flutter_app/lib/widgets/page_backdrop.dart`;
`docs/v2.6/progress.md` "Flutter mobile reader: card visual-parity porting
(Phase B)".

### Flutter mobile theming: build light+dark infrastructure before touching card visuals, not dark-first

**Decided:** 2026-07-23.

**Why:** the Flutter reader had zero theme-switching machinery going in — no
`ThemeMode`, no light color set, no persisted preference, no toggle;
`AppColors` was a `static const` dark-only holder referenced directly by
every widget. Two sequencing options were considered when scoping the work
Tez asked for (bring the dark theme in line with the web app's redesigned
cards, and add a light theme via a Settings toggle):
- **Dark-first** — fully polish the dark cards to match the web app's
  redesigned look, ship that, then add light theme + toggle as a second
  phase. Gets a visible win sooner, but every widget touched for the dark
  polish would need touching again to make it theme-aware, since nothing
  reads from a theme yet.
- **Infra-first (chosen)** — convert `AppColors`/`AppText` into a
  `ThemeExtension`-backed light+dark pair and wire up `ThemeMode` + the
  Settings toggle first, with no visual change to the cards yet, then port
  the redesigned card look into both themes in the same later pass (the web
  app already defines both, so this isn't double work).
- Chose infra-first: it touches each widget exactly once. Confirmed with Tez
  before starting (see `docs/v2.6/progress.md` "Flutter mobile reader:
  light/dark theme infrastructure (Phase A)").

**Where:** `flutter_app/lib/theme/tokens.dart`; `docs/v2.6/progress.md`.

### BUG-033 fix: re-rank Search Online results in ComicVault's own bridge layer, not by patching the pinned CT dependency

**Decided:** 2026-07-23.

**Why:** the root cause is inside the pinned `comictagger`/`comictalker` pip
dependency (`comictalker/comiccacher.py`'s `get_search_results()` — a cache-read
SQL query missing `ORDER BY`, so a cached search replays in arbitrary join order
instead of ComicVine's original relevance order). Two ways to fix it were
considered:
- **Monkeypatch the dependency's cache query at runtime** (e.g. add `ORDER BY
  rowid` to `get_search_results()`) — fixes the true root cause and would also
  benefit any other code path that reads this cache, but means reaching into a
  pinned third-party git commit's private SQL internals. If that pin is ever
  bumped (`requirements.txt` already notes it's pinned past the last PyPI
  release for unrelated reasons), the patch could silently stop applying or
  break against a changed schema, with no test surface to catch it.
- **Re-rank results in ComicVault's own `ct_bridge.py`** (chosen) — `ct_bridge.py`
  already exists specifically as the layer that adapts CT's raw output for
  ComicVault's own use, so recomputing "best match" there rather than trusting
  CT's pass-through order keeps the fix inside code ComicVault owns and tests
  against, independent of how the dependency's internals evolve.
- Chose the second: `search_series()` now scores each result with
  `difflib.SequenceMatcher` over `comicapi.utils.sanitize_title`-normalized
  strings (the same technique CT's own `titles_match()` uses internally for
  accept/reject filtering, just applied as a sort key), tiebroken by
  `count_of_issues` descending. This makes "Best match" actually deterministic
  and correct regardless of whether the underlying call was cache- or
  live-served, rather than depending on an assumption (`EDITOR_SPEC.md` §9.6's
  "results stay in ComicVine's own relevance order") that a cache hit can
  silently violate.

**Where:** `backend/ct_bridge.py` (`_series_match_score()`, `search_series()`);
`docs/EDITOR_SPEC.md` §9.6; `docs/archive/bugs-fixed-archive.md` BUG-033.

### Basic PWA support: explicit-button-only install, dedicated root-scope service worker route

**Decided:** 2026-07-23 (backfilled — the implementation itself was built by
Dispatch, outside a Claude Code session, in response to an ad-hoc feasibility
ask from Tez; this entry captures the reasoning after the fact from the
diff/new files, since Tez has manually confirmed it works).

**Why:** Two choices in the implementation are non-obvious enough to be worth
recording so a later session doesn't "fix" them by accident:
- **No automatic install prompt.** `frontend/js/pwa.js` captures the browser's
  `beforeinstallprompt` event and calls `preventDefault()` on it immediately,
  stashing it for later instead of letting the browser show its own mini-
  infobar. Install only ever fires from the explicit **Install App** button
  on the Admin page (hidden unless the page is actually installable). This
  keeps the install offer out of every visitor's face on every page and puts
  it somewhere Tez already goes to manage the app.
- **`/sw.js` gets its own FastAPI route, not `/static/sw.js`.** A service
  worker's control scope is limited to the path it's served from and below —
  serving it under the existing `/static` mount would only ever let it
  control `/static/*`, not the actual app pages. `backend/main.py` adds a
  dedicated `GET /sw.js` route (still reading the file from `FRONTEND_DIR`)
  with `Cache-Control: no-cache` so browsers always revalidate it against
  the server rather than serving a stale cached worker indefinitely.

Caching strategy is also worth noting even though it's more routine:
`frontend/sw.js` is cache-first for the static app shell (CSS/JS/images/
manifest) and network-first-with-cache-fallback for `/api/*` — always want
fresh library data, but the shell itself can serve instantly from cache.

**Where:** `backend/main.py` (`/sw.js` route), `frontend/js/pwa.js`,
`frontend/sw.js`, `frontend/manifest.json`, `ADMIN_SPEC.md` §2 ("Install App"
row + new "Install App / PWA support" subsection), `docs/v2.6/progress.md`
"Session — 2026-07-23 — Basic PWA support (Install App button)".

### Series/Issue backdrop bleed: shared `--container-pad-x` token instead of a second hardcoded `-30px`

**Decided:** 2026-07-22, fixing the Series/Issue Detail backdrop bleeding past
the sidebar edge at the ≤640px breakpoint.

**Why:** `.series-backdrop`/`.issue-backdrop` cancelled `.container`'s side
padding with a literal `left: -30px; right: -30px` to achieve their edge-to-
edge bleed. The 640px responsive breakpoint shrinks `.container`'s own
padding to `10px` but the backdrop's offset stayed `-30px`, so below that
width the backdrop overshot the container's real edge by 20px on each side —
visually bleeding under the sidebar on the left. Fixed by introducing
`--container-pad-x` (`tokens-base.css`, default `30px`) as the single source
for that padding value: `.container`'s padding and both backdrops' negative
offsets now all read from it, and the 640px media query overrides the token
itself (`10px`) rather than overriding `.container`'s padding directly — the
two literally cannot drift apart again since there's only one number.

**Where:** `frontend/css/tokens-base.css` (`--container-pad-x`),
`frontend/css/style.css` (`.container`, `.series-backdrop`, `.issue-backdrop`,
the 640px media query).

### Card Size range shift: preserve 50%/100% pixel anchors, treat stale saved values as unset

**Decided:** 2026-07-22, when replacing the 10/25/50/75/100% Card Size options
with 30/40/50/60/70/80/90/100%.

**Why:** Two calls that weren't dictated by the request itself. First, kept
`CARD_SIZE_PX['50']` (160px) and `['100']` (220px) numerically unchanged and
interpolated the new in-between steps at the same ~12px/10% rate the old map
used between 50-100%, rather than picking a fresh scale — anyone with `50` or
`100` already saved sees zero visual change. Second, a `cv_card_size` value
saved before this change (`10`/`25`/`75`) no longer matches any option; rather
than leave it passed through unchecked (which left the Admin dropdown
rendering blank, caught in manual testing, even though the grid itself still
rendered correctly via an existing internal fallback), both `app.js` and
`admin.js` now validate the stored value against the live option set and fall
back to `30` if it doesn't match.

**Where:** `frontend/js/app.js` (`CARD_SIZE_PX`, `cardSize` init),
`frontend/js/admin.js` (`initCardSize()`).

### Backdrop/cloud-field opacity-blur tokens: split per-theme after all, reversing the original "same in both themes" call

**Decided:** 2026-07-22, splitting `--backdrop-opacity`/`--blur-backdrop`
(Series/Issue Detail cover backdrop) and `--pagebg-blob-opacity`/
`--pagebg-blur` (Home/Browse/Folder View cover cloud field) into light-theme-
only overrides in `tokens-light.css`.

**Why:** Both token pairs lived only in `tokens-base.css`, with an explicit
comment recording a deliberate original choice: "Same values in both themes
(Design's elevation.css doesn't override these for light)." That held up
fine when the values were only ever tuned against dark. Tez reported the
same low-opacity/light-blur values that read well against dark's dark
background were close to invisible against light theme's paler `--bg`/
`--surface`, and wanted independent control per theme rather than one
compromise value. Followed the existing `tokens-light.css` override pattern
(explicit `:root[data-theme="light"]` block + matching `@media
(prefers-color-scheme: light)` block) instead of inventing a new mechanism.
Dark theme keeps reading the original `tokens-base.css` values untouched.

**Where:** `frontend/css/tokens-light.css`, `frontend/css/tokens-base.css`
(comment updated to point at the light override rather than claiming both
themes share the value).

### Bulk Delete: one permanent DB+disk operation, no DB-only tier; first custom-modal destructive confirmation

**Decided:** 2026-07-21, adding a Delete action to the multi-select bottom toolbar.

**Why:** The original request specified two delete tiers — DB-only ("remove from
library, leave file untouched") and DB+disk (permanent). While scoping this, I
flagged that DB-only wouldn't actually stick: the scanner's own invariant is "flag
missing, don't delete" (`SPEC.md` §"Incremental rescan", lines ~239-245, ~673-674) —
a file left untouched on disk gets silently re-imported as a new issue on the next
library rescan, undoing the DB-only delete with no trace it ever happened. Tez agreed
this wasn't worth shipping as a half-safeguard and collapsed the feature to a single
operation: delete the DB row (with cascades) and the file on disk, together,
permanently, no recycle-bin/send2trash softening. Also decided against gating this
behind a "delete files?" checkbox pair (mutually-exclusive, grey-out-the-other UI)
since there's only one operation now — just a single confirm modal.
Separately: this is the app's first destructive action to use a real custom
pill-button modal instead of the native `confirm()` every other Danger Zone action
uses (`ADMIN_SPEC.md` §"Danger Zone", ~lines 490-494 — even ADMIN_SPEC's own wording
once said "modal" and the actual build used `confirm()` anyway). Tez explicitly asked
for a proper modal here, matching the rest of the app's UI language, so
`ensureDeleteConfirmModal()` was built fresh rather than reusing that shortcut.
**Where:** `backend/routers/progress.py` (`POST /progress/bulk/delete`),
`frontend/js/app.js` (`ensureDeleteConfirmModal()`, `runBulkDelete()`,
`removeIssuesFromDom()`), `SPEC.md` §20.15.

### Issue Detail Format pill link: fall back to the fieldview filter for a "Series"-format issue with no known siblings, rather than always linking to `/series/{id}`

**Decided:** 2026-07-21, adding an href to the Format pill on `/issue/{id}`.

**Why:** Tez specified two cases directly — format is literally "Series" *and*
there's more than one issue → link to the series page; anything else → the
same fieldview filter the Genre pills already use. He didn't say what should
happen when format is "Series" but `Count` is 1 or absent (common — many
scanned issues have no `<Count>` in their XML at all). Chose to fold that
case into the fallback (fieldview filter on `format=Series`) rather than
linking to `/series/{id}` regardless: without a known issue count there's no
way to tell "genuinely a lone issue of an ongoing series" from "the XML just
never recorded a count", and the fieldview filter is a safe default either
way (it still surfaces every other "Series"-format issue, series page or
not). If this reads wrong in practice — e.g. Tez expects any "Series"-format
issue to always go to its series page — it's a one-line condition change
(`data.format === 'Series'` alone, dropping the `count > 1` check).
**Where:** `frontend/js/app.js` (issue-detail badge-row `format-badge`
construction), `SPEC.md` §20.8.

### Series Detail hero: dropped the rounded-card backdrop, unified with Issue Detail's full-bleed recipe

**Decided:** 2026-07-20, follow-up bug session after the CSS theme-token split.

**Why:** Tez reported the series page's cover backdrop "doesn't stretch,
leaving a gap top and sides." Investigated live and confirmed the backdrop's
own sizing math was correct (no actual box-model gap) — the perceived gap
came from `.series-hero-wrap` clipping the backdrop to a rounded, inset card
(`overflow:hidden; border-radius`) plus a flat 45% black overlay on top of an
already-faint (opacity 0.28) image, so on covers with dark artwork near the
crop line it read as empty space bounded by a visible card edge. Asked Tez
which treatment to match; he pointed at the Issue Detail page's backdrop,
which has no such card — it bleeds past `.container`'s side padding via
negative margins and fades through a gradient instead of a flat overlay, and
was never perceived as gappy.

Rather than patch series's numbers in isolation, unified both pages onto one
recipe: same bleed technique (`left/right: -30px`), same gradient fade
(`var(--bg) 0% → transparent 30% → var(--bg) 100%`, replacing series's flat
overlay), and the same opacity/blur values now sourced from one place
(`--backdrop-opacity: 0.18`, `--blur-backdrop: 2px` in `tokens-base.css` —
previously `0.28`/`3px` for series and separate hardcoded `0.18`/`2px`
literals for issue, i.e. already drifted apart despite the tokens' own
comment claiming to be the shared recipe for both). Series keeps its own
height (content-driven via `.series-hero`'s padding) rather than adopting
issue's fixed 440px, since its content differs.

**Known pre-existing gap not addressed this session:** the `-30px` bleed
offset is hardcoded to match `.container`'s default 30px side padding: the
`max-width:640px` breakpoint drops that padding to 10px, so both pages'
backdrops technically over-bleed by 20px on narrow viewports. Pre-existing
on the issue page since 2026-07-17; now also true of series since it matches
the same recipe. Not fixed here — out of scope for a backdrop-consistency
bug fix, flag if it becomes a real complaint.

### CSS theme-token file split: three files (base/dark/light), token-only pass, component split deferred

**Decided:** 2026-07-20, CSS theme-token refactor session — executed
`docs/v2.6/code-handoffs/css-theme-token-refactor-plan.md` (drafted 2026-07-17).

**Why:** No doc previously governed CSS *file* architecture in this repo
(`SPEC.md` documents theme *behaviour* — OS auto-match + Admin Appearance
override — not file structure), and `style.css` had grown to one ~3900-line
file loaded by all 6 pages with dark values, light overrides, and every
component's layout CSS interleaved. Light-theme gaps kept surfacing while
working other areas (admin, editor, series/issue) precisely because
"light theme values" and "code that never had any" couldn't be cleanly told
apart in one undifferentiated file. Splitting the token layer out first —
before the larger page/component split (`admin.css`/`editor.css`/`grid.css`,
deferred to `ROADMAP.md`) — makes that distinction structural instead of
requiring a manual read each time.

Cascade order is base → dark → light → style, loaded via 4 plain `<link>`
tags per page (no `@import` chaining, no JS). This works because CSS custom
property resolution is lazy (used-value time, not file-parse-order) —
`tokens-base.css`'s semantic aliases (`--surface-card: var(--surface)`, etc.)
correctly pick up whichever of dark/light's `--surface` is active regardless
of which file *defines* the alias vs. what it points to, as long as all
three token files load before `style.css` uses them.

Two accompanying decisions, made mid-execution rather than pre-planned:

1. **`.state-read`/`.state-part-read` got its planned token fix
   (`--read-overlay`/`--read-overlay-text`) even after discovering it's
   currently dead code** — every card builder in `app.js` emits
   `.cover-card--redesign`, which nulls this exact styling and substitutes a
   progress-bar/`% Read` label instead. Kept the fix anyway: it's what the
   plan specified, it's harmless, and it's a live safety net if a
   non-redesigned card path is ever reintroduced. Noted as dead code in
   `v2.6/progress.md` rather than silently presenting it as a visible fix.

2. **`.card-genre-ribbon`'s light-theme bug (found during step-6
   verification, not in the original plan) was fixed as a fixed literal
   (`--rc-genre-text`), not a themed token pair**, despite using the same
   `--read-overlay`/`--read-overlay-text` mechanism being the more
   "consistent" choice on the surface. The ribbon lives inside
   `.cover-card--redesign`, which SPEC.md §20.20 requires to render
   identically in both themes ("dark-only, fixed regardless of the site's
   light/dark theme setting") — the bug was that it referenced the
   theme-dependent `var(--text)` by mistake, not that it needed theme-aware
   values. Theme-tokenizing it would have been the wrong fix for a component
   the spec says must *not* be theme-split. Matches the pattern the codebase
   already used one section over, for `.folder-result-path`
   (`style.css` ~1354): "Redesigned card: fixed dark face, so use the same
   off-white/cream meta colour... rather than the theme-dependent --text-3
   grey."

Also swept 5 scattered danger/error hex literals to `var(--danger)`/a new
`--danger-text` alias (step 7 of the plan) — cross-checked against
already-correct sibling patterns elsewhere in the file (e.g.
`.pt-remove-btn:hover`, `.editor-error--notice`) to separate real oversights
from two decorative fixed-color favourite-heart badges that are
deliberately theme-independent (a physical-sticker effect on cover art, not
a themed UI state) and correctly left untouched despite matching the same
reddish-hex grep.

**Found but not fixed, logged as BUG-032:** the 6 HTML page routes and the
`/static` mount send no `Cache-Control` header, so browsers can serve a
stale cached page on normal navigation. Pre-existing behaviour, unrelated to
the CSS work itself, but this session's edits to all 6 HTML files made it
visible for the first time. See `BUGS.md`.

### Desktop reader window resize: size target measured against live chrome overhead, not the raw cover-to-window ratio

**Decided:** 2026-07-19, desktop reader cover-resize session.

**Why:** `window_manager`'s `setSize`/`getSize` operate on the Windows outer window
rect — title bar and borders included — confirmed by reading its native Win32
source (`SetWindowPos`/`GetWindowRect` directly, no client-area adjustment). Setting
the window to exactly 75% of the cover's pixel dimensions therefore left the actual
Flutter content area smaller than intended by that chrome's size. For a tall
portrait cover this was a small, mostly invisible fraction of the height budget; for
a short window (a wide/landscape cover) the same fixed ~30-40px title bar ate a much
bigger fraction of a much smaller budget, visibly cropping the bottom of the page —
caught by Tez during manual testing, not anticipated at plan time.

Fixed by measuring the live chrome overhead each resize
(`windowManager.getSize()` — current outer frame — minus `MediaQuery.sizeOf(context)`
— current content area, both in logical pixels) and adding it back onto the desired
content size before calling `setSize`, rather than hardcoding an assumed title-bar
height. This self-corrects for whatever title bar/border style Windows is actually
rendering (theme, DPI, etc.) instead of encoding an assumption that could drift.

Same session, a second bug surfaced and got the same live-testing-driven fix: the
resize calls are fire-and-forget (must never block opening a comic), so nothing
guaranteed they'd apply in the order comics were opened — a slower call finishing
after a faster one could silently overwrite a newer comic's correct size. Fixed with
a monotonic request-generation counter in `WindowResizeService` (`window_resize_service.dart`)
— a resize only applies if it's still the most recently *issued* request by the time
it finishes, regardless of completion order. See `v2.6/progress.md` 2026-07-19
session entry for full build detail.

### Admin Logs modal: scan-boundary markers written into the log file, not a persisted count

**Decided:** 2026-07-19, Admin Logs "most recent scan only" session.

**Why:** to slice "just the last scan's entries" out of `changed_files_log.md`/
`new_files_log.md`/`missing_log.md` (which have zero-or-more lines per scan, no
per-line timestamp), something needs to record where each scan's section starts.
Two options: (a) persist the per-scan line counts `ScanProgress` already computes
in-memory (e.g. alongside `log_last_viewed` in `config.json`), or (b) write an
explicit marker line into the log file itself at the start of each scan.

Went with (b). A config-side count is invisible outside the app and has to stay in
lockstep with the log file (a manually-edited or externally-truncated log file
would silently desync it); a marker line is self-describing, lives with the data it
describes, survives being opened in a text editor (arguably *helps* there — it's a
visible scan-run boundary for manual review too), and needs no new `config.json`
state. Trade-off accepted: this changes the on-disk log format going forward
(documented in `ADMIN_SPEC.md` §8) — pre-existing log files have no marker, so
`read_recent_log()` falls back to full content for those until their next scan adds
one. No backfill — forward-only, same convention as other scan-detection fixes (see
BUG-029 entry below).

### BUG-029 fix: content-hash rename detection is forward-only, no library backfill

**Decided:** 2026-07-18, BUG-029 fix session.

**Why:** Tez asked for a cost/impact analysis before committing to content
hashing as the fix. The scanner is deliberately not I/O-bound today
(`PERFORMANCE.md` finding #16 — it only reads the ZIP central directory and
one cover per file, not the whole archive); a content hash requires a full
sequential read of every byte, which is a fundamentally different cost
profile. A one-time backfill across the whole library (~5,427 issues) was
estimated at roughly 75-95 minutes of continuous reads off the `L:\Comic
Archives` USB 3.0 HDD (~430GB at its measured 77-95MB/s), while hashing only
new/changed files going forward is nearly free — real scans typically touch
0-2 files (`PERFORMANCE.md` finding #7). Also ruled out doing the backfill
automatically inside `database.py`'s existing `_add_missing_issue_columns()`
startup migration — that pattern is safe for cheap additive columns like
`file_size` (a stat call) but would block server startup for over an hour if
applied to a full-content hash.

Tez confirmed the dev DB will be wiped at least once more before production,
so spending 75-95 minutes protecting data that won't survive to production
wasn't worth it — decided to go forward-only: `content_hash` is computed and
stored only on INSERT/UPDATE from this fix forward, no backfill tool built
(not even as an optional/deferred add-on). Consequence accepted: the 4
already-orphaned rows from the original bug report, and any row not touched
again before it's next renamed, stay unprotected until they're naturally
re-scanned — cleaned up via the existing manual `cleanup-missing` endpoint,
same as before this fix.

**Also decided (same session):** rename-matching runs against every DB row
currently off-disk (`file_size` + `content_hash` match), not just rows going
missing in the same scan pass — this catches a rename that happened between
two separate scan runs, not only one detected within a single run, at no
extra cost since it's the same query the missing-flagging loop already did.

### BUG-026/BUG-027 fix: Clear Database self-restarts instead of adding a "quiesce" mode

**Decided:** 2026-07-18, BUG-026/BUG-027 fix session.

**Why:** BUG-027's own `BUGS.md` note assumed the fix needed a way to "quiesce
writes" — pause the live server without fully stopping it — before the DB
could be safely wiped and VACUUMed. Investigation found that primitive
doesn't exist anywhere in the codebase, and the only two proven process
states are "live pooled engine" and "engine disposed, process about to exit"
(the pattern `restore_database()` already uses for its BUG-016 fix). Rather
than inventing a new quiesce concept, `clear_database()` reuses that exact
sequence — `checkpoint_wal()` → `engine.dispose()` → sidecar delete →
`_schedule_delayed_exit()` — and simply accepts the same ~15s self-restart
Restore Database and the Server Port control already impose. This also
resolves BUG-027 as a side effect: since the endpoint is fully
self-contained, there's no longer any reason to look for a way to "stop the
server, then wipe" — a sequence that was never actually reachable from the
Admin UI anyway (Stop/Start Server are tray-menu-only).

**Also decided (same session):** Clear Database's reset scope includes scan
logs (`last_scan_log.md` etc.) and `log_last_viewed`/`next_processing_run`
in `config.json`, not just thumbnails+VACUUM — Tez's call, for a fuller
"start fresh" reset rather than the narrower thumbnails-only scope BUG-026
itself would have minimally required. Confirmed safe to null
`next_processing_run`: the Processing Folder Automation loop
(`scheduler.py`) already treats a missing/null value as "recompute on next
tick," not "fire immediately."

**Bug found during this fix's own verification:** `clear_database()` had to
be changed from a plain `def` to `async def`. `_schedule_delayed_exit()`
calls `asyncio.create_task()`, which requires a running event loop in the
calling context; FastAPI runs plain `def` routes in a worker thread with no
event loop, so the call raised `RuntimeError: no running event loop` — caught
via a live 500 response during manual testing, not by inspection beforehand.
`restart_server()` and `restore_database()` were already `async def`, which
is exactly why they didn't hit this.

### BUG-016 fix: `engine.dispose()` before deleting the post-checkpoint `-wal`/`-shm` sidecars

**Decided:** 2026-07-18, BUG-016 fix session.

**Why:** the obvious fix for the WAL-replay bug is `PRAGMA wal_checkpoint(TRUNCATE)`
before copying the backup over `db_path`. Testing that in isolation showed TRUNCATE
alone empties the `-wal` file to 0 bytes but doesn't remove it, and a follow-up
`unlink()` of the now-empty sidecar threw `PermissionError` on Windows — the app's
SQLAlchemy engine uses `QueuePool` (confirmed via `type(engine.pool)`), which keeps a
real, pooled OS-level connection open in the background, and that connection still
holds a file handle on `-wal`/`-shm` even after the checkpoint. Calling
`engine.dispose()` right after the checkpoint releases that handle and lets the
sidecar deletion succeed. Only done in `restore_database()`, not
`run_database_backup()` — disposing mid-request is harmless in restore's case since
`_schedule_delayed_exit()` tears the process down ~1s later anyway (a fresh connection
just gets opened on relaunch), but doing it during an ordinary backup would
needlessly drop the live server's connection pool for no reason, since backup never
deletes the sidecars at all.

### BUG-013 fix: backfill `file_size` at migration time; split the rename/move blind spot into a new bug (BUG-029) instead of stretching BUG-013's scope

**Decided:** 2026-07-18, BUG-013 fix session.

**Why (backfill):** the fix adds `Issue.file_size` and requires it to match
alongside mtime before the scanner will skip a file. Leaving every existing
row's `file_size` at NULL after the migration would make the very next full
scan treat all ~5,500 already-scanned files as "changed" (same effect as a
NULL `date_modified` already has) — a one-time mass reprocess/re-thumbnail
storm for something that isn't actually changed. Backfilling from disk inside
the same migration (`_add_missing_issue_columns()`) avoids that; confirmed
cheap (stat-only, not a read) against the 2026-07-18 performance baseline.

**Why (split, not expand):** BUG-025's investigation earlier the same day had
pointed at "BUG-013" as the bug covering a file/folder renamed *outside* the
app while already in the library (scanner's exact-`file_path`-match, no hash
or move detection). But BUG-013's own text was always scoped narrower — a
same-path re-save that preserves mtime. Expanding BUG-013's scope retroactively
to also cover renames would have been the easy path, but the two are different
mechanisms with different fixes (a size check vs. some form of content-hash or
move-heuristic matching), and a live example of the rename gap turned up
directly during this session's migration test (`'68 Homefront [2014]` →
`(2014)`, IDs 1-4, still `missing=False`) — concrete enough to warrant its own
tracked entry rather than a footnote. Opened as **BUG-029**; BUG-025's stale
"see BUG-013" cross-reference was updated to point at it.

### BUG-025: kept the DB-sync fix even after re-diagnosing it as not-a-bug

**Decided:** 2026-07-18, BUG-025 follow-up session.

**Why:** BUG-025 was filed after the Move Series/Singles Folders tool moved
already-in-library content (the 2000 AD reorg) without updating `Issue.file_path`
/`CustomTab.folder_path`, leaving thousands of dead-path rows. A fix
(`sync_moved_paths_to_db()` in `backend/library_move.py`) was built and
scratch-verified before Tez pointed out the tool's actual intended workflow is
Stage 3 Processing → Move → manual Scan — and `scan_exclude: ["Processing"]`
means Processing content is never scanned before the move, so no DB row exists
yet to desync in that normal flow. The 2000 AD case was the tool being pointed
at content already inside the library (already scanned) — an atypical use, not
the designed one. See `docs/archive/bugs-fixed-archive.md` BUG-025 for the full
resolution writeup.

**What changed:** BUG-025 was closed as "not a bug in the intended workflow"
rather than left open or logged as a genuine fix. The sync code itself was
kept rather than reverted, since it's a no-op on the normal path (nothing
matches an unscanned source) and correctly protects the one case that actually
broke (pointing the tool at already-in-library content) — reverting working,
tested, harmless code just because the bug that prompted it turned out to be
narrower than first thought would have been pure churn.

**Also clarified:** BUG-025 and BUG-013 were being conflated. BUG-025 is
specifically the Move tool's own DB bookkeeping when *it* relocates something.
The Scanner's inability to recognize a folder that moved/renamed *outside* the
tool (e.g. a manual Explorer rename) while already in the library is a
different bug, in `scanner.py`, not touched by this session — at the time
this was tracked under BUG-013; BUG-013's own 2026-07-18 closeout later split
that rename/move scenario out into its own entry, **BUG-029** (see below).

### BUG-028 fix: centralize junk-entry filtering, don't reconcile the 5 inconsistent image-extension whitelists

**Decided:** 2026-07-18, BUG-028 fix session.

**Why:** investigating the macOS-junk-entries bug turned up 5 different
image-extension whitelists across the codebase (`scanner.py`, `reader.py`,
`editor/archive_io.py`, `image_convert.py`, `archive_convert.py`), no two
identical — a real inconsistency, but an unrelated one. BUG-028 is about
`._`-prefixed/`__MACOSX/` junk entries being counted as pages, not about
which extensions count as images. Reconciling the whitelists too would have
widened the diff and risked changing behaviour (e.g. `.tiff` support) nobody
asked to change in this session.

**What changed instead:** one shared predicate,
`archive_formats.is_macos_junk_entry()`, applied at every site that lists or
rebuilds archive image entries (scanner, reader, Editor, Convert Archives,
Convert Images) — each site kept its own existing extension whitelist,
just piped through the new junk filter. The 5-way whitelist inconsistency
is unfixed, noted here as a known, separate cleanup candidate if it ever
causes an actual problem.

**Also decided, same session:** the 22 already-affected issues' `page_count`/
`cover_path` DB fields were remediated directly (see
`docs/archive/bugs-fixed-archive.md` BUG-028), but their archive files on
disk were deliberately left untouched — only files that pass through Convert
Archives/Convert Images/CT Auto-Tag going forward get the junk physically
stripped from the archive. Direct-to-library files keep the junk bytes on
disk but the app now correctly ignores them everywhere. `8_macos_junk_sweep.py`
will therefore keep reporting these 22 as "containing junk entries" even
though the actual bug symptom (`page_count is wrong`) is fixed — the sweep
script's two numbers now mean different things; use `page_count is wrong`
as the real fixed-or-not signal, not the raw "containing junk" count.

### `INBOX.md` is Tez's personal scratchpad — Code doesn't write to it, even with good intentions

**Decided:** 2026-07-18, Move Series/Singles Folders session (v2.6 Item 10).

**Why:** `working-rules.md` already said "Code never adds to it or triages it
unprompted" (settled 2026-07-16), but mid-session Code wrote an unprompted
entry into `INBOX.md` anyway — a note about a DB file_path-relink gap found
while investigating the 2000 AD folder move, added because it seemed
inbox-shaped and there was nowhere else obvious to put it. Tez caught it
immediately and clarified the intent more strongly than the existing wording
conveyed: it's not just "don't triage it," it's "this is mine, you don't
need to factor it into your own work or use it as a place to park findings."
Existing wording was technically sufficient but evidently not load-bearing
enough in practice.

**What changed:** Entry reverted. `working-rules.md`'s "Inbox workflow"
section restated with an explicit no-parking-findings clause and a pointer
to surface things directly in conversation instead. `CLAUDE.md`'s doc-map
table row for `INBOX.md` updated to say the same, so it's visible from
either entry point rather than living only in one doc.

**Where:** `docs/meta/working-rules.md` ("Inbox workflow"), `CLAUDE.md`
(§2 doc table), `docs/INBOX.md` (entry reverted).

---

### Move Series/Singles Folders: article-stripping alpha rule, and why 2000 AD needed no code exception

**Decided:** 2026-07-18, same session.

**Why (alpha rule):** the obvious rule — bucket on a folder name's literal
first character — contradicts `SPEC.md` §5's own worked examples (`'68
Homefront` → `#`, `The 13th Artifact` → `#`) and most of the real library.
Checked the actual folder tree before picking a rule rather than trusting
the spec's prose description in isolation: the library consistently strips
a leading `The`/`A`/`An` before bucketing (`A Taste for Blood` → `T`, not
`A`). Picked that as the rule. **Known residual gap, deliberately not
fixed:** some titles are filed by subject rather than by this rule at all —
`The Complete Terminal City` sits under `T` (matching `The Complete Bad
Company` under `B`), which the article-strip rule alone would send to `C`.
Near-miss detection (§11.7.4) is the mitigation, not a fix — flagging a
probable mismatch for Tez to decide is safer than trying to encode a second,
fuzzier filing convention into the mover.

**Why (2000 AD):** originally scoped with a hardcoded root-level exception
in mind, because `20000AD` sat outside the whole A–Z/`#` scheme at the time
(a typo'd folder name, and historically home to more than just progs —
megazines, one-shots, year books). Tez restructured the actual folder
instead of asking for a code exception: renamed to `2000 AD`, moved under
`#\Series\2000 AD`, kept the existing `2000 AD - YYYY` sub-folders exactly
as they were. That fits the ordinary alpha rule with zero special-casing —
the only reason it then worked correctly is the recursive-merge fix
(source folder shape mirrors the library's, mover recurses to match).
Preferred over a code exception because a naming/structure fix is permanent
and self-documenting; a hardcoded exception is one more thing to remember
exists and to keep in sync if the library structure ever changes again.

**Where:** `backend/library_move.py` (`_alpha_bucket`), `ADMIN_SPEC.md`
§11.7.2/§11.7.3.

---

### Move Series/Singles Folders: recursive merge and exact-duplicate blocking, both structural not name-based

**Decided:** 2026-07-18, same session, both found during Tez's manual test
pass (not caught by the automated test suite beforehand).

**Why (recursive merge):** the first real run put a Stage 3 `2000 AD -
2026` folder as a wrong sibling of the existing `#\Series\2000 AD`,
instead of merging into `#\Series\2000 AD\2000 AD - 2026`. The original
merge logic (`_merge_series_folder`) treated every entry in a matched
folder as opaque — a same-named subfolder at the destination just failed
instead of being merged into one level deeper. Considered and rejected:
special-casing "2000 AD" by name to know it should nest. Chose instead to
make the merge itself recursive and purely structural (same-named folder →
merge deeper; same-named file → per-file clash, unchanged) — this
generalizes to any future container-style series without the mover needing
to know anything about it by name, and is the direct enabler for the "no
2000 AD exception" decision above.

**Why (exact-duplicate blocking):** Tez flagged that older library folders
use `Title [YYYY]` where current Stage 3 output uses `Title (YYYY)` — an
unprocessed folder under the new convention could duplicate an existing one
under the old convention, and the existing near-miss warning (non-blocking)
wasn't strong enough for a case this confident. Split into two tiers rather
than just lowering the near-miss threshold: a folder that normalizes
*identically* to an existing one (same content stripped of year-bracket
style and punctuation) is blocked outright, not moved, logged as a failure
naming the exact match; a folder that's merely *similar* keeps the older
non-blocking warning behaviour. Kept as two separate checks rather than one
sliding scale so a confident duplicate can never be "just a warning" by
threshold tuning drifting later.

**Where:** `backend/library_move.py` (`_merge_into_existing`,
`_find_exact_duplicate`, `_find_near_miss`), `ADMIN_SPEC.md`
§11.7.3/§11.7.4.

---

### Folder View's in-page "← Back" / "Mark all read" row removed, not just restyled

**Decided:** 2026-07-17, Folder View card-chrome session (same session as the
subfolder-card border/padding match above).

**Why:** Tez asked to remove both buttons so the grid pushes up flush under
the menu bar, matching Browse's cover-grid. Checked before removing rather
than just deleting on request: `folderBackBtn`'s handler (`app.js`,
`renderFolderView()`) was literally `window.history.back()` — a same-effect
duplicate of the browser's own back button/gesture, not a "go up one folder
level" action, so nothing is lost by dropping it (confirmed live: browser
back from a leaf folder correctly lands back on its parent's listing).
`folderMarkAllBtn` called a folder-scoped bulk mark-read endpoint; the
already-existing multi-select toolbar (`ensureSelectionToolbar()`, `app.js`
~line 230, "Mark Read"/"Mark Unread") covers the same job for whatever's
currently selected in the grid, so the dedicated button was redundant rather
than a genuine capability loss. Backend endpoint
(`/library/tab/{id}/folder/mark-read`) deliberately left in place — removing
it wasn't asked for and it's harmless dead surface, not a maintenance risk.

**Where:** `frontend/index.html` (`#folderView` markup), `frontend/js/app.js`
(`renderFolderView()`, `startFolderViewSearch()`; the now-unused
`markFolderViewRead()` function deleted outright), `frontend/css/style.css`
(`.folder-view-nav` rule removed, `.folder-search-label` given its own
stand-alone spacing since it no longer sits inside that nav row).

### Cover-image cache invalidation: version-stamped URL, not per-request revalidation

**Decided:** 2026-07-16, BUG-023 fix session.

**Why:** the interim fix for the stale-cover bug (`Cache-Control: no-cache` on
`GET /api/cover/{id}`, forcing the browser to check with the server on every
request) worked, but Tez asked whether that adds per-request overhead across a
~5,500-issue library, and whether invalidation could instead ride on the
scanner's own change detection rather than a blind "always ask" policy. It can:
`path_utils.cover_url(issue)` now appends a `?v=` stamp derived from
`Issue.date_modified` — the field the scanner already sets to the archive's
filesystem mtime the moment it detects and applies a change. This gets both
properties at once — unchanged covers keep the original zero-request 24h cache
(`v2.6 Item 2 Phase 4`'s intent, `PERFORMANCE.md` finding #3), and changed
covers get a structurally new URL the instant a rescan updates that row, with
no reliance on reload gestures or revalidation timing. Chosen over the simpler
`no-cache` approach specifically to avoid adding a network round trip to every
cover load in the common (unchanged) case.

**Where:** `backend/path_utils.py` (`cover_url()`), `backend/routers/reader.py`
(`COVER_CACHE_CONTROL`), 9 call sites across `backend/routers/library.py` /
`home.py`. Full detail in `docs/archive/bugs-fixed-archive.md` BUG-023.

### Full Editor's "never touches the DB" rule gets one confirmed exception, for review-queue saves only

**Decided:** 2026-07-15, review-queue feature build session (v2.6 Item 8).

**Why:** `EDITOR_SPEC.md` §5 deliberately built the Full Editor to never touch
the DB or trigger a rescan on save — a considered call, not an oversight,
since it's designed around pre-library files that have no `Issue` row yet.
The new "Send to Full Editor" action (part of the review-queue feature)
breaks that assumption for the first time: it sends *already-catalogued*
issues into the same working set. Without a rescan, saving one there would
leave the DB showing stale field values against the rewritten archive —
exactly the staleness problem the Basic Editor's "read live XML, not DB"
design already exists to avoid, just reintroduced through a new door.

Rather than leave this gap, `process_batch()` now looks up
`Issue.file_path` against the pre-rewrite path after every successful save;
a match triggers the same `scan_single_file` rescan the Basic Editor's save
path already uses, plus clears the review flag. **Scoped narrowly:** this
only fires when the path is already a known Issue — a file added via the
Full Editor's normal pre-library folder-browse picker has no matching row
and is completely untouched, so the original, still-primary Full Editor
workflow keeps its original "never touches the DB" guarantee unchanged.

**Where:** `backend/routers/editor_full.py` (`process_batch()`'s DB-sync
block, module docstring updated to note the exception), `EDITOR_SPEC.md`
§13.5.

### Legacy raw-CSV credit columns: dropped only the 4 confirmed-dead ones, not all 6

**Decided:** 2026-07-15, executing `ROADMAP.md`'s deferred "Drop the old raw CSV
credit columns" item.

**The existing docs were wrong.** `ROADMAP.md`/`SPEC.md` described all 6 columns
(`writer`/`penciller`/`inker`/`colorist`/`letterer`/`cover_artist`) as "written by
the scanner but no longer read" since the June 2026 Writer/Artist dedup — implying
a safe, mechanical drop. Traced every usage in `backend/` and
`frontend/js/app.js` before touching anything and found that's only true for 4 of
the 6. `writer`/`penciller` are still genuinely read server-side, powering three
things live in the UI today: the library search box (`path_utils.matches_search()`),
"Group by Writer" (`#groupBySelect`, confirmed still present), and the series-card
meta line (`library.py`'s per-series `writers`/`artists` aggregate). Only
`_issue_to_dict()`'s dead JSON serialization and the already-migrated Issue Detail
credit links (on `people`/`issue_credits`) matched the "no longer read" claim.

**Why scope down instead of migrating writer/penciller too:** the full fix (rewrite
those 3 live consumers to query `people`/`issue_credits` instead of the raw
columns, add eager-loading to avoid reintroducing the N+1 class of bug
`v2.6 Item 2` just fixed, then drop) is real, working code Tez uses daily —
search, grouping, and what he sees under every series card. Tez's explicit call,
given he can't easily verify a backend data-model migration himself: don't touch
anything currently working. Dropped only the 4 confirmed-dead columns this
session (verified against a scratch DB copy, then Tez manually confirmed the real
app). The `writer`/`penciller` migration is real, non-trivial work — folded into
Tez's own already-queued `INBOX.md` "scan code base - clean, removal of dead
code" item as its natural home, a session with room for the testing that
behavior-changing work deserves, rather than being decided in a rush here.

### Advanced Search page and multi-location scanning — ruled out

**Decided:** 2026-07-15, closing out `SPEC.md` §20.14's remaining "deferred"
entries and `ROADMAP.md`'s roadmap.html `Later` lane.

**Advanced Search page:** existing inline filter+search already cover the same
ground a dedicated page would — Tez's call was that building one would add real
code/maintenance for little to no benefit over what's already there.

**Multiple scan locations across drives (+ the bundled series-level overview
field idea):** Tez's own library lives in one location, and both the app and his
own file-organizing workflow are built around that assumption. Considered
generalizing for other users' setups (multi-drive scanning, per-folder excludes)
but judged the complexity not worth it for a single-user tool — if this ever goes
live for others, the expectation is they adapt to a single-location model rather
than the app supporting multiple. The series-level overview field (a free-text
description at the series level) was ruled out separately in the same pass —
per-issue descriptions already cover the need.

### Page background: multiple real covers, not a code-generated gradient

**Decided:** 2026-07-15, reworking `SPEC.md` §20.19 (multi-cover cloud field).

**Context:** Tez likes the random-cover background's "colourful blurred clouds…
alien feel" but the single-cover top-right-corner mask didn't cover enough of
the content area. Before committing to just widening the mask, he asked
whether a code-generated colour effect (no cover image at all) would be a
better/lighter option, expecting memory to be the deciding factor.

**Why real covers, composited, won instead:** checked first, not assumed —
the background already reuses the exact same `/api/cover/{id}` 300px
thumbnail URL the card grid fetches and browser-caches for that page anyway
(`frontend/js/app.js` `setPageBackground()`); nothing extra loads today, and
compositing 3–4 of them changes that not at all (same cached URLs, no new
endpoint, no larger images). So memory was never actually the differentiator
— the real tradeoff was aesthetic. A generated gradient would look
consistent but generic and unrelated to the library; real covers are what
produce the "alien clouds" effect Tez already liked, and using *several* per
page (vs. one) both fixes the coverage complaint and makes the randomness
more pronounced (a new multi-cover palette every surface-entry, not just a
new single hue). Chose: keep real cover art, layer several as soft-masked
blurred blobs spread via zoned-random quadrant anchors (guarantees coverage
without losing per-page randomness) rather than switching to synthetic
colour. See `SPEC.md` §20.19 for the resulting mechanism.

### Full Editor 4-column redesign rebuilt locally, not recovered from the cloud build

**Decided:** 2026-07-14. The Full Editor redesign (v2.6 Item 7) was first built by a
cloud Ultraplan session, but that container had **no git remote** and an **egress
policy that 403-blocks GitHub**, so it could never push or open a PR; the delivered
patch files never reached the PC and their claude.ai URLs are auth-gated (full
context: `temp/build-not-deployed.md`).

**Why rebuild instead of chasing the patches:** the cloud artifacts were stranded in
an ephemeral container, the download path was fragile (auth, a stale base — the cloud
cloned from `origin/main`, which is behind local `main` by the unpushed v2.6 Items
5/6 + a bugfix), and the cloud build was only *mock*-verified anyway. A local rebuild
from the approved plan is guaranteed, durable, builds on the correct current base,
and commits/pushes normally. Tez chose this over the patch route.

### Full Editor Column 1: group the loaded working set as a tree, not a live library browser

**Decided:** 2026-07-14, scoping v2.6 Item 7's Column 1 with Tez.

**Why:** the redesign's Column 1 shows a folder → series → issue tree. Two readings
were possible — (a) keep today's "load files into an in-memory working set" workflow
but *render* that set as a tree, or (b) replace it with a live, on-demand library
browser. Chose (a): it reuses the entire existing intake path (`/browse` +
`/files/add` + `/folders/add`, still behind the `Select Folder` modal picker) and all
downstream state, so the change is a pure presentation reskin with no new backend or
working-set-model risk. Grouping is derived from each file's two nearest directory
levels (grandparent = folder, parent = series), which matches typical
`Publisher|Letter/Series/issue.cbz` layouts without tracking how each file was added.
Drag-reorder of the loaded list was dropped as part of this — ordering has no meaning
in a grouped tree.

### Full Editor viewer: no Rotate control

**Decided:** 2026-07-14. The Claude Design export's viewer toolbar included a rotate
button; Tez dropped it while confirming Item 7 scope ("I missed that and it's not
needed"). Fit + Fullscreen + the lazy thumbnail strip were kept. Recorded so a later
pass doesn't "restore" it from the mock as if it were an oversight.

### Mobile Browse: filter Series/Singles client-side, never via `GET /api/library?group=`

**Decided:** 2026-07-13, root-causing a count mismatch Tez reported (mobile
Browse showed different totals than the web for the same library).

**Why:** `GET /api/library?group=` (`backend/routers/library.py::get_library`)
filters at the *individual issue* level before grouping into series-name
cards — `query.filter(Issue.format_group == group)` runs before the
per-series groupby. For a series where issues don't all share the same
`format_group` (found 8 real cases — e.g. "Nowhere Men", a 12-issue run
with one issue individually tagged `Singles`, likely a special/annual
sharing the series name), `group=Singles` picks up just that one stray
issue and builds a *phantom extra 1-issue card* for it — on top of the
real multi-issue "Series" card the same series already has under
`group=Series` or no group at all. The web app (`frontend/js/app.js`)
never hits this: it fetches the full ungrouped library exactly once and
filters *client-side* by each series-group's own single representative
`format_group` (the cover issue's, chosen by lowest issue number) — a
mixed-tag series always resolves to exactly one card that way. Fixed
`flutter_app/lib/screens/browse_screen.dart` to do the same — fetch
unfiltered, filter by `Series.formatGroup` client-side — rather than
"fixing" the backend's grouping order, since the backend's per-issue
`group=` filter is also used correctly elsewhere (Folder View field/value
scoping, `BUG-010`'s search scoping) where issue-level filtering before
grouping is exactly the intended behaviour. The bug was mobile using the
wrong tool for a series-level distinction, not the backend being wrong.

**Where:** `flutter_app/lib/screens/browse_screen.dart` (`_load()`). Custom
Library tabs still use the backend's `tab_id` param — genuinely
server-scoped (folder/favourites), not a subset of the "All" pool, so
unaffected by this issue.

### Mobile UI Redesign (v2.6 Item 4): `google_fonts` for the Flutter app's Hanken Grotesk requirement

**Decided:** 2026-07-13, before any code was written for the redesign.

**Why:** The design handoff specifies Hanken Grotesk everywhere, same as
the web redesign's Item 1 Phase A. But the Flutter app, unlike the web
app, has real offline-reading functionality (downloaded issues, local CBZ
files) — a runtime font-download dependency is a bigger tradeoff there
than it was for a browser tab. Asked Tez directly rather than assuming:
options were system-default (zero dependency, wrong typeface), bundled
`.ttf` assets (fully offline, but needs someone to supply the font files),
or `google_fonts` (fetches once per device, cached after). Tez chose
`google_fonts` — same call Item 1 Phase A already made for the web app,
kept consistent rather than diverging for the mobile app alone.

**Where:** `flutter_app/pubspec.yaml` (`google_fonts: ^6.2.1`),
`lib/theme/tokens.dart` (`AppText`, `buildAppTheme()`).

### Mobile UI Redesign (v2.6 Item 4): Home strip cards can't show favourite ring or unread-count badge

**Decided:** 2026-07-13, during planning, before building `home_screen.dart`.

**Why:** `GET /api/home/strips` returns issue-level cards
(`backend/routers/home.py::_issue_card`) — each one representing a single
issue (the next-unread issue of a series, the most-recently-added issue,
etc.), not the series itself. That endpoint's card shape has no
`favorites` or `unread_count` field at all; only `GET /api/library`'s
series-level cards (used by Browse) carry those. Rather than adding new
backend fields or aggregating client-side from partial data, left Home
strip cards without the favourite-gold-ring and blue-unread-badge
treatments the design mockup shows on every card uniformly — those
treatments only render on Browse, where the underlying data actually
supports them. A real, disclosed scope gap, not a silent omission.

**Where:** `lib/screens/home_screen.dart` (`_StripRow._cardFor`) vs.
`lib/screens/browse_screen.dart` (`_BrowseScreenState._cardFor`).

### Mobile UI Redesign (v2.6 Item 4): dropped the manual "sync now" button

**Decided:** 2026-07-13, while replacing `LibraryScreen`'s app bar with the
new rail-based Home/Browse headers.

**Why:** The old `LibraryScreen` had a manual sync icon + spinner + result
snackbar in its app bar (`mobile-server-sync-scope.md`'s sync feature,
built v2.5 Item 3). The new design spec's Home/Browse headers only show
`⌕`/`⚙` — no sync control anywhere in the reference. Rather than force it
in against the design, dropped it: background sync (`SyncService.syncNow()`)
still fires automatically on load and on return-from-reader
(`ShellScreen._checkAndLoad()`, same trigger `LibraryScreen.didPopNext()`
used), so the underlying capability isn't lost, just its manual trigger and
status feedback. Flagged to Tez as a disclosed removal rather than
silently dropped; can be re-added (e.g. as a rail action) if it's missed.

**Where:** `lib/screens/shell_screen.dart` (`_checkAndLoad`) vs. the old
`lib/screens/library_screen.dart`'s `_syncNowManual`/`_lastSyncedLabel`
(removed).

### Mobile UI Redesign (v2.6 Item 4): a tapped single goes straight to Issue Detail, never a "series of one" page

**Decided:** 2026-07-13, while wiring up card taps in
`home_screen.dart`/`browse_screen.dart`.

**Why:** The design mockup's `CoverCard.onClick` is opaque (`{{ item.open }}`
in the prototype HTML) — it doesn't show the branching logic. Existing
Flutter behaviour before this redesign always routed through `/series`
regardless of format, showing a "series" page with exactly one issue row
for a single. The new design has a genuinely distinct Issue Detail page
(cover, credits, rating stars, prev/next) that a single format has no
reason to sit behind an extra tap for. Used the existing
`Series.formatGroup`/`Issue.formatGroup` field (`'Singles'` vs `'Series'`)
already present in both API responses to branch directly: `'Singles'` →
`/issue`, else → `/series`. Matches how the "Single"/"Series" type pill on
Issue Detail's own header already frames the distinction.

**Where:** `lib/screens/home_screen.dart` (`_StripRow._cardFor`'s `onTap`),
`lib/screens/browse_screen.dart` (`_BrowseScreenState._cardFor`'s `onTap`).

### Tray icon base glyph: reuse `favicon.png` (digib00age mark), visual-only exception to the 2026-07-07 tray-app-stays-ComicVault scope

**Decided:** 2026-07-13, from an `INBOX.md` item ("replace taskbar icon with
icon-oo.png - keep current green dot for server running, red for stopped").

**Why:** `icon-oo.png` (and the identical `logo1.png`) turned out to be a
166×100 horizontal logo lockup, not a square icon — pulled into
`frontend/images/` generically during the v2.6 Design redesign (commit
`77a0dc0`, 2026-07-12) with no tray-specific intent, and unusable as a small
square tray glyph without cropping. `favicon.png` (136×127, RGBA, transparent
background around a solid blue rounded-square "oo" mark) is square-shaped and
already used as the web favicon, making it the only existing asset that
actually fits. Tez confirmed reuse after being flagged that this cuts against
`SPEC.md` Section 1's 2026-07-07 note that the tray app stays outside the
v2.6 digib00age rebrand — resolved as a **narrow, visual-only exception**:
the tray app's process name, window/menu text, and log strings all stay
"ComicVault" (unchanged); only the icon's base artwork now reuses the
digib00age mark. The existing status-dot mechanism (`tray/tray_app.py`
`make_icon_image()` — 3 states, green/amber/red, bottom-right corner,
code-drawn via Pillow) was kept exactly as-is; only the base glyph
underneath it changed, from a purple book-shape to the favicon image
(loaded once via `_load_base_icon()`, cached in `_base_icon_cache`, composited
fresh per call — same per-call cost profile as the previous fully
programmatic draw).

**Where:** `tray/tray_app.py` (`FAVICON_PATH`, `_load_base_icon()`,
`make_icon_image()`).

### Full Editor page-preview: fix the page-list N+1, leave full-res/base64 encoding alone

**Decided:** 2026-07-13, during v2.6 Item 2 Phase 5 (Performance fixes).

**Why:** Finding #6 in `PERFORMANCE.md`'s baseline (never actually measured
until this session — admin-auth-gated) turned out to have two distinct
costs once measured live: an archive re-parse-per-call N+1 (same root
cause as findings #4/#5) and a full-resolution, base64-encoded, uncached
image payload (up to 3.7MB per page on a large compendium). Fixing the
first is the same low-risk, already-proven pattern as Phase 3. Fixing the
second would mean downscaling preview images and/or caching encoded page
bytes — a bigger change that touches editor image quality, a UX tradeoff
worth its own discussion rather than folding into a performance-fix pass.
Chose to fix only the N+1 this session and leave the encoding cost as a
documented, flagged follow-up in `PERFORMANCE.md` finding #6.

### Claude Code as master controller; Cowork's scan cancellation confirmed permanent

**Decided:** 2026-07-12, same session as the `docs/` junction removal, as a
follow-up once Tez confirmed the nightly scan wasn't coming back.

**Why:** The project used to split process across three tools — Chat for
planning/triage, Cowork for nightly doc drift-scanning, Design for UI
mockups — with Code building whatever the others had scoped. Tez confirmed
the nightly scan was cancelled for good (not paused pending a replacement),
and clarified the bigger picture: Code is now the master controller for
everything — planning, triage, build, docs — with one exception: outside
planning docs (a Design mockup, notes from a Chat conversation) still get
dropped into the repo as reference material when they exist, just not as a
required upstream stage Code waits on. Two things now cover what the old
three-way split covered: a `SessionEnd` hook (personal, cross-project
conversational summary, outside this repo) and this project's own doc set
(`progress.md`/`CHANGELOG.md`/`DECISIONS.md`), which were already how
substance got tracked — only the scan and the presumption of a separate
Chat-run triage stage go away. Documented in
`docs/meta/working-rules.md` "Master controller" and reflected in
`CLAUDE.md` Sections 2, 4, and 5.

### Retire Cowork's nightly doc-scan rather than reconfigure it

**Decided:** 2026-07-12, while removing the `docs/` Google Drive junction.

**Why:** Cowork's nightly drift-scan (`doc-scan-issues.md`, `doc-scan-state.md`,
`cowork-doc-scan-instructions.md`) depended entirely on Cowork having live Drive
access to `docs/` via that junction. Tez no longer wants Google Drive in the
loop, which removes the scan's only access path. Asked Tez whether to retire
the workflow outright or leave the docs alone pending a separate
Cowork-side reconfiguration (e.g. pointed at GitHub instead) — **chose
retire**: no replacement mechanism assumed or half-built. The three
scan-specific files moved to `docs/archive/` as point-in-time records rather
than being deleted, in case a future drift-checking mechanism gets built and
wants the prior instructions as a reference.

### Basic Editor async save: silent failure after navigating away is acceptable

**Decided:** 2026-07-11, scoping the Basic Editor's async-save fix (`INBOX.md`
"[feature] to scope... quick save hits a bottleneck").

**Why:** Making the save "fire and forget" (close the modal immediately,
finish the archive rebuild + rescan in the background) means the user can
navigate away before the rebuild completes. If it then fails — rare: disk
full, permission error, a locked file — there's no in-app mechanism to tell
them once they've left the page, short of building a new persistent
cross-page notification system (localStorage-tracked pending saves + a
poll-on-load indicator visible from any page). Asked Tez directly rather
than assuming either way: confirmed a silent failure is acceptable — a
toast only while still on the issue page, nothing otherwise. Discoverable
by reopening the Basic Editor on that issue and noticing the edit didn't
take (the field values come from the live file, so a failed save just
reads back as the pre-edit values). This is safe to accept because the
archive rewrite can't half-fail into a corrupted file: `_rebuild_archive()`
(`backend/editor/archive_io.py`) stages the new zip fully before an atomic
`os.replace()` — a failure at any point up to that swap leaves the original
file completely untouched.

**Where:** `EDITOR_SPEC.md` §6.1 Change Log (2026-07-11), `docs/v2.6/progress.md`.

### Small/cosmetic UI changes don't need the full process

**Decided:** 2026-07-08, in a Chat session, formalizing a threshold that had been
discussed verbally but not written down anywhere Code or Cowork would see it.

**Why:** The full process (scope in Chat, track as a build-queue item or bug,
Design→Code handoff, `DECISIONS.md` entry) exists to keep structural changes —
navigation, routing, information architecture — deliberate and reviewable, since
those are the changes with the widest blast radius. Applying that same weight to
purely cosmetic tweaks (colour, spacing, typography, copy, element position/sizing
within an existing layout) adds process friction with no corresponding benefit, and
risks Code either skipping the "required" steps informally (silent drift from the
documented process) or over-processing trivial changes. Splitting the two
explicitly avoids both failure modes. This decision itself is the kind of
non-obvious judgment call this log exists for; the threshold's mechanics live in
`CLAUDE.md` Section 5 and `docs/meta/working-rules.md` rather than being restated
here.

**Where:** `CLAUDE.md` Section 5 ("Doc-update threshold"), `docs/meta/working-rules.md`
("Structural vs. cosmetic threshold").

### v2.6 Item 1 Phase E: Issue backdrop doesn't extend behind the "← Back" button

**Decided:** 2026-07-08, while building the new Issue detail backdrop.

**Why:** Design's `IssueScreen` renders the backdrop as the first element
inside the page, with the back button and everything else sitting in a
`position:relative; z-index:1` wrapper on top of it — so the backdrop
visually extends behind the back button too. The real app's back button
(`#backLink`) is static markup in `issue.html`, a DOM sibling *before*
`#issueContent` (not something `buildIssueDetail()` builds, and not
something any other Phase E work touched) — matching Design exactly here
would mean restructuring `issue.html`'s static layout for a purely
cosmetic few pixels of overlap, a different and riskier class of change
than the contained `app.js`/`style.css` edits everything else in this
phase used. Kept the backdrop scoped to `#issueContent` (started with
`position: relative` on that container) — it starts just below the back
button instead of behind it. Flagging this explicitly rather than either
silently shipping the visual gap unmentioned or scope-creeping into static
markup for a nicety nobody asked for.

**Where:** `frontend/js/app.js` (`buildIssueDetail()`), `frontend/css/
style.css` (`#issueContent`, `.issue-backdrop`).

### v2.6 Item 1 Phase D: kept native `<select>` filter dropdowns, didn't rebuild as Design's custom popup component

**Decided:** 2026-07-07, while building Phase D (Browse filter/sort bar
restyle), before writing any code.

**Why:** Reading `screens.jsx` and the compiled `_ds_bundle.js` directly
(rather than working from the prior session's textual description) showed
that Design's filter dropdowns aren't styled native `<select>` elements —
`FilterSelect` renders a fully custom-built popup listbox
(`components/library/Dropdown.jsx`): its own open/close React state,
click-outside-to-close, Escape-to-close, and a themed `.ds-dropdown-panel`
for the open option list. Matching that exactly would mean building a new
interactive JS component from scratch, not restyling an existing one — a
different class of work than the "visual restyle only" scope already
settled for this phase, and not something that can be done through CSS
alone on a native `<select>` (the browser owns the open-state popup
rendering). Kept the real app's native `<select>` elements and applied only
`.ds-filter`'s closed-trigger styling (borderless, muted text, hover/focus
colour change) — the part that's actually visible and comparable to Design
side-by-side. The open dropdown list still uses the browser's native
popup, unstyled, same as before this phase.

**Where:** `frontend/css/style.css` (`.filter-select`), `frontend/index.html`
(`#menuBar`'s `<select>` elements, unchanged markup).

**Reversed same day, later this session** — Tez shared a screenshot of the
open Genre dropdown asking for the open-menu styling specifically, which is
exactly the piece this decision had ruled out. See the next entry below
(sync mechanism) and `v2.6/progress.md` "Phase D follow-up built" — the
custom listbox got built after all, once it was explicitly requested rather
than assumed out of scope. This entry is kept as-is (not deleted) since the
reasoning for the original call is still valid context — "restyle only"
was the correct read of the request *at the time*.

### v2.6 Item 1 Phase D follow-up: hidden native `<select>` + `Object.defineProperty`/`MutationObserver` sync, not a full replacement

**Decided:** 2026-07-07, while building the styled open-dropdown panel
(reversing the "kept native select" call above).

**Why:** `app.js` reads and writes the 10 `.filter-select` elements three
ways that all had to keep working with zero changes to `app.js` itself:
`change` listeners (the real filter logic), **programmatic** `.value =`
in a couple of places (`clearAllFilters()`, sort's "Pages"-option
suppression — neither of which fires a native `change` event), and
dynamically-rebuilt option lists for Genre/Format/Decade/Year/Publisher/
Rating (populated from live library data via `addOpts()`, not static
HTML). Fully replacing the `<select>` with a custom widget (as Design's
own React `Dropdown` component does) would have meant either touching
every one of those `app.js` call sites, or reimplementing a `.value`-like
interface from scratch. Instead: kept the real `<select>` in the DOM,
hidden but otherwise untouched, as the sole source of truth, and built a
custom trigger+panel purely as a visual/interaction layer on top of it —
`Object.defineProperty` on the select's `value` accessor catches
programmatic sets (which don't fire `change`), and a `MutationObserver` on
the `class`/`hidden` attributes keeps the trigger's active-state and
visibility in sync regardless of the order `app.js` happens to touch them
in (e.g. `clearAllFilters()` sets `.value` and removes `.active` as two
separate statements). Rejected deriving "active" styling from a blanket
`select.value !== ''` — tried first, but wrongly made `sortSelect` (always
has a real value, never gets `.active` toggled by `app.js`) permanently
accent-coloured; mirroring the select's own real `.active` class instead
matches original behaviour exactly, including for the two elements
(`sortSelect`, `groupBySelect`) `app.js` never marks active at all.

**Where:** new `frontend/js/filterDropdown.js`; `frontend/css/style.css`
(`.fd-wrap`/`.fd-panel`/`.fd-opt`/`.fd-trigger`); `frontend/index.html`
(one new `<script>` tag). No `app.js` changes.

### v2.6 Item 1 Phase C2b: ct_autotag_log.md becomes standalone-capable (`auto` param)

**Decided:** 2026-07-07, while building the new XML Tagging tool.

**Why:** `ct_autotag_log.py`'s `append_entry()` unconditionally hardcoded the
`[AUTO]` prefix, and its own docstring stated CT Auto-Tag "only ever runs...
never as a standalone admin-UI tool" — true when written, no longer true once
XML Tagging exists as a manual, one-folder-at-a-time trigger for the same
underlying `ct_autotag_file()` call. Rather than start a second log file for
manual runs (would split one tool's history across two files for no reason),
added the same `auto: bool = False` parameter `convert_log.py`/
`convert_images_log.py` already use, and updated `processing_folder.py`'s one
call site to pass `auto=True` explicitly. Verified post-build: a real XML
Tagging run against a scratch file produced a non-`[AUTO]` line sitting
directly below pre-existing `[AUTO]` lines from real automation runs, in the
same file, with no cross-contamination.

**Where:** `backend/ct_autotag_log.py`, `backend/routers/processing_folder.py`
(`_run_ct_autotag_stage()`), `docs/ADMIN_SPEC.md` §11.4.9/§11.6.3.

### v2.6 Item 1 Phase C2a: Genre List / Format List unlocked, rest of Advanced Settings stays locked

**Decided:** 2026-07-07, before building Phase C2a (Admin IA restructure, part 2).

**Why:** Same reasoning as Phase C1's Home Page Strips/Libraries decision below.
Genre List and Format List used to live inside `<fieldset id="advancedFields"
disabled>` alongside Password Protection, Server Port, and the old "Danger
Zone" subsection. The new Admin IA moves them into their own **Editor
Options** category, distinct from **Advanced Settings** — keeping the lock
would mean the unlock checkbox lives in a different part of the nav than the
content it gates. Matches `New Admin Layout.md`'s own category split (Editor
Options is a separate top-level section from Advanced Settings). The
remaining four sub-items (Password Protection, Change Server Port + Reader
Location, Wipe Database, Wipe Reading State) **stay locked** — they weren't
reclassified, they're still Advanced Settings, so the existing gate continues
to make sense there and wasn't relitigated.

**Also decided this session:** the old single "Danger Zone" subsection
(Clear Reading Progress + Clear Database together under one heading) splits
into two independent sub-items, **Wipe Database** and **Wipe Reading State**,
matching `New Admin Layout.md`'s own two-item list — same buttons/IDs, just
no longer grouped under one shared heading.

**Where:** `frontend/admin.html` (Genre List / Format List blocks moved out
of `#advancedFields`; Danger Zone split into two `.admin-content-block`s),
`docs/ADMIN_SPEC.md` §7.

### v2.6 Item 1 Phase C2: Processing Tools mapping corrected — XML Tagging is new functionality, not a relocation

**Decided:** 2026-07-07, during Phase C2 planning, before Phase C2a was built.

**Why:** The Phase C1 plan had guessed Processing Tools' 5 sub-items were all
relocations of existing sections. New reference material (`admin2.PNG`,
`New Admin Layout.md` — the actual source doc `admin.jsx`'s categories were
built from, on Google Drive outside the `docs/` junction — and 3 CAPT-era
PDFs) showed a **XML Tagging** sub-item with no existing-section match. Tez
confirmed: it's a genuinely new standalone tool (own folder picker + Run),
not just a settings relocation, and the reference doc/PDFs had mistakenly
dropped CT Auto-Tag from Auto Processing entirely — Auto Processing actually
keeps its CT Auto-Tag enable checkbox; only the *detailed* settings (Match
Ratio Threshold, Save on Low Confidence, ComicVine API Key) move to the new
XML Tagging pane, reading/writing the same shared config fields. This pushed
Processing Tools out of Phase C2a (no backend work) into its own session,
Phase C2b, and settled that all 5 Processing Tools sub-items ship together
atomically in C2b rather than split further — removing Auto Processing's CT
settings fields before XML Tagging exists to receive them would leave the
ComicVine API key/threshold/save-low-confidence genuinely inaccessible in the
UI for however long the gap lasted, a real regression, not just cosmetic.

**Where:** `docs/v2.6/comicvault-changes-v2.6.md` Phase C2a/C2b split,
`docs/ADMIN_SPEC.md` §11 (pending Phase C2b build).

### v2.6 Item 1: "Libraries" is UI copy only — "Custom Tabs" stays the internal/spec name

**Decided:** 2026-07-07, during Phase B (left sidebar nav) — resolving the open
question raised the day before in `comicvault-changes-v2.6.md` Item 1 ("does
this rename ripple into `CUSTOM_TABS_SPEC.md`'s own terminology, or does the
spec keep 'Custom Tabs' as the internal/technical name while the UI surfaces
'Libraries'?").

**Why:** The Design reference renames the sidebar section "Libraries" and drops
the old "Custom Tabs" label entirely from anything user-facing. But the
underlying feature — `custom_tabs` table, `CustomTab` model, `/api/admin/
custom-tabs` endpoints, `loadCustomTabsNav()`, `CUSTOM_TABS_SPEC.md` itself —
has no reason to be renamed: it's the same code, same data model, same admin
workflow, just relabelled where a user actually sees it. Treating this as a
pure UI-copy change avoids a rename sweep across the backend, the spec, and
every code comment for a change that's cosmetic everywhere except the sidebar
label. Same pattern already used for the **digib00age** brand rename
(ComicVault stays the internal/codebase name) — visible-copy renames don't
automatically become internal renames unless there's a reason beyond "the
mockup says so."

**Where:** `frontend/js/app.js` (`loadCustomTabsNav()` renders into the
sidebar's "Libraries" section — Change Log entry, `CUSTOM_TABS_SPEC.md` §5.2),
`docs/CUSTOM_TABS_SPEC.md` (feature name, data model, and internal references
all unchanged).

### v2.6 Item 1 Phase C1: Home Page Strips / Add-Remove Libraries — unlock them

**Decided:** 2026-07-07, before building Phase C1 (Admin IA restructure).

**Why:** Home Page Strips and Custom Tabs ("Add/Remove Libraries") used to live
inside `<fieldset id="advancedFields" disabled>`, gated behind the "Unlock
advanced settings" checkbox, alongside Password Protection, Server Port, and
Danger Zone. The new Admin IA moves them into their own **Library Appearance**
category, separate from **Advanced Settings** — keeping the lock would mean the
checkbox that unlocks them lives in a completely different part of the nav than
the content it unlocks, a confusing UX regression. Asked rather than assumed,
since removing a gate is a real behaviour change, not just a visual one. Tez
confirmed: unlock them. Matches `admin.jsx`'s own `HomeStripsContent`/
`LibrariesContent` — no lock gate at all in the design reference either.
Verified `toggleAdvanced()` (`admin.js`) only does `fieldset.disabled = locked`,
no other JS-level gating tied to these two sections specifically, so moving
their markup outside the fieldset was sufficient — no JS logic changed.

**Where:** `frontend/admin.html` (Home Page Strips / Add-Remove Libraries blocks
moved out of `#advancedFields`), `docs/ADMIN_SPEC.md` §7.

### v2.6 Item 1: Browse filter/sort bar — restyle existing controls, don't drop any

**Decided:** 2026-07-07, resolving the open question raised the same day in
`comicvault-changes-v2.6.md` Phase D.

**Why:** The Design reference's `BrowseScreen` filter bar is missing several
controls the real app already has and uses — `Group by`, a separate `Year`
filter alongside `Decade`, a separate `Rated` (personal star rating) dropdown,
and the `Clear` button. Tez confirmed this is **not** a deliberate scope cut —
Claude Design was working from an incomplete snapshot of the app's own files,
so later-added fields never made it into what Design saw, and the mockup
simply doesn't know they exist. Contrast with Phase B's status-pill removal,
which *was* confirmed deliberate after checking directly — this is the other
outcome of asking the same class of question, not a rule that Design always
wins. **Phase D scope, going forward:** every current field/control stays —
this is purely a visual restyle (borderless/minimal control styling, hover/
active states, spacing) applied to the existing full control set, not a
functional reduction to match the mockup's control count.

**Lesson for future phases (C, E):** don't assume a control's absence from a
Design mockup means "remove it" — check whether Design had visibility into
that control's current-app existence at all before treating an omission as
a decision. Ask, as this session did, rather than build either extreme
(silently dropping working features, or silently ignoring the design intent)
on an assumption.

### Mobile Sync: build the download-for-offline feature rather than a filename heuristic or a deferral

**Decided:** 2026-07-05, during v2.5 Item 3 scoping, before any code.

**Why:** `mobile-server-sync-scope.md` (the Cowork discovery-session doc) scoped
sync assuming the tablet already had a way to have "comics downloaded for a
trip" tied to a server `issue_id`. Reading the actual Flutter code showed this
didn't exist — the app's only local-file mode opens arbitrary CBZs copied onto
the device manually or via Android "Open With," tracked by file path only,
with no timestamp and no link to any `issue_id`. Without that link there was
nothing concrete for a sync feature to act on. Considered three options:
build a real download feature (bigger scope than the doc anticipated, but the
only way to actually deliver the doc's own scenario); guess the `issue_id` by
matching the local file's name against the library (cheap, but a wrong match
could silently push progress onto the wrong comic); or descope entirely and
treat download as a separate future item. Tez chose the first — worth
recording since it's a meaningfully bigger build than the original scope doc
implied, and a future reader shouldn't assume the smaller scope was what
shipped.

**Where:** `flutter_app/lib/services/download_service.dart`,
`backend/routers/reader.py`'s `download_issue`.

### Mobile Sync: last-write-wins by timestamp, not highest-page-wins

**Decided:** 2026-07-05, confirming the scope doc's flagged-but-unconfirmed
default.

**Why:** The scope doc named this as needing eng review before it could be
locked in. Highest-page-wins is simpler (progress never silently moves
backward) but would block a deliberate rewind/re-read from ever taking effect
once synced — the scope doc explicitly wanted that case supported. Tez
confirmed last-write-wins by timestamp over highest-page-wins.

**Where:** `backend/routers/sync.py`'s `sync_progress()` conflict comparison.

### Sort by Filename: "existing folder with different file" collision means unrelated content, not just an exact-path clash

**Decided:** 2026-07-05, during the build session, found via direct scratch-folder
testing before the manual UI pass.

**Why:** The build brief's literal wording — "existing-folder-with-different-file-in-it
collision → explicit check before move, fail that single file with a clear reason
rather than silently overwriting" — reads two ways: (a) fail only when the exact
destination path (`folder\filename`) is already occupied, or (b) fail whenever the
target folder already exists and contains *anything* that isn't this file's own
sibling. The first pass implemented (a), since it was the simpler/more literal
reading and matched every other Processing Tool's existing collision-guard shape
(`rename_tool.py`'s `rename_files()`, `archive_convert.py`'s backup-exists check).
A scratch test built specifically to exercise the named edge cases caught the gap
immediately: a folder pre-populated with an unrelated file let the new file move in
without complaint, since its own destination path was still free — silently mixing
unrelated content into an already-organized folder, exactly what the edge case was
supposed to prevent. Reading (b) is what the spec actually intended. Fixed by
checking, before any move, whether the target folder already exists and holds an
entry whose own basename differs from the folder's name — same-basename siblings
(a CBZ+CBR pair) are still allowed through unchanged, since that's the explicitly
un-concerning case named right next to this one in the same brief.

**Where:** `backend/filename_sort.py`'s `_conflicting_existing_entry()`,
`ADMIN_SPEC.md` §11.5.3.

### BUG-017 fix scoped to .cbz only, not .cbr

**Decided:** 2026-07-05, before building the Android file-association fix.

**Why:** The bug was originally logged covering both `.cbz`/`.cbr`, but
`LocalCbzService` (`flutter_app/lib/services/local_cbz_service.dart`) decodes
exclusively via `ZipDecoder()` — there is no RAR support anywhere in the
Flutter app. Associating `.cbr` in the Android manifest would have put
ComicVault in the "Open With" list for a format it can't actually read,
which just trades "no app can open this" for a different, equally unhelpful
failure once tapped.

**Decision:** intent-filters registered for `.cbz` only. `.cbr` stays
unassociated — exactly as unopenable as before, no regression introduced.

**How to apply:** if CBR reading support is ever added to the Flutter reader,
revisit extending the same intent-filter/`resolveSharedUri` mechanism to
`.cbr` — the plumbing (native URI resolution, `_handleLink` routing) would
carry over unchanged; only the manifest's MIME-type/pathPattern list and the
archive-decoding side would need to grow.

### Flutter's `shouldHandleDeeplinking()` disabled to fix a route-push crash found during BUG-017 testing

**Decided:** 2026-07-05, mid-session, after live testing on Tez's tablet
surfaced a crash the plan hadn't anticipated.

**Why:** `FlutterActivity`'s default Android embedding behaviour
auto-converts any incoming `ACTION_VIEW` intent into a raw
`Navigator.pushNamed()` call using the intent URI's literal path as the
route name — this happens *before* the `app_links` package's own
`uriLinkStream` (what `main.dart`'s `_handleLink` listens on) ever sees the
intent. A path like `/storage/emulated/0/Download/foo.cbz` isn't a
registered route, so this crashed with "Could not find a generator for
route" and silently swallowed the intent — meaning the manifest change
alone would have gotten ComicVault into the Open With list, but tapping it
would have crashed rather than opened anything. Confirmed via `adb logcat`
against a plain installed APK first (no visible crash in that log, wrongly
suggesting no problem), then conclusively by attaching `flutter run`
directly to the tablet and reading the live Dart exception — the lesson
being that `adb logcat` alone isn't sufficient for diagnosing Dart-level
widget exceptions; a debugger-attached run surfaces them far more reliably.

**Decision:** override `shouldHandleDeeplinking()` to return `false` in
`MainActivity.kt`, leaving `app_links` as the sole path that receives
incoming intents (native `VIEW` intent handling, not anything specific to
CBZ files).

**How to apply:** this affects *all* incoming `VIEW` intents to this app,
including the pre-existing `comicvault://read/{id}` deep link — worth
knowing if a future deep-linking change behaves unexpectedly, since Flutter's
own automatic route-push is now deliberately off, not just quietly present.

### OPDS / 3rd-party reader connectivity ruled out — continue Flutter app development instead

**Decided:** 2026-07-04, first scoping session for the v2.5 "OPDS" holding-list item.

**Why:** Research carried out ahead of/during scoping found CDisplayEx (the
target reader, Android tablet) doesn't support OPDS at all — it only connects to
Komga or Kavita via their own proprietary, undocumented REST APIs. So "add OPDS"
as originally conceived wouldn't have delivered CDisplayEx support anyway; the
only path would have been reverse-engineering and maintaining a Komga-API-shim
against another project's private, unstable surface — a materially different
and riskier build than a standards-based OPDS server.

Tez's own stated reasoning tipped it beyond just the CDisplayEx-specific
mismatch: this is a single-connection use case (his own tablet), so building and
maintaining a generic reader-compatibility layer isn't worth the effort even
before the CDisplayEx finding. He also raised the possibility of ComicVault
going public eventually, and concluded that if it does, maintaining ComicVault's
own client apps will be easier than supporting third-party readers whose
behaviour/versions/API expectations he can't control — i.e. this isn't just
"not worth it now," it's "not worth it even in the public-release scenario that
would otherwise be the strongest argument for it."

**Decision:** no OPDS server, no Komga-API-compatibility shim. Development effort
goes into the existing Flutter app instead — which turns out to need it anyway
(see BUG-019/BUG-020, surfaced in this same session: the Flutter app currently
fails to connect to the server and crashes when selecting a CBZ on the tablet).

**How to apply:** if third-party reader connectivity comes up again later
(e.g. a different target reader that does speak real OPDS), this decision
doesn't rule that out categorically — it rules out this specific
CDisplayEx-driven path. Re-scope fresh against whatever reader/use-case is
actually being asked for rather than reviving this research wholesale.

### CT Auto-Tag's "N of M succeeded" summary needed its own outcome breakdown, not a status-semantics change

**Decided:** 2026-07-04, diagnosing a misleading result reported during Tez's
low-confidence real-world test (5 files, 4 tagged, 1 correctly no-matched,
reported as "5 of 5 succeeded").

**Why:** `ct_autotag_file()` correctly returns `success=True` for a `no_match` or
a skipped-low-confidence outcome — deciding not to tag a file is a legitimate,
intentional result (per ADMIN_SPEC.md §11.4.3's "distinct from low confidence"
framing), not an error, so `success=False` would be the wrong signal to reuse
here. The bug wasn't in that status value — it was that
`pollPfStatus()`'s run-complete summary (`frontend/js/processingTools.js`)
reused Convert Archives/Images' generic `results.filter(r => r.status !==
'failed').length` framing for every stage, which fits a simple two-outcome
model (converted vs. failed) but silently swallows CT Auto-Tag's real
four-outcome model (tagged confident / tagged low-confidence / correctly
skipped / failed) into a misleading two-bucket "succeeded/failed" count. The
underlying `ct_autotag_log.md` audit log was accurate throughout — this was a
UI rollup-message bug only, not a data-integrity issue.

**How to apply:** Don't "fix" this by changing `ct_autotag_file()`'s
`success`/`status` semantics to make `no_match` count as something other than
success — that would break the correct, already-established design. Instead,
any stage whose outcome model doesn't fit the simple succeeded-vs-failed
framing needs its own summary branch in `pollPfStatus()`, using the per-file
result fields already available (`tags_written`, `confidence`) rather than
the generic `status` field alone. `ADMIN_SPEC.md` §11.4.4/§11.4.9 and
`v2.5/progress.md`'s 2026-07-04 close-of-session entry have the full detail.

### ComicTagger integration — field mapping expanded to capture everything CT/ComicVine supplies, not just editor-exposed fields

**Decided:** 2026-07-04, during Tez's live testing of v2.5 Item 1's build.

**Why:** The build's `metadata_to_field_dict()` (`backend/ct_bridge.py`) originally
only mapped the subset of ComicInfo.xml fields ComicVault's own Basic/Full Editor
UI exposes (Series, Number, Title, Year, Summary, Publisher, Count, StoryArc,
Language, Writer, Penciller) — a judgment call made during the build, not confirmed
with Tez in advance. Live testing surfaced this as real data loss: Tez compared a
ComicVault-tagged file against the same file tagged by his standalone ComicTagger
1.5.5 and found Month, Day, Notes, Inker, Colorist, Letterer, and CoverArtist all
missing. His stated intent: "pull it all... just save the current fields to the db
and display them in the library" — i.e. capture everything CT/ComicVine supplies
into the archive's XML, even fields ComicVault's own UI doesn't display, matching
what a proper auto-tagging tool does. Fixed by reading
`comicapi/tags/comicrack.py`'s own write mapping directly and mirroring it
field-for-field, rather than continuing to guess at scope.

**Genre/Format/AgeRating/BlackAndWhite stay excluded — confirmed as a different
category, not swept up in this reversal.** These were never a "the editor doesn't
show it" exclusion like the fields above — Genre/Format/AgeRating are
ComicVault-enforced dropdown fields with a validation gate (`EDITOR_SPEC.md` §4.4);
ComicVine doesn't reliably supply values matching that vocabulary (confirmed
2026-07-03 that `md.genres` is never even set by ComicVine's own issue mapper).
BlackAndWhite has a real semantic-correctness problem: ComicVault's convention is
the literal text `"on"` for checked (`EDITOR_SPEC.md` §3.3), while CT's own writer
uses `"Yes"` — writing CT's value would silently fail to register as checked
anywhere the Editor reads this tag.

A second, related bug surfaced in the same testing pass: ComicVine's `description`
field is raw HTML, and CT's own pipeline runs it through
`comictalker.talker_utils.cleanup_html()` (BeautifulSoup-based) before ever writing
it to `Summary` — this call was missing, so raw markup was landing as literal
escaped text (`&lt;p&gt;&lt;em&gt;...`) instead of clean plain text.

**How to apply:** `backend/ct_bridge.py`'s `metadata_to_field_dict()` now maps
Series, Number, Count, Title, Volume, Summary (via `cleanup_html()`),
AlternateSeries/Number/Count, StoryArc, SeriesGroup, Publisher, Imprint, Day,
Month, Year, Language, Web, Manga, Characters, Teams, Locations, Notes
(self-generated, mirroring CT's own "Tagged with..." convention), and all seven
credit-role fields (Writer/Penciller/Inker/Colorist/Letterer/CoverArtist/Editor) —
Genre/Format/AgeRating/BlackAndWhite/PageCount remain the only exclusions. Written
into `EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4's Change Logs, 2026-07-04 — both
surfaces share this one mapping function, so the fix applies identically to Search
Online and the CT Auto-Tag automation stage.

### ComicTagger integration — identify() needs a filename-parsing fallback, and 80% match thresholds, confirmed after live testing failures

**Decided:** 2026-07-04, diagnosing two consecutive failed live tests of v2.5
Item 1's CT Auto-Tag stage.

**Why:** Tez's first real test — a file with `ComicInfo.xml` deliberately removed,
run through "Run Now" — came back `[skipped: no match]` in the audit log
immediately (implausibly fast for a real ComicVine search). Diagnosis: `ct_bridge.
identify_file()` only ever seeded its search from `ComicArchive.read_tags("cr")`;
with no embedded XML, `Series`/`Issue#` were both empty and the function
short-circuited before ever calling ComicVine — a gap flagged as an open judgment
call during planning but never actually built or confirmed. Separately, ComicVine
genuinely did have the series (confirmed via direct search), but the real issue
had no explicit number in the filename — a one-shot-style release. Tez's own
standalone ComicTagger successfully tagged the same file using its own
default-on "If no issue number, assume 1" Auto-Tag option, which ComicVault had no
equivalent of.

**How to apply:** `identify_file()` now falls back to `backend/rename_tool.py`'s
`parse_comic_filename()` (the tested, scene-release-tolerant parser — not
`scanner.py`'s weaker one, which was confirmed via direct testing to leave scene
tags unstripped for this exact filename shape) when the archive has no
Series/Issue# embedded, and defaults the issue number to "1" when the filename
itself has none — confirmed with Tez as the right call, matching CT's own default.
Separately, match thresholds (`series_match_search_thresh`/
`series_match_identify_thresh`) were lowered from CT's own CLI defaults of 90/91
to **80**, matching what Tez had already found worked well in his own standalone
ComicTagger testing (`_DEFAULT_IIO_KWARGS`, `backend/ct_bridge.py`) — confirmed
this is still a hardcoded value with no Admin UI to tune it, per the locked spec's
"simpler two-outcome model" framing; revisit if 80% proves too loose in practice
once Tez's low-confidence sample testing (still pending) surfaces false positives.

### ComicTagger dependency pinned to a GitHub commit, not the published PyPI release

**Decided:** 2026-07-03, during v2.5 Item 1's build (Step 1 smoke test).

**Why:** `pip install comictagger` resolves to PyPI's published release
(1.5.5 at the time), which predates the `comictalker` plugin-talker architecture
the entire integration plan was researched and built against (that split only
exists on ComicTagger's `develop` branch — confirmed via `pip show`, RECORD
inspection, and comparing the local research clone's `git describe` output,
`1.6.0-beta.10-45-g0cc9e76`, against 1.5.5's actual installed file layout, which
has no `comictalker` package at all, just a single legacy
`comictaggerlib/comicvinetalker.py`). Installing from an agent-chosen external git
URL tripped Claude Code's auto-mode safety classifier, correctly — this needed
explicit sign-off before proceeding, not a silent workaround.

**How to apply:** `requirements.txt` pins `comictagger` to
`git+https://github.com/comictagger/comictagger.git@0cc9e76f8d45d3ef27bcf2feabb676e124412abf`
— an exact commit, not a branch name, so a fresh install can't drift even if
`develop` moves on. Confirmed with Tez as the right tradeoff over two alternatives:
installing from the local research clone's path (rejected — couples
`requirements.txt` to that exact folder surviving on this one machine, the same
personal-environment coupling this project has deliberately cut elsewhere, e.g.
the `rar.exe` decision below) or rewriting the whole integration against 1.5.5's
older API (rejected — throws away already-completed, verified research, and 1.5.5
lacks the dual rate-limiter split this integration depends on). Revisit once
ComicTagger publishes a PyPI release that includes the `comictalker` split.

### ComicTagger integration — "Save on Low Confidence" toggle and ComicVine key field behaviour locked (session 4)

**Decided:** 2026-07-03, ComicTagger integration scoping session 4 (Chat +
Tez), following up two items introduced under "Processing Folder Automation
addition" that weren't actually in any prior entry.

**Why:**

1. **"Save on Low Confidence" toggle, in §11.4 alongside the CT Auto-Tag
   stage toggle.** Confirmed new — not present in session 1–3 scoping, so
   this is the first time its behaviour is defined, not a recap. **OFF:**
   skip writing tags for a low-confidence CT match entirely — the file
   passes through the stage untagged and unflagged, as if CT Auto-Tag hadn't
   run on it. **ON (default):** unchanged from session 1/2 — write the
   best-guess tags, set `NeedsReview`, let Full Editor's Search Online
   resolve it later. This is deliberately a cheap branch inside the CT
   Auto-Tag stage itself, not a pipeline-flow change — the alternative
   (holding a low-confidence file back from continuing to Convert Images /
   the library) was ruled out on this pass: §11.4 is explicitly
   **folder-level, not per-file chaining** ("Stage 2 simply picks up
   whatever CBZ/CBR files are present... it does not receive an explicit
   list from the previous stage"), so "hold this one file back" would need
   new per-file tracking infrastructure that doesn't exist anywhere in this
   pipeline today. Confirmed not worth building for this.

2. **ComicVine key field gets a "Save & Test" button**, not auto-save and
   not a bare manual Save — the one deliberate exception to this section's
   auto-save convention, justified because CT's own `comicvine.py` already
   ships `check_status()` (hits `team/1/`, detects ComicVine's "Invalid API
   Key" error 100) giving real pass/fail feedback a plain auto-save
   couldn't. Distinct from the Schedule/Time/Day manual-save control
   (`INBOX.md`, deferred to v2.6 as a bug) — that one has no such
   justification and stays logged as an inconsistency to fix; this one does
   the extra step because it earns it.
   **Recommended (not yet asked, low-stakes default):** the button always
   persists whatever's typed to `comicvine_api_key` in `config.json` on
   click, with the test result shown as separate pass/fail feedback rather
   than gating the save — losing a just-typed key because the test call
   itself timed out would be worse than saving a key that later turns out
   to be wrong and is easy to re-edit.

**How to apply:** `ADMIN_SPEC.md` §11.4 needs: the CT Auto-Tag toggle row, the
Save on Low Confidence toggle row (both matching the existing Convert
Archives/Convert Images toggle pattern), and the `comicvine_api_key` field
with its Save & Test button and `check_status()` wiring. **Written up
2026-07-03**, same session — see `EDITOR_SPEC.md` §9 and
`ADMIN_SPEC.md` §11.4. (Correction: the three earlier entries below cite a
"standing hold — nothing goes to Code until reviewed with the §12 CAPT tool
ports" as blocking this. That was wrong — the §12 cluster was already built
and verified before this scoping began; v2.4 closed 2026-07-02. No hold ever
applied to this work; see the correction note at the end of this entry's
neighbours below and `ROADMAP.md`.)

### ComicTagger integration — search/select UI detail locked (session 3); reverses part of session 2's trigger design

**Decided:** 2026-07-03, ComicTagger integration scoping session 3 (Chat +
Tez), working from two CT screenshots (`images/search-online-manual-
selection-from-results.PNG`, `images/series-page-search-issue-list.PNG`) and
`taggerwindow.py`/`issueidentifier.py` read directly.

**Why — this reverses part of the previous entry, not a refinement:**
Session 2 had the `NeedsReview` badge itself as a click-to-open trigger for
the search modal, with a second trigger beside the Series field, and assumed
the badge would reuse §3.5's read-only side-by-side view as its resolution
UI. None of that survives contact with the actual design:

- **Card indicator is now a plain colour-coded border, not a text badge** —
  reuses the existing favourited-card gold-border convention (`SPEC.md`) with
  a different colour/condition, not §3.5's pattern. Purely passive — clicking
  it does nothing beyond the existing unified focus/load mechanic (§5.2); it
  does not open the modal.
- **One global trigger only:** a "Search Online" button in the Full Editor's
  toolbar, next to the existing Admin-cog link (`(log in)` in Tez's original
  note refers to that area's unrelated Allow-Remote-Admin login control, not
  a gate on this button — confirmed, no relation to the ComicVine key).
  Operates on whichever file is currently focused/loaded into the form.
- **Column 1 gains one inline count**, "N Low Confidence," placed after the
  Clear List button in the action row, same text style as the "N File(s)
  Loaded" line but a different line/position — not folded into that count.

**Search field source, verified against CT source rather than assumed:**
Two different CT code paths use different keys — worth being precise since
they don't match:
- Automated Auto-Tag (`issueidentifier.py::identify`) requires **Series and
  Issue #** at minimum ("Not enough info for a search!" if either's blank),
  then uses Year/Publisher/Month/Issue Count to filter and score candidates,
  plus cover-image hashing for confidence. No Title anywhere in the key set.
- Manual Search Online (`taggerwindow.py::query_online`, the function behind
  the ported dialog) only **requires Series** ("Need to enter a series name
  to search" if blank, search stops there) — Issue #, Year, and Issue Count
  are read from the form and passed through to pre-filter/sort results, but
  none of them block the search if empty. **Title is not used in either
  path** — Tez's original assumption included it; confirmed absent from both
  `SearchKeys` (`issueidentifier.py`) and `query_online`'s field reads.

  ComicVault's Search Online button follows the manual-path behaviour: reads
  Series/Issue #/Year/Issue Count directly from the currently-focused file's
  form fields at click time (no separate input, no state duplication),
  blocked with a message if Series is empty (matching CT's own guard).

**Select Series dialog — deliberately trimmed from CT's native version**
(per screenshot): no editable search box, no Re-Search button, no Show
Issues button, no Filter Publishers checkbox — all present in CT's dialog,
all dropped here since the read-from-form behaviour above replaces them (to
retry, edit the Series field in the main form and click Search Online
again). Kept: results table (Series/Year/Issues/Publisher), cover-art
preview and description panel that both update on row selection, double-click
a row to proceed.

**Select Issue dialog** (second screenshot): issue list (Issue #/Date/Title)
with cover preview and description, both updating on row selection — no
changes from the screenshot's own layout.

**Two-window question resolved as one modal, two internal steps, not two
stacked windows.** CT's split into separate `QDialog`s is a desktop-toolkit
artifact — independently movable/resizable windows are a native-app
affordance that doesn't carry over to a browser modal. Stacking two overlays
would mean nested focus-traps, a second backdrop, and rebuilding a whole
overlay just to go "back" to already-fetched series results, for no offsetting
benefit — nothing else in ComicVault has a stacked-modal precedent either.
Built as one modal container; a "← Back to Series" control returns to the
cached results list from the issue step.

**Confirming a match still fully overwrites the mapped form fields and still
only clears the `NeedsReview` XML tag on save** (session 2, unchanged) — the
border/count are read live off in-memory form state, so they update the
moment fields are populated, same as every other field in this editor; they
don't wait for a save round-trip.

**Not yet decided, flagging for a future pass, not blocking:** whether
Search Online should also warn/disable if no `comicvine_api_key` is
configured in Admin, rather than surfacing a raw network failure on first
use. Worth doing, doesn't affect anything else here.

**How to apply:** Written into `EDITOR_SPEC.md` §9, 2026-07-03 (session 4's
doc-update pass). No hold applied — see the correction note in the session 4
entry above.

### ComicTagger integration — search/select dialog locked as a modal overlay; ComicVine API key gets a home; 2000 AD parser fix deferred

**Decided:** 2026-07-03, ComicTagger integration scoping session 2 (Chat + Tez) —
eng-review pass on session 1's two open questions, plus one gap the review
surfaced.
**Why:** Three related calls:

1. **Modal overlay confirmed** for the CT search/select dialog (not an
   in-column panel swap in Column 2). A modal cleanly blocks the rest of the
   Full Editor while it's open — in particular Column 1's existing
   hover/arrow-key "focused card" mechanic (§5.2), which would otherwise fight
   with an open search dialog over which file is "current." An in-column swap
   would have had to solve that conflict from scratch; a modal gets it for
   free by definition.

   Design details locked in the same pass, all chosen for consistency with
   existing Full Editor conventions rather than inventing new ones:
   - Re-Search field pre-fills with the form's current Series value (not
     blank) — matches the already-confirmed "editable search field, not a
     passive candidate list" workflow (`INBOX.md`, session 1).
   - Confirming a selected issue **fully overwrites** the mapped fields in
     the form — same "not a smart merge" rule §3.3 already established for
     saves generally (every exposed tag is fully overwritten by whatever's in
     the form). One rule for the whole editor, not a special case for this
     dialog.
   - Modal traps focus, blocking Column 1's card-swap and Process
     Queue/Process All while open.
   - Two trigger points open the same modal instance: a button beside the
     Series field (always available), and clicking a `NeedsReview`-flagged
     card's warning badge in Column 1. The badge reuses §3.5's warning visual
     pattern but the click target opens this modal directly, not §3.5's
     read-only side-by-side view — different problem (wrong/blank field vs.
     duplicate XML) doesn't need the same resolution UI.
   - No auto-advance to the next flagged file after confirming a match —
     closes back to normal state, Tez picks the next one manually, matching
     the existing "walk the list" batch workflow rather than a new
     guided-queue mechanic.
   - Series/issue search must go through **one shared backend function**,
     called by both this manual modal and the eventual CT Auto-Tag automation
     stage (session 1) — same router-independent-callable principle already
     applied to Convert Archives/Convert Images (`ADMIN_SPEC.md`
     §11.2/§11.3), not two codepaths hitting ComicVine.

2. **ComicVine API key gets a home.** Reading
   `comictalker/talkers/comicvine.py` directly (in the CT clone) found the
   talker ships with a hardcoded shared default key
   (`27431e6787042105bd3e47e169a624521f89f3a4`) rate-limited to **1
   request/10s, 100/hour** — versus **10 req/10s, 200/hour** on a personal key
   (`custom_limiter` vs `default_limiter`, same file). That shared key is used
   by every ComicTagger install that hasn't configured its own, so a
   Processing-folder batch running on it would stall for hours and compete
   with unrelated users worldwide. Nothing in `config.json` or
   `ADMIN_SPEC.md` currently holds a personal key — this blocks the CT
   Auto-Tag automation stage from session 1 as much as it blocks this modal,
   not something either can quietly work around. **Confirmed with Tez:** new
   `comicvine_api_key` field in `config.json` (same trust model already
   applied to `SESSION_SECRET`, stored there in plaintext today), with an
   Admin UI field placed near Processing Folder Automation, since that's the
   section it unblocks.

3. **2000 AD "progs"-to-issue filename pattern fix deferred**, logged as a
   `[change]` not a `[bug]`. The manual Re-Search field (above) already
   covers this workflow today at no extra cost — re-typing the issue number
   into the search string was already the confirmed real-world habit
   (session 1). Automating the upstream parser is a precision improvement for
   later, not a gap blocking anything now.

**How to apply:** Written into `EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4,
2026-07-03 (session 4's doc-update pass). **Correction, same pass:** this
entry originally cited "per the standing rule nothing in the CAPT cluster
goes to Code until the whole set is reviewed together" as a blocker. That
was wrong — checked against `ROADMAP.md`'s own v2.4 close-out note and
`ADMIN_SPEC.md`'s per-section build-status text, the §12 CAPT cluster (Items
4–7/9–13/15–16) was already built and verified before this scoping began;
v2.4 closed 2026-07-02. No such hold ever applied here — I was working from
stale memory instead of checking. `EDITOR_SPEC.md` got a new CT
Integration section (§9) covering the modal (data flow, both triggers, overwrite
semantics, focus trap) alongside the existing §3.5/§5.2 material it reuses;
`ADMIN_SPEC.md` got the `comicvine_api_key` field documented alongside
§11.4's automation settings, plus the three-stage pipeline amendment already
noted in the entry below.

### ComicTagger integration — Rename moves after Full Editor review; low-confidence flag stays an in-file XML tag

**Decided:** 2026-07-03, ComicTagger integration scoping session (Chat + Tez),
continuing from the CBR write-back decision above.
**Why:** Two related calls made in the same session:

1. **Manual workflow order changes.** Tez's original stated pipeline was convert
   → CT tag → convert images → rename → open in Full Editor. Rename sitting
   between tagging and review meant any "needs review" signal correlated by
   filename/path would break exactly at that step. Tez agreed to reorder:
   convert → CT tag → convert images → **open in Full Editor (review/confirm/
   search-fallback)** → rename → move to library. This doesn't change
   `ADMIN_SPEC.md` §11.4's built automation (Rename was already excluded from
   automation, for a separate reason — no undo, needs a human at the live
   preview) — it changes the order Tez runs Rename manually, after the Editor
   step rather than before.
2. **Low-confidence match flag stays an XML tag, not a dump/log-file
   correlation**, even after the reorder removed the original objection
   (filename changing mid-window). Reason: the Full Editor already parses each
   file's XML on load — reading a new tag out of that same parse costs nothing.
   A log-file approach still needs new write code, new read code, and a
   path-correlation step, none of which are free. The "must be explicitly
   cleared/resolved on save, or it lingers" problem applies equally to both
   approaches, so it isn't a differentiator. A separate **aggregate audit-run
   log** ("12 converted, 11 confident, 1 flagged") is still worth building —
   Tez confirmed this explicitly — but as a future addition alongside whatever
   job-progress logging the eventual CT automation stage needs, not as the
   mechanism the Editor itself reads.

**How to apply:** When CT integration is actually scoped for build, it becomes
a **new middle stage** in `ADMIN_SPEC.md` §11.4's pipeline — Convert Archives →
CT Auto-Tag → Convert Images — following the exact same architecture already
established twice (§11.2/§11.3): a plain router-independent callable, its own
progress singleton, its own audit log using the existing `[AUTO]`-prefix
convention rather than a new log format. The low-confidence flag is a new XML
tag (name TBD, e.g. `NeedsReview`) added to `COMICINFO_TAGS`
(`backend/editor/xml_parser.py`) with special handling in the Editor's save
routes to explicitly clear it on every successful save — `build_xml_from_fields`
only touches tags present in the submitted payload, so this tag will never
self-clear via the normal field-preservation mechanism (`field_merge.py`) the
way a text field would. **Confirmed whole-file, not per-field** (same
session, follow-up) — Tez's stated need was "flag the file," and Genre is
irrelevant to this either way since CT/ComicVine doesn't supply Genre data at
all, so there's no per-field case being lost by keeping this simple.

### ComicTagger integration — CBR write-back stays out of scope even though `rar.exe` is present on Tez's machine

**Decided:** 2026-07-03, ComicTagger integration scoping session (Chat + Tez).
**Why:** While scoping CT integration, Tez asked whether the existing CBR→CBZ
conversion requirement (Item 6, `admin-spec-section-12-processing-tools.md`
§12.2) might no longer be needed, since CBR is now natively DB-supported
read-only (Item 5) and CAPT already has a CBZ→CBR converter. Reading
`comicapi/archivers/rar.py` (in the CT clone at
`D:\workshop\3rd_party_apps\ComicTagger`) confirmed all RAR write operations
(`write_file`, `remove_file`, `set_comment`) shell out to an external `rar`
executable located via `shutil.which()` — no pure-Python or free fallback
exists. CAPT's own `create_rar_archive()` (`arc_conv_helpers.py`) does the
identical thing. Tez then confirmed `rar.exe` (the WinRAR CLI component) is
in fact installed on his machine, which is why CAPT's CBZ→CBR button has
apparently worked before.

That finding doesn't change the decision: Convert Archives (CBR→CBZ) stays a
hard requirement ahead of CT tagging, and CBZ→CBR / any CBR write-back stays
permanently out of scope. Depending on one specific machine happening to have
a paid tool's CLI binary on PATH is exactly the kind of personal-environment
coupling the project has been deliberately cutting elsewhere (Flatten
Archive, saved rename templates). It's not portable, not guaranteed to
survive a reinstall/migration, and isn't something Code should build a
dependency on.

**How to apply:** CAPT's `create_rar_archive()` / CBZ→CBR feature is now dead
code from ComicVault's perspective — candidate for removal from CAPT, not for
porting into ComicVault's Admin UI. If CBR write-back is ever reconsidered,
it needs its own decision (and would still require documenting the WinRAR
dependency explicitly, not assuming it away), not a quiet re-add.

### File Rename — kept Year over the mockup's Publisher field; added per-item queue removal

**Decided:** 2026-07-02, planning session with Tez ahead of the "Add to Queue" fix
(see `progress.md` "Session — 2026-07-02").
**Why:** Restoring the queue workflow surfaced two mismatches against the original
mockup (`images/Filename-Editor.pdf`) that needed a call, not just a mechanical
port:
- The mockup's 4th field is "Publisher"; the shipped build (and `ADMIN_SPEC.md`
  §11.1.4) uses "Year". Publisher isn't parsed by `filename_parser.py` or included
  in the `Series - Title #Issue (Year)` output format — adopting it would mean new
  backend parsing work, not just a frontend relabel. Tez chose to keep Year,
  since it matches what the parser and output format already do; Publisher stays
  unbuilt rather than half-matched to the mockup.
- The mockup only shows a whole-queue "Clear Preview" control, no per-row removal.
  Tez chose to add per-item removal anyway, since without it a single mis-added
  file would force clearing (and re-queuing) everything else in the batch.

**How to apply:** If Publisher ever gets scoped in, it needs its own parsing +
output-format decision first — don't just add a text field. The per-item queue
removal control is intentional scope beyond the mockup, not an oversight to trim
back toward it.

### v2.4 Item 10/15 — File Rename dropped from Processing Folder Automation

**Decided:** 2026-07-01, dedicated re-scoping session (Chat + Tez).
**Why:** Item 15 flagged §12.1 File Rename as needing a bigger re-scope before Item
10 could build, on the assumption automation needed a saved naming-convention
template system. Before building that, the session tested the actual parser
(`filename_parser.py`) against two real filename sets pulled from the library (323
periodical-style releases, 319 creator-prefixed OGN/collection files) rather than
reasoning about it in the abstract.

That testing found the re-scope's real problem wasn't missing features, it was a
live bug: `extract_year()` has a hardcoded `present_year = 2025` validity ceiling,
so every 2026-dated file silently fails year extraction — which cascades into
series/issue extraction failing too, since a rejected year's bracket never gets
stripped from the series string. Measured against the sample: 64% failure rate.
Two smaller bugs also found (a zero-issue string collapsing to empty via
`lstrip('0')`; whitespace/text artifacts left behind by volume+subtitle patterns
like `v05 - Twisting Loyalties`). All three are fixed in the §12.1.3 Change Log.

The creator-prefixed sample also confirmed something structural, not a bug:
`"Cyberpunk 2077 - Chrome 03"` and `"Abby Howard - The Crossroads at Midnight"` are
structurally identical strings to a regex parser — there's no reliable way to know
one is an umbrella-series/sub-title pair and the other is an author/book-title
pair. Trying to auto-split these was the actual source of "too many variables" —
the fix wasn't smarter parsing, it was accepting the parser can't resolve this
class of ambiguity and routing it to the existing manual Title field + All
checkbox instead (which already existed for exactly this purpose).

Once that was settled, the automation question answered itself: Rename's *only*
correction mechanism is the human reviewing its live preview before committing (no
undo — §12.1.6). That's specifically the thing Processing Folder Automation
removes by running unattended. And the ambiguous Series/Title cases above need a
human decision no saved template could supply — automating Rename would mean
silently applying the "good enough" fallback output to every file that would have
benefited from a manual Title entry, with no signal in the log distinguishing which
files got which treatment. Tez agreed dropping Rename from automation entirely was
the right call rather than trying to make both work — matches the session's
recurring theme of catching scope before it compounded (see "Pattern worth naming"
below).

**Knock-on effect:** §12.4 Processing Folder Automation is amended from a
three-stage to a two-stage pipeline (Convert Archives → Convert Images). The
saved-naming-convention-template requirement raised in Item 15 scoping (`INBOX.md`)
is dropped entirely, not deferred — nothing to build. `INBOX.md`'s §12.1 re-scope
entry is struck as resolved; the separate §12.2 backup-model re-scope entry is
unrelated to this decision and remains open.

**Pattern worth naming:** the session started as "make the rename parser smarter"
and nearly expanded to cover ComicTagger-integration timing and XML-driven
renaming before Tez caught it and pulled back to KISS. The eventual real fix (one
hardcoded constant) was far smaller than the scope that was almost built instead —
worth remembering next time a "just needs to be smarter" feeling shows up: test
against real data before assuming the gap is in the logic rather than a stale
constant or a genuinely unparseable ambiguity.

### v2.4 Item 8 — Flatten Archive dropped, reclassified as BUG-018

**Decided:** 2026-06-30, mid-scoping session (Chat + Code).
**Why:** Item 8 went in as a routine CAPT-tool port, same pattern as Items 6/7.
Scoping it started with the normal "why does this tool exist" check, and Tez
couldn't recall the original reason — he knew he'd built Flatten Archive for a
concrete problem, just not which one. Handed to Code to investigate; Code traced
it to a real, still-open scanner bug (BUG-018, `BUGS.md`): `_parse_cbz()` only
matches `ComicInfo.xml` at the zip root, so archives with the xml nested inside a
subfolder import with filename-guessed metadata instead of real data. That
symptom — exactly what a Flatten tool would visually "fix" by restructuring the
archive — was the actual reason the tool got built originally.

Once that was clear, the question stopped being "how do we scope this tool" and
became "does this tool still have a job once the bug's fixed." It doesn't:
editors already read nested xml correctly (`find_xml_in_archive()` matches any
depth) and already flatten on save (`_rebuild_archive()`, existing behavior,
unchanged) — so a fixed scanner means nested archives import correctly without
any manual intervention, and editing one (for any reason) flattens it as a side
effect anyway. Confirmed with Tez no independent use case survives this (e.g. no
bulk-hygiene or Flutter-local-mode need distinct from the bug). Item 8 and Item
14 (its build counterpart) are both struck from `comicvault-changes-v2.4.md`
rather than scoped/built.

**Knock-on effect:** Item 15 (Processing Folder Automation) listed Item 8 as a
hard dependency and counted Flatten Archive as one of four CAPT tools it would
orchestrate unattended. With Item 8 gone, Item 15's dependency note was revised
to drop that blocker — it now depends only on Items 10–13. Whether unattended
automation still needs a flatten step (and if so, calling `_rebuild_archive`
directly the way Item 7 already does, with no standalone tool behind it) is left
for Item 15's own scoping session, not decided here.

**Pattern worth naming:** a CAPT tool's original existence is itself a strong
signal there was a real problem behind it — "why was this built" is now a
standing first question for any remaining unscoped CAPT-tool item, not just a
one-off for Item 8.

### v2.4 Item 5 — CBR support reversed back in, EPUB and PDF dropped from scope

**Decided:** 2026-06-30, eng-review + scoping session (Chat).
**Why:** Item 5 went in scoped as one decision ("add CBR/PDF/EPUB"). An eng-review
pass before scoping (`/eng-review`) surfaced that each format is actually a
separate problem with a different right answer, and that two of the original three
had a materially cheaper existing solution the original scope didn't weigh against
native support — read `cap_toolkit/processors/arc_conv_cb_proc.py` and
`arc_conv_pdf_proc.py` directly before concluding this, both already exist and
work.
- **EPUB dropped entirely.** Confirmed with Tez it was a speculative carry-over
  from another app, not a confirmed need, and the sample file he has (HTML pages +
  cover.jpg inside a plain archive) doesn't generalize to the EPUB spec anyway.
  Structurally incompatible with the page-indexed reading model every other part
  of the app depends on (`page_count`, `/issue/{id}/pages`,
  `/page/{issue_id}/{page_number}`, Flutter's `comic_page_view.dart`) — supporting
  it for real would mean a second, genuinely different reader, not an extension of
  the existing one. Too much cost for a feature that was never confirmed wanted.
- **PDF dropped from native scanner/library scope**, redirected entirely to CAPT's
  existing PDF↔CBZ converter (delete-original option already built) plus the Full
  Editor for tagging. PDF has no ComicInfo.xml-equivalent metadata standard —
  natively indexed, every PDF would land `metadata_source = "filename"` with none
  of the genre/writer/story-arc filtering working. Converting first gets a fully-
  capable CBZ for free; native PDF support would have meant real scanner/thumbnail
  work for a permanently second-class result.
- **CBR reinstated as full native support, read-only at the archive level.** The
  original "library is all-CBZ" decision (`EDITOR_SPEC.md` §2/§9, made when CAPT
  was ported) was correct *for that scope* — personal project, already-converted
  collection. It no longer fits the current goal: Tez's thinking has shifted toward
  a possible public release, and he knows from seeing other users' collections that
  large mixed CBZ/CBR libraries are common (some over 100,000 issues). Forcing a
  bulk pre-conversion before the library is even browsable isn't viable at that
  scale or for a public audience who didn't curate their collection the way Tez
  curated his own.
  - **Read CBR everywhere, never write it.** `rarfile` (extraction-only) is already
    a proven dependency via CAPT's own CBR↔CBZ converter — no new library, and no
    `7-Zip` dependency either, contrary to the original v2.4 doc's note (verified
    by reading `arc_conv_helpers.py` directly: it's `rarfile`/`unrar` for
    extraction, a `rar` CLI shell-out for creation).
  - **Why never write:** RAR archive *creation* requires a paid WinRAR install —
    confirmed by reading `create_rar_archive()`, which shells out to `rar` and
    raises if it's missing. That's not a dependency a public app can carry.
  - **So editing a CBR's metadata rebuilds it as `.cbz`, not `.cbr`.** This isn't
    new code — the editor's rebuild path (`shutil.make_archive(..., "zip", ...)`)
    already only ever produces a zip, even before this change. Adding CBR support
    only meant adding a `rarfile` *read* branch; the existing rebuild path needed
    no change at all, it just now sometimes has a `.cbr` source feeding into the
    same zip-only output. Confirmed with Tez this applies uniformly across Basic
    Editor, Full Editor single-file, and Full Editor batch/Process All — no
    per-surface exception.
  - **Net effect, confirmed as the actual goal:** a user's library is fully
    browsable/readable on day one regardless of CBZ/CBR mix, no bulk conversion
    required: the library trends toward all-CBZ over time as files happen to get
    edited, rather than needing a separate batch-conversion pass.
  - **Known accepted gap:** Flutter local/offline mode (the `archive` Dart package
    has no RAR support) won't open a `.cbr` copied to a device for travel reading.
    Server mode is unaffected — page-serving already abstracts the container format
    away from the client. Left for whoever revisits Mobile Reader work
    (`ROADMAP.md` "Paused indefinitely"), not addressed by this item.
**Where:** `SPEC.md` §6/§6.1/§7/§13/§17/§21, `EDITOR_SPEC.md` §2/§3.1/3.2/§9 +
Change Log, `v2.4/comicvault-changes-v2.4.md` Item 5/11.

### v2.4 Item 3 (empty-results logo) extended to all emoji empty/error states

**Decided:** 2026-06-29, build session (Code), Tez's explicit call after seeing
the original item work.
**Why:** Item 3 as scoped only covered the "No comics match these filters."
state's `📚` icon. Once built and manually tested, the same `.empty-icon`
pattern turned out to cover 10 more states in `app.js` — some genuinely
"no content" (`📚` on "No content yet."), others error/warning states (`⚠️`
on server-unreachable, search failure, series/issue not found, etc.). Tez
asked for the same logo swap across all of them rather than leaving a mix of
emoji and logo. This is a judgment call worth a paper trail specifically
because it repurposes the logo for warning/error states too, not just
"library has nothing to show" — a different semantic than the original item
text described, decided live rather than scoped in advance.
**Where:** `frontend/js/app.js` (11 spots total), `frontend/css/style.css`
(`.empty-logo` class, shared by all of them). See `v2.4/progress.md` "Session
— 2026-06-29: v2.4 Item 3" for the full list of states touched.

### BUG-016 root cause confirmed; INBOX.md, ROADMAP.md/INDEX.md/roadmap.html reconciled with the 2026-06-28 manual test pass

**Decided:** 2026-06-28, doc-handling review session (Chat).
**Why:** BUG-016 (Restore Database) was logged with two competing theories —
connection-teardown race vs. path mismatch. Read `backend/database.py` and
`backend/routers/admin.py` directly: confirmed it's neither a race nor a path bug.
SQLite runs in WAL mode (`PRAGMA journal_mode=WAL`); `restore_database()` copies the
backup over the main `.db` file but never clears the existing `-wal`/`-shm` sidecar
files, so writes made after the backup (sitting in the pre-restore WAL) get replayed
back in on the next connection, undoing the restore. Path mismatch ruled out —
`db_path` resolves identically in both the restore and backup functions. Confidence
is now "confirmed by reading the exact mechanism," not "plausible theory" — worth
noting for whoever picks up the fix, since the recommended fix (checkpoint + clear
WAL files before the copy) follows directly from this, not from further
investigation.
**Where:** `BUGS.md` BUG-016 (root cause section rewritten, old hedge removed).
Also reconciled `INDEX.md` and `meta/roadmap.html`, which still said "10–13 not yet
manually tested" — stale relative to the test pass another session had already run
and logged; `ROADMAP.md` and `comicvault-changes-v2.3.md` were already current.
`INBOX.md`'s "Unprocessed" section also turned out to be fully triaged already (every
line had a destination annotation) — moved to "Processed" under a new "Triaged
2026-06-28" heading; no actual triage decisions were needed, just the move.

---

### Doc folder restructure (`docs/historical/`, `docs/meta/`) + CLAUDE.md status-line fix + git tag convention

**Decided:** 2026-06-28, doc-handling review session (Chat).
**Why:** Two separate problems surfaced together. (1) Cowork's nightly scan only
rechecks *changed* files — a closed-out doc that stops changing drops out of scope
permanently, so anything it was quietly still tracking (e.g. Admin Card Size, found
at the bottom of `comicvault-changes-2.1.md`, never carried into `ADMIN_SPEC.md`
until backfilled 2026-06-27) can sit invisible indefinitely. Splitting closed-out/
one-time docs into `docs/historical/` makes "out of scope" mechanical (a path Cowork
can skip by rule) rather than something relying on per-file judgement — doesn't fix
the omission-detection gap itself (flagged in `INDEX.md`'s historical section as
still open), but stops the folder from growing more ambiguous. (2) `CLAUDE.md`
Section 5 had been silently hardcoding the active feature name ("Custom Tabs (done)
→ Home Strips (in progress)") since before v2.2 even existed — the same failure
shape as `doc-scan-issues.md` ISSUE-005/006/007 (a status fact restated in a second
place, with no automated check on this particular copy since Cowork doesn't read
`CLAUDE.md`). Fixed by having Section 5 point at `comicvault-changes-vN.M.md`'s own
status block instead of restating it, removing the redundant copy rather than just
refreshing it. Also added a git tag convention (tag `vN.M` on build-queue close-out)
rather than adopting finer-grained SemVer-style versioning — the project has one
deployment and one user, so there's no compatibility surface that finer granularity
would serve; the existing doc version label just needed an actual git ref tied to it.
**Where:** `INDEX.md` (folder structure section, full doc table), `CLAUDE.md`
(Section 2 doc table + folder note, Section 5 rewritten, Section 7 git tag
convention added), `meta/working-rules.md` (new Versioning section). `meta/
build-plan.html` also moved from `historical/` to `meta/` during the same pass —
it's the live build tracker, not a closed-out doc, and was misfiled in the initial
move.

---

### v2.3 Item 14 moved to `ROADMAP.md`; v2.3 kept open rather than formally closed

**Decided:** 2026-06-28, doc-handling review session (Chat).
**Why:** Item 14 (site-wide header unification) is blocked on the same dependency
(Claude Design UI redesign direction) as an existing `ROADMAP.md` item, so it no
longer belongs in an active build queue — moved there, merged with that context,
rather than sitting in `comicvault-changes-v2.3.md` looking like queued work. Tez's
call on the broader question (is v2.3 "done"): explicitly **not** closing it out
despite Items 1–13 being complete — `INBOX.md` still has unprocessed items that
might reasonably land under v2.3 once triaged, and closing the doc now would force
a premature decision about where those go. Separately noted but not yet acted on:
Items 10–13 were each Code-verified live in their own session but never went
through the kind of dedicated manual test pass Items 1–9 got — flagged to Tez,
especially Item 12 (Restore Database), where Code's own session notes confirm the
actual restore-and-restart path was never exercised against a real file.
**Where:** `comicvault-changes-v2.3.md` Item 14 entry (now a pointer),
`ROADMAP.md` (new "Blocked on Claude Design UI redesign exploration" section),
`ADMIN_SPEC.md` status block, `INDEX.md` (two rows).

---

### Doc folder restructure round two: `historical/` → `archive/`, per-version `docs/vN.M/` working folders, `BUGS.md` split (open vs. fixed), v2.3 fully consolidated, v2.4 started

**Decided:** 2026-06-29, doc-handling review session (Chat), refining the
2026-06-28 restructure above.
**Why:** As the project grows, the root doc set keeps growing too — more token
cost per session, more surface area for drift. Tez's first instinct was to archive
everything except `ADMIN_SPEC.md`, the Processing Tools spec, and the cowork docs.
Pushed back on that specifically: feature specs (`SPEC.md`, `EDITOR_SPEC.md`,
`CUSTOM_TABS_SPEC.md`, `HOME_STRIPS_SPEC.md`, `MENU_BAR_SPEC.md`), `ROADMAP.md`, and
`TESTING.md` describe what the app currently *does* or standing process — they're
not version-scoped, and archiving them the moment a build queue closes would mean
every spec goes stale-by-relocation on every release, forcing future sessions to
re-derive current behaviour from source instead of reading a maintained reference.
Landed on a narrower, sharper cut instead:
- **`historical/` renamed `archive/`** — same contents, different framing: "out of
  focus, not out of mind." Code/Chat retain full read access any time something
  needs revisiting; only Cowork's nightly scan treats it as out of scope.
- **`docs/vN.M/` working folders**, new pattern starting with v2.4 — each version
  gets its own `comicvault-changes-vN.M.md` + scoped `progress.md`, bundled
  together and moved into `archive/vN.M/` as one unit on close. Bundling (not
  separately rotating each file) means a version's full story stays in one place.
- **`BUGS.md` split into open-only (stays at `docs/` root) + `archive/
  bugs-fixed-archive.md`** (flat, not version-scoped — a bug found in one version
  can get fixed in a later one, so tying its fixed record to either version's
  folder would be the wrong cut). 11 fixed entries moved out 2026-06-29, leaving 5
  open (`BUGS.md` BUG-016/015/014/013/008).
- **v2.3 fully consolidated into `archive/v2.3/`**: its build queue, the full
  pre-v2.4 `progress.md` (covers V1 through v2.3 — predates the per-version
  pattern, archived as one snapshot rather than split further), and the
  2026-06-26 test-session artifacts.
- **`comicvault-changes-v2.4.md` created**, Item 1 = File Rename Tool (already
  fully scoped in `admin-spec-section-12-processing-tools.md` §12.1).
- **`ROADMAP.md` cleanup, same pass:** removed two already-resolved sections (port
  8000 workaround, BUG-003) that had accumulated informal "edit: Tez, fixed" notes
  instead of being removed; corrected a stale `ADMIN_SPEC.md` section reference for
  Rename (was §11.1, now §12.1); flagged an unresolved ambiguity rather than
  guessing — a note in the file said "13 added to bugs.md" but Item 13 (Card Size)
  passed its test; the actual `BUGS.md` entry is Item 12. Tez confirmed Card Size
  was never a bug but couldn't explain the mismatch — left as an open flag, not
  resolved here. Also flagged Tier 5's Genre-additions/draw.io-video items as
  unconfirmed (only the `.ico` item got an explicit answer: deferred, not done).
- **`DECISIONS.md` deliberately not touched** — flagged in `INDEX.md` as needing
  its own entry-by-entry pass (some entries are closed-chapter, others are standing
  rationale current specs still point back to) rather than a blanket move.
**Where:** `docs/historical/` → `docs/archive/`, `docs/archive/v2.3/` (new,
consolidated), `docs/v2.4/` (new), `BUGS.md` (trimmed), `archive/
bugs-fixed-archive.md` (new), `ROADMAP.md`, `INDEX.md`, `CLAUDE.md` (Section 2
table + folder note, Section 4 checklist, Section 5, Section 7), `meta/
working-rules.md` (doc-structure section rewritten), `meta/roadmap.html` (Now/Next
lanes updated, bug count), `CHANGELOG.md` (intro note on which `progress.md` old
vs. new entries point to).

---

### Restore Database: auto-snapshot the current DB before every restore

**Decided:** 2026-06-27, Item 12 scoping session.
**Why:** Restore is strictly more destructive than Clear Database (§7.4) — it
replaces the entire DB file, including Custom Tabs/Home Strips that Clear Database
deliberately preserves — and has no undo once committed. Tez's call: take a
throwaway snapshot of the *current* DB (reusing the existing `run_database_backup()`
helper already shared by manual + scheduled backup, so this is a filename, not new
code) immediately before overwriting it. "Can't hurt and extra safety is worth it."
**Where:** `comicvault-changes-v2.3.md` Item 12.

### BUG-014: root cause is the four main surface tabs never updating the URL, not a regression of the Tier 1 back-button fix

**Decided:** 2026-06-27, found while scoping `comicvault-changes-v2.3.md` Item 14
(read `app.js`/`issue.html`/`series.html` directly rather than guessing).
**Why:** Initially logged as a possible regression of the Tier 1 fix
(`comicvault-changes-2.1.md`, 2026-06-21/22). Direct code reading showed that fix
is still intact — `initIssue()`/`initSeries()` correctly call `window.history.back()`.
The real gap: the four main surface tabs (Home/All/Singles/Series) never call
`pushState`, so the URL never reflects which tab is active, while Folder View
already does this correctly via `pushFolderViewUrl()`. Recorded as a decision rather
than just a bug note because it reframes the fix — extend an existing, proven
pattern to the main tabs, not write a new one — and because it links BUG-014 and
Item 14 (header unification) as one piece of work rather than two.
**Where:** `BUGS.md` BUG-014, `comicvault-changes-v2.3.md` Item 14.

### Inbox triage 2026-06-27: treated as v2.3 continuation, not a v2.3 close-out + v2.4 open

**Decided:** 2026-06-27, inbox triage session (`doc-scan-issues.md` ISSUE-007 follow-up).
**Why:** Tez's explicit call — before closing out v2.3 (all 9 original items built and
manually tested 2026-06-26), the 7 new inbox lines were folded in as Items 10–14 of
the same `comicvault-changes-v2.3.md` queue rather than starting a fresh
`comicvault-changes-v2.4.md`. v2.3 stays "Active" until Items 10–14 are also built.
**Where:** `comicvault-changes-v2.3.md` (status block, Items 10–14), `INDEX.md`,
`ROADMAP.md` active-queue line.

### BUG-014: three back-button reports merged into one regression entry

**Decided:** 2026-06-27, inbox triage session.
**Why:** Three separate inbox lines (`?from=all`, `?from=series`, `?from=singles`)
all described the identical symptom — back navigation landing on Home instead of
the originating tab. Logged as one `BUGS.md` entry with three repro cases rather
than three separate bug numbers, and explicitly flagged as a **regression** of the
Tier 1 "Back button inconsistency" fix already closed out twice in
`comicvault-changes-2.1.md` (2026-06-21, then a follow-up correction 2026-06-22) —
worth flagging as a regression rather than a fresh bug, since it changes what Code
needs to check first (did the old fix get undone, vs. is this a new code path the
old fix never covered).
**Where:** `BUGS.md` BUG-014.

### File Rename: in-app picker, no recursion, per-field checkbox independence, narrow auto-increment scope, no undo

**Decided:** 2026-06-27, dedicated Rename scoping session.
**Why:** Several deliberate departures from precedent worth recording the reasoning
for, not just the outcome (full detail lives in `ADMIN_SPEC.md` §11.1, this is the
*why*):
- **In-app folder-tree picker, not a native OS dialog** — breaks the pattern set by
  the Scheduled Backup folder picker (§9), which gets away with a native dialog only
  because frontend and backend currently share a machine. That assumption doesn't
  hold under Remote Administration (the dialog would pop open on the server's own
  screen, not the remote browser), so Rename uses the same in-app HTTP/JSON picker
  pattern as the Editor and Custom Tabs instead.
- **No recursion into subfolders** — a deliberate divergence from both CAPT's
  original `rglob()` behaviour and the Editor's recursive folder-add, to keep a
  batch rename scoped to exactly what the user can see when they select a folder.
- **Per-field File/All checkbox independence, no column auto-select** — fixes a real
  CAPT bug where ticking one File (or All) checkbox auto-selected the entire column
  regardless of field.
- **Auto-Increment Issue Numbers gated specifically on Issue→All**, not any-All
  checkbox — fixes another CAPT bug where it activated regardless of which field's
  All box was ticked.
- **No undo** — consistent with the tool being a basic audit log, not a transaction
  system; the live preview is the only safety net before committing, matching
  CAPT's own behaviour.
**Where:** `ADMIN_SPEC.md` §11.1.1–§11.1.6.

---

### Clear Database scope: library data only, not Custom Tabs/Home Strips; same confirm() as Delete Tab; local-only gate

**Decided:** 2026-06-24, Item 9 build session.
**Why:** `ADMIN_SPEC.md` §7.4's literal wording ("wipes all records from the DB")
doesn't say whether Custom Tabs / Home Strip configuration counts as "all
records." Checked the schema directly: neither table has any FK relationship to
Issue, so wiping Issues has zero effect on them either way — the real question
was whether to *also* write code to explicitly delete them. Tez's call: library
data only (issues, genres, credits, reading progress, the now-orphaned People
rows) — Custom Tabs/Home Strips stay intact, since a "start fresh" library reset
shouldn't force rebuilding unrelated nav/home-page configuration.

Confirmation: the spec says "confirmation warning/modal," but Tez confirmed
reusing the exact same plain `confirm()` mechanism already used for deleting a
Custom Tab, not a custom modal — consistency with existing UX over literal spec
wording.

Gating: both Clear Database and Clear Reading Progress got the same
`is_local_request()` gate already used for Restart Server and the backup folder
dialog, on top of the existing blanket admin-password gate — a full library wipe
was judged at least as disruptive as either of those, and shouldn't be
triggerable over an authenticated Remote Administration session.

**Where:** `backend/routers/admin.py`'s `clear_database()` / `clear_reading_progress()`.

### Backup destination uses a native OS folder dialog, not the existing library-scoped picker

**Decided:** 2026-06-24, Item 8 build session.
**Why:** `ADMIN_SPEC.md` §9 originally said the backup folder picker should reuse
"the same mechanism as the Scan Roots Add button / Full Editor's path picker."
Checked both existing browse endpoints (`GET /api/admin/browse`,
`GET /editor/full/browse`) directly — both hard-reject any path outside the
configured library roots. A backup destination is explicitly meant to live
*outside* the library (a different drive, USB, or cloud-sync folder), so that
restriction makes the existing picker unusable here, not just inconvenient.

Tez's direction: use a real native OS folder dialog instead, opened by the
backend itself. This works because frontend and backend always run on the same
machine for this app — `tkinter.filedialog.askdirectory()` (stdlib, no new
dependency) run in a thread executor so it doesn't block the async event loop.
Gated to local-only sessions (`is_local_request()`, same helper already built
for the admin password feature) since a remote-admin session would otherwise
pop the dialog open on the server machine, not the remote user's screen — a
confusing, effectively broken result for that one case.

**Where:** `backend/routers/admin.py`'s `browse_folder_dialog()` /
`_show_folder_dialog()`.

### Server port change restarts via deliberate self-exit, relying on the tray app's existing crash-recovery

**Decided:** 2026-06-24, Item 8 build session.
**Why:** `reader_port` is read once at process start (`backend/config.py`'s
module-level `READER_PORT` constant, plus `start_server.py`'s `uvicorn.run()`
call) — there's no live-rebind path, a real process restart is required.
Rather than building new restart-orchestration code, `POST /api/admin/restart`
just saves the new port then calls `os._exit(0)` after a short delay (long
enough for the HTTP response to actually reach the client). The tray app's
`tray/tray_app.py` `health_check_loop()` already auto-relaunches the reader
subprocess on any unexpected exit — and a freshly-spawned process reads
`config.json` from scratch, picking up the new port with zero extra code.

Confirmed by live testing: when the server isn't running under the tray app
(e.g. started directly via `uvicorn`, as in this session's own scratch
verification), the process exits and **stays down** — there's no other
supervisor to relaunch it. This is a known, accepted limitation: the user gets
the same "you need to restart it" outcome either way, just automatically under
the tray app and manually otherwise. The frontend shows a confirmation dialog
before submitting a port change (it disconnects active LAN users) and the
field's hint text states the restart consequence up front.

**Where:** `backend/routers/admin.py`'s `restart_server()`,
`frontend/js/admin.js`'s `initServerPort()`.

### Backup frequency dict separate from the Auto Scan frequency dict

**Decided:** 2026-06-24, Item 8 build session.
**Why:** `ADMIN_SPEC.md` §9's 22 backup intervals (down to 1hr/2hr/4hr
granularity, up to 12 months) don't overlap cleanly with §4's 8-option scan
frequency set. Built a second `_BACKUP_FREQUENCY_SECONDS` dict in
`backend/scheduler.py` and a parallel `backup_loop()` following the exact same
polling/skip/re-read-config pattern as `auto_scan_loop()`, rather than trying
to force one shared frequency vocabulary onto two features with different
granularity needs.

**Where:** `backend/scheduler.py`.

### Scan log truncation, last-viewed state, and Explorer-reveal — Item 7 judgment calls

**Decided:** 2026-06-24, Item 7 build session.
**Why:** Three small implementation choices `ADMIN_SPEC.md` §4/§8 left open:

1. **Log truncation** — when a log file exceeds its configured size limit, the
   oldest ~10% of lines are dropped and the file rewritten, rather than rotating
   to `.1`/`.2` backups. The spec doesn't mention rotation, and a single
   append-only file that quietly drops its oldest entries is simpler and matches
   the "log", not "archive", framing of the feature.
2. **Last-viewed state** (drives each card's green-border indicator) lives in
   `config.json`'s new `log_last_viewed` object rather than a separate state
   file — it's UI state, but small and config-shaped, and reuses
   `config.save_config()` directly with no new file format to introduce.
3. **"View Logs Folder"** displays/copies the path rather than having the
   backend call `os.startfile()` to open Explorer directly. Even though this
   app always runs frontend and backend on the same machine (so it would work),
   no precedent exists yet for a web API spawning a native OS window, and
   display+copy achieves the same practical outcome without introducing one.

**Where:** `backend/scan_logs.py` (truncation), `backend/routers/admin.py`
(`mark_log_viewed`, `get_logs_folder_path`), `frontend/js/admin.js`
(`initLogsSection()`).

### `autostart_scan` config key reused verbatim for "Scan on launch"

**Decided:** 2026-06-24, Item 7 build session.
**Why:** `config.json` already had an `autostart_scan: false` key, present since
an earlier session but read nowhere in the codebase — clearly a stub left for
exactly this feature. Reused it directly for ADMIN_SPEC.md §4's "Scan on
launch" checkbox rather than introducing a new, differently-named key.

**Where:** `backend/scheduler.py`'s `maybe_scan_on_launch()`,
`frontend/admin.html`'s `#scanOnLaunchCheckbox`.

### Admin password gate: client-side popup instead of server-side redirect; global fetch wrap for 401 interception

**Decided:** 2026-06-24, Item 6 build session.
**Why:** `ADMIN_SPEC.md` §7.1.2 says an unauthenticated page request is "shown the
password popup." Two ways to get there: (a) always serve the page HTML/JS and let a
JS bootstrap show a blocking overlay if unauthenticated, or (b) check the session
cookie server-side in `main.py`'s page routes and redirect to a dedicated login page.
(b) is more airtight (unauthenticated HTML/JS never reaches the browser) but this
codebase has no templating engine — page routes are plain `FileResponse` — so it would
need a new login page and a redirect-back-after-login flow. Chose (a): simpler, reuses
one popup component for both page bootstraps and API 401s, and the actual security
cost is minor given the spec's own threat model (closed home LAN, not defending
against a hostile client reading static JS).

To catch 401s from every caller — `apiFetch()` in `app.js` plus the many raw
`fetch()` call sites in `editor_basic.js`/`editor_full.js` — without rewriting each
one, `auth.js` monkey-patches `window.fetch` globally to watch for 401 responses and
trigger the login popup. This is more "magic" than this codebase's usual explicit
style, but the alternative (touching dozens of call sites) was judged more invasive
and more error-prone to keep in sync over time.

After a successful login, the popup does a full `location.reload()` rather than
transparently retrying the original failed request — simpler given the interception
point doesn't have a handle back to the original caller's promise chain.

**Where:** `ADMIN_SPEC.md` §7.1/§7.2. Implementation: `frontend/js/auth.js`,
`frontend/login_popup.html`, `backend/auth.py` (`require_admin_auth` dependency, not
global middleware — kept per-router so the gate stays auditable per `main.py`'s
router-registration block, and so `/api/editor/genres`/`/formats` are caught
alongside the issue-specific editor routes without special-casing a path regex).

### Disabling password protection clears the stored hash outright

**Decided:** 2026-06-24, Item 6 build session.
**Why:** `ADMIN_SPEC.md` §7.1.1 says the stored hash "may remain on disk" after
disabling — ambiguous on whether enforcement state needs its own separate flag.
Chose to clear `admin_password_hash`/`admin_password_salt` on disable instead, so
`is_protection_enabled()` stays a one-line "hash present" check rather than needing a
second boolean to keep in sync (especially relevant given §7.1.1's force-disable-
remote-admin rule already has to update two fields atomically).

**Where:** `backend/routers/admin_auth.py`'s `disable_protection`.

### Multi-select scope corrected to include Series and Singles aggregate cards

**Decided:** 2026-06-23, inbox triage.
**Why:** Original scoping (`SPEC.md` §20.15, `comicvault-changes.md` Tier 4 Item 2)
deliberately limited card-hold multi-select to elements that map 1:1 to a single
issue — Singles surface cards, series-detail issue rows, Folder View flat file cards.
Series-aggregate cards were explicitly excluded on the reasoning that Favorites should
apply at the issue level and that a bulk action's meaning across a whole series
(mark read? favorite? rate?) would be ambiguous.

After using the library in practice, Tez found issue-only selection too limiting —
Series and Singles cards should be selectable on the same terms as issues, with the
same read/unread/favorite/rate bulk actions available. The "ambiguous meaning across
many issues" concern was weighed and overridden: bulk-marking a series as read or
favourited is a natural, common action and the ambiguity argument applies equally to
the existing "Mark all read" series-detail button, which has always been there and is
never confusing in practice.

**Where:** `SPEC.md` §20.15 (scope boundary definition) — treat this entry as the
correction before implementation begins. `SPEC.md` §20.15's explicit exclusion of
Series-aggregate cards is superseded by this decision.

---

### A scratch DB copy's `file_path` values still point at real, shared files — and ids aren't stable across separate scratch copies
**Decided:** 2026-06-21, during Tier 4 Item 3 Session C verification.
**Why:** Two related mistakes compounded into a real incident. (1) A "scratch DB" is
a disposable copy of the *metadata*, but every `Issue.file_path` inside it still
points at the one real, physical CBZ file on disk — there's only one copy of the
actual library. Testing any feature that *writes to the file* (the metadata editor's
save, specifically) through a scratch DB copy is therefore not actually scratch-safe
the way testing a DB-only feature is — it needs a genuinely fake, disposable CBZ
file with its own throwaway DB row instead. (2) Separately and compoundingly: this
session had already learned, and written down, that Person/Issue ids aren't stable
across different scratch-copy/migration runs — only names are — but a Playwright
test was built using a *remembered* issue id from an earlier scratch copy in the
same session, without re-querying what that id actually pointed to in the *current*
copy. It pointed at a different real file than assumed. Caught immediately via the
discrepancy between "no file changed" (checked the wrong filename) and the DB
showing a real update; root-caused by building a true fake-CBZ fixture and
reproducing the save cleanly, which also definitively proved the actual code path
has no bug — the mistake was entirely in how the test was constructed, not in the
feature being tested. Full incident account in `progress.md` "Session — 2026-06-21:
Tier 4 Item 3 — Session C".
**Where:** No code change — a testing-practice decision. Going forward: any test
that exercises a file-writing endpoint (the editor's save, archive rebuild, etc.)
uses a dedicated fake CBZ + throwaway DB row, never a real `file_path` borrowed from
a copied DB, scratch or otherwise. Always re-query an id's actual identity in the
copy being tested against, rather than reusing one remembered from a different copy.

### Live working-tree edits must stop the running server first, on high-risk sessions
**Decided:** 2026-06-21, during Tier 4 Item 3 (Writer/Artist dedup).
**Why:** Editing `backend/models.py`/`database.py`/`scanner.py` directly in the live
repo, while the actual running ComicVault server was up, let that server pick up the
new code on its own restart (unrelated to anything this session did) and write real
data via not-yet-fully-verified logic — breaking an explicit "this session never
touches the real DB" agreement. The scratch-DB isolation built into this session's
own test scripts protected nothing about the live, already-running process, which
reads shared source files off disk independent of any session's intentions. Tez's
call: for the rest of high-risk sessions like this one, stop the live server before
touching shared source files, rather than the more involved option of isolating the
work in a separate git worktree.
**Where:** Full incident account in `progress.md` "Session — 2026-06-21: Tier 4 Item
3". No code change — a working-practice decision for future sessions.

### One shared `role`-column junction table, not 6 per-role tables, for credit entities
**Decided:** 2026-06-21, building Tier 4 Item 3 (Writer/Artist dedup).
**Why:** `IssueGenre`'s per-field pattern (one junction table, denormalized string
value) doesn't fit people — a Person needs one stable id referenceable across all 6
credit roles (someone can be writer on one issue, colorist on another), which a
6-table split would multiply migration/sync/query code six-fold for no benefit. One
`IssueCredit` table with a `role` column serves both "browse by person across all
roles" (the click-through use case) and "filter by a specific role" equally well.
**Where:** `backend/models.py` `Person`/`IssueCredit`.

### Old raw CSV credit columns kept temporarily after the Writer/Artist migration
**Decided:** 2026-06-21, building Tier 4 Item 3.
**Why:** Dropping `Issue.writer`/`penciller`/etc. immediately (matching exactly how
Genre has no raw column at all) would be a one-way door on a 5,429-row production
table — if the new `people`/`issue_credits` data turns out subtly wrong after the
fact, the original raw strings are gone and the only recovery path is a full DB
restore. Keeping the columns inert for one release cycle costs nothing but a little
schema clutter and gives a free, instant cross-check path if anything's ever found
wrong. Drop them in a separate later session once the new system has run for real
with no issues found.
**Where:** `backend/models.py` (`Issue`'s 6 credit columns, now unused by read
paths once Session C lands), `backend/scanner.py` `_apply_metadata()`.

### `create_all()` doesn't add columns to an existing table — additive-schema assumption corrected
**Decided:** 2026-06-21, building Tier 4 Item 2 (Multi-select + Favorites/Rating).
**Why:** `comicvault-changes.md` assumed the new `favorites`/`personal_rating` Issue
fields would need "no migration of existing data" the same way CustomTab/HomeStrip
didn't — but those were whole new *tables*, and SQLAlchemy's `Base.metadata.create_all()`
only creates tables that don't exist yet; it never diffs columns on a table that's
already there. Proved this with a throwaway SQLite file before writing any real code
(column stayed absent from `PRAGMA table_info` after `create_all()` re-ran with the
column added to the model). This is the first time this project's "additive fields
need no migration" assumption didn't hold — first real additive *column* on an
existing table, as opposed to a new table. Fixed with a small idempotent
`ALTER TABLE` step in `init_db()`, verified against a scratch copy of the real
~5,500-row DB before trusting it.
**Where:** `backend/database.py` `_add_missing_issue_columns()`, `SPEC.md` §7 / §21.

### Bulk endpoints over a client-side fetch loop, for the multi-select toolbar
**Decided:** 2026-06-21, building Tier 4 Item 2.
**Why:** The series-detail page's existing "Mark all read" button (`markAllRead()`)
loops `Promise.allSettled()` over one `fetch()` per issue — fine for that button's
existing scope, but a multi-select bulk action could cover many more cards at once, so
N round-trips don't scale the same way. Built real bulk endpoints
(`POST /api/progress/bulk/...`) instead, following the existing
`PATCH /api/admin/home-strips/reorder` pattern (fetch all matching rows in one query,
loop, single `db.commit()`). `markAllRead()` itself was left untouched — a separate,
already-shipped feature, not retrofitted to the new endpoints.
**Where:** `backend/routers/progress.py` bulk endpoints, `frontend/js/app.js`
`runBulkAction()`.

### Auto-save confirmation message — dropped, deferred to admin redesign
**Decided:** 2026-06-20, reconciling `comicvault-changes.md` against `DECISIONS.md`.
**Why:** Originally planned for both Custom Tabs and Home Strips admin sections
(UI-consistency assumption — three sections, three buttons — not a functional need;
both already auto-save on every action, confirmed by direct testing). Purely
cosmetic, and the whole admin area is slated for a redesign once remaining
functionality work is done — adding a one-off message now would likely be redone
anyway. Deferred to that redesign rather than tracked as a standalone backlog item.
**Where:** `comicvault-changes.md` Tier 3 (item removed), `CUSTOM_TABS_SPEC.md` /
`HOME_STRIPS_SPEC.md` admin sections (future redesign).

### ComicInfo.xml is the sole source of truth when MetronInfo.xml also exists
**Decided:** 2026-06-20, discovered via `thanksgiving.cbz` / `tales of ruination.cbz`
already being in the library with both XML schemas present.
**Why:** The editor (`EDITOR_SPEC.md` §3.1/3.5) only ever reads/writes ComicInfo.xml —
it was never designed to reconcile two metadata schemas. Originally assumed to be rare
pre-library debris and folded into the Full Editor's existing multi-XML detection as a
test case; turned out to affect files **already scanned into the library**, where
`EDITOR_SPEC.md` §3.5 explicitly assumed "the existing library is already known to be
clean." That assumption is now known to be false. Rather than build dual-schema
reconciliation, ComicInfo.xml is confirmed as the single authoritative source —
matches the editor's existing scope exactly, no new logic needed. MetronInfo.xml is
treated as stale/ignorable wherever both exist. Confirmed working as designed for new
intake (Full Editor's side-by-side picker already lets Tez choose per-file before a
comic ever reaches the DB) — the gap was only ever already-scanned library files.
Cleanup of those handled via a one-off script run outside this project, not a
ComicVault feature (script should be report-first/dry-run, only act where ComicInfo.xml
is actually present and valid, to avoid stripping the only metadata source from a file
that happens to only have MetronInfo.xml).
**Where:** `EDITOR_SPEC.md` §3.5 (assumption correction below), cleanup via external
script — no project code changes.

### Writer/Artist: people table + search/link, not an enforced dropdown
**Decided:** sequencing/design confirmed across multiple sessions, formalized in
`comicvault-changes.md` Tier 4 Item 3.
**Why:** Genre/Format got the dropdown fix because each issue carries one short,
single value from a small fixed vocabulary. Writer/Artist are different on two counts:
(1) they're multi-value per issue — anthology titles (2000 AD, etc.) credit many
contributors on one issue, so a dropdown can't represent "this issue's credits" as a
single selectable value the way Genre/Format can; (2) even a fully deduplicated list of
individual names would be too long to be a usable dropdown — it's a search problem, not
a selection-from-a-short-list problem. Both issues point to the same fix: a real people
table (solves duplicate-name data integrity, e.g. spelling variants of the same person)
plus search + click-through linking (solves the UI volume problem), same pattern as the
clickable Genre tags on `/issue/{id}`. Sequenced last because it requires a one-time
migration/merge pass across ~5,500 real issues — highest risk item in the backlog,
needs its own short spec before any code is written.
**Where:** `comicvault-changes.md` Tier 4 Item 3.

### Genre/Format admin-list deletion: confirm-with-count, hard-block on emptying the list
**Decided:** 2026-06-20, building the Genre/Format admin editor (`comicvault-changes.md`
Tier 4 Item 1).
**Why:** Both fields are enforced, non-blank-required per issue. A silent delete could
orphan hundreds of issues' worth of tagging with no warning; an emptied list would make
every future save fail validation with no valid option left to pick. Confirm-with-count
mirrors the existing Custom Tabs delete pattern rather than inventing a new one.
**Where:** `backend/editor/editable_lists.py`, `frontend/js/admin.js`.

### Format flipped from locked constant to admin-editable list
**Decided:** 2026-06-20, reversing `EDITOR_SPEC.md` Section 4.2's original "locked,
no editing mechanism needed" call.
**Why:** Tier 5 cleanup (adding Anthology/Comic/Omnibus to Genre) was blocked on having
an admin editor at all, and the original rationale for locking Format ("the list
shouldn't change") turned out not to hold — Tez needed to add values for real library
data. Mirrors Genre's existing file-backed-list mechanism rather than building a second
pattern.
**Where:** `EDITOR_SPEC.md` §4.2 deviation note, `backend/editor/formats.json`.

### Home Strips' cap is on total stored strips, not just visible
**Decided:** during Home Strips build, 2026-06-19.
**Why:** Custom Tabs caps *visible* tabs (4) because the cost is nav-bar space — hidden
tabs are free. Home Strips caps *total* (5) because the cost is a DB query per strip on
every home-page load, whether visible or not — hiding a strip doesn't remove its cost.
Recorded here because the two caps look like the same rule by analogy and aren't —
a future session "fixing" Home Strips to match Custom Tabs' visible-only cap would
reintroduce a real performance problem.
**Where:** `HOME_STRIPS_SPEC.md` §3 vs `CUSTOM_TABS_SPEC.md` §3.

### Editor sync: webhook → in-process call
**Decided:** evolved across the V1→V2 editor integration (2026-06-18).
**Why:** V1's `SPEC.md` described the metadata editor as a separate Flask process that
called `POST /api/scan/file` over HTTP to tell ComicVault to rescan a changed file —
necessary because the two apps were genuinely separate processes on separate ports.
Once the editor's logic was ported into the same FastAPI app (`EDITOR_SPEC.md` §6.1),
the same rescan became a plain in-process function call — no HTTP round-trip, no
separate port. This is *why* any documentation written before 2026-06-18 (the original
`README.md`) describing a webhook/separate-app architecture is now wrong, not just
out of date.
**Where:** `SPEC.md` §17 (original) vs `EDITOR_SPEC.md` §6.1 (current).

### Genre/Format enforced dropdowns instead of free text
**Decided:** during editor integration design, `EDITOR_SPEC.md` §4.1.
**Why:** Direct fix for a real CAPT bug — its "dropdown" was actually free-text with
autocomplete suggestions and never validated anything, which is how the library ended
up with inconsistent values needing a pre-migration cleanup pass in the first place.
**Where:** `EDITOR_SPEC.md` §4.1, `backend/editor/validation.py`.

### Full Editor uses a server-side path picker, not browser file upload
**Decided:** `EDITOR_SPEC.md` §5.1 correction log, 2026-06-18.
**Why:** Browsers never expose a real filesystem path for an uploaded file, and the
editor needs to write a rebuilt archive back to a real path on disk — uploaded bytes
would have nowhere correct to land. Ported CAPT's existing server-side directory
browser instead of building a new upload-based flow.
**Where:** `EDITOR_SPEC.md` §5.1.

### Editor core: full overwrite + full archive rebuild, not incremental patching
**Decided:** `EDITOR_SPEC.md` §3.2/3.3, during editor-core porting.
**Why:** Simplicity-over-performance trade, deliberately — the collection isn't large
enough per-file for save latency to matter, and a full rebuild is more robust against
partial-write corruption than in-place patching. Every editor-exposed XML tag is fully
overwritten on save; tags the editor doesn't expose are preserved untouched rather than
merged field-by-field.
**Where:** `EDITOR_SPEC.md` §3.2 (archive rebuild), §3.3 (XML field merge).

### Format-group ("Series" vs "Singles") comes from folder path, not the XML Format field
**Decided:** V1 scanner design, `SPEC.md` §6.
**Why:** The XML `Format` field (Graphic Novel, One Shot, etc.) and the folder-based
Series/Singles split are answering different questions — where a comic *physically
lives* in the library vs. what *kind* of release it is. Using the folder path for
routing means moving a file between folders changes its routing immediately, without
needing an edit to its metadata.
**Where:** `SPEC.md` §6, `backend/scanner.py` `_format_group()`.

### Flutter over a web-based reader for the mobile/tablet app
**Decided:** mid-V1-build deviation, `SPEC.md` §21 change log.
**Why:** A web reader couldn't satisfy the "installed app" requirement on Android, and
a single Flutter codebase covers both Android and Windows rather than building two
separate native readers.
**Where:** `SPEC.md` §21 change log (2026-06-12 entry), `flutter_app/`.

### Menu bar redesign: treated Item 2's inline bullets as the complete sort spec
**Decided:** 2026-06-23, start of v2.3 build plan Item 2.
**Why:** `comicvault-changes-v2.3.md` Item 2 pointed to a "sort controls section
below" that doesn't exist anywhere in the doc — a dangling cross-reference, not an
intentional placeholder. Rather than pause the session to draft that missing section,
Tez chose to proceed using Item 2's own bullet list (A–Z / Newest / Recent / # of
Issues / # of Pages + ascend/descend toggle) together with `MENU_BAR_SPEC.md` as the
full spec.
**Where:** `comicvault-changes-v2.3.md` Item 2, `MENU_BAR_SPEC.md`.

### Convert Archives: background-job progress instead of Rename's blocking pattern
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** Rename's apply step blocks the request and shows a summary modal at the
end, which works because renaming is a near-instant string operation. Archive
conversion does real per-file work (extract, rezip, PDF page rasterization at
300 DPI) that can take meaningful time over a batch — a blocking request risked
long hangs or timeouts on larger batches. Rather than invent new infrastructure,
reused the module-level progress-singleton + polling-endpoint pattern
`backend/scanner.py` already established for scan jobs.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2.5, `backend/scanner.py`
`scan_progress`.

### Convert Archives: CBR CRC errors surfaced, not silently skipped
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** CAPT's original RAR extraction silently drops unreadable pages and still
reports the conversion as a clean success. That's inconsistent with the
no-partial-silent-failure principle already established for Rename (§12.1.6) —
carrying it over unchanged would mean a damaged CBR could convert to an
incomplete CBZ with no indication anything was lost. Kept the tolerant
extraction itself (still produces a CBZ rather than failing outright) but added
a `pages_skipped` count surfaced in both the result summary and the audit log.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2.4.

### Convert Archives: PDF render DPI as an isolated constant, not an Admin setting
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** CAPT's original PDF→CBZ rendering used 72 DPI (`fitz.Matrix(1,1)`),
which produces visibly blurry pages compared to native CBR/CBZ scans, and isn't
fixable after the fact short of re-converting from the source PDF. Raised to 300
DPI (Tez's call, print-scan-grade sharpness over file size). Deliberately kept as
a single code constant (`PDF_RENDER_DPI`) rather than an Admin-UI setting — a
rarely-changed technical knob doesn't need a settings-table entry, and an
isolated constant is already a one-line change if the value needs revisiting.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2.4.

### Convert Archives lands in the existing Processing Tools section, not a new "Archive Tools" section
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** Tez's initial framing proposed a new "Archive Tools" admin section. The
Processing Tools section (§12) already exists for exactly this category of work —
CAPT-ported, pre-ingest filesystem utilities — and File Rename already lives
there as §12.1, with Convert Images and Flatten Archive (Items 7/8) also slated
for the same section. A second parallel section would split functionally
identical tools across two admin headers for no structural reason.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2 (placed under the
existing §12 header), `comicvault-changes-v2.4.md` Item 6.

### BUG-014: diagnosed live (with browser automation) before writing any fix, rather than trusting the existing written diagnosis
**Decided:** 2026-07-08, BUG-014 fix session.
**Why:** BUG-014 had already been "fixed" twice before (2026-06-21, 2026-06-22)
and resurfaced both times — Tez explicitly asked for a full diagnostic pass,
including manually navigating the real app and recording outcomes, rather than
another quick patch on top of the existing (pre-v2.6-redesign) diagnosis, because
the bug's behavior had felt too inconsistent to trust a code-reading-only
explanation. That instinct was correct: live testing found Chrome's back/forward
cache was intermittently masking the underlying (fully deterministic) code
defect, which is almost certainly why the two prior fixes looked like they'd
worked in manual spot-checks but hadn't actually addressed the root cause.
**Where:** `archive/bugs-fixed-archive.md` BUG-014 entry, `v2.6/progress.md`
2026-07-08 session.

### BUG-014 fix: dead `from=` param cleanup bundled into the same session, sequenced after verification
**Decided:** 2026-07-08, BUG-014 fix session (Tez's call, asked directly).
**Why:** The fix made ~4 spots of `from=` query-param construction
(`buildStripCard()`, `buildCoverCard()`, `buildIssueRow()`, `initSeries()`)
provably dead — they'd already stopped being read by the back-link logic back in
the 2026-06-21/22 fix, but only became safe to prove dead once every surface
switch reliably wrote real URL state (removing any chance a `from=` value was
silently load-bearing somewhere backward-compatible). Bundled as a final
sub-step in the same session rather than a separate follow-up, but deliberately
sequenced *after* the behavioral fix passed its full verification pass, so a
regression from cleanup couldn't get conflated with a regression from the fix
itself.
**Where:** `frontend/js/app.js` (`buildStripCard()`, `buildCoverCard()`,
`buildIssueRow()`, `initSeries()`).

### BUG-014 fix: Admin page's back link left unchanged
**Decided:** 2026-07-08, BUG-014 fix session (Tez's call, asked directly).
**Why:** `admin.js`'s back-link implementation is a separate, near-identical
`history.back()` call, but structurally unrelated to BUG-014's mechanism — its
only entry point is a literal `href="/"`, it never routes through
`switchSurface()` or the app's `surface=` URL convention, so it was never
exposed to this defect and already works correctly today. Hardening it anyway
would have been scope creep against a working control with no bug to fix.
**Where:** `frontend/js/admin.js` (unchanged).

### BUG-015 fix: generalized scoped-view banner instead of a Genre-dropdown "Clear" row
**Decided:** 2026-07-08, BUG-015 fix session (Tez's call, after being presented
with the alternative).
**Why:** Tez's initial proposal — add a "Clear" first row to the Genre filter
dropdown — was investigated and found to only solve the genre case. Fieldview
(the actual mechanism behind the bug) is reached via genre tags, writer/artist
credit links, and admin-configured home strips (publisher/format/decade/year/
rating/B&W too) — there's no dropdown at all for writer/artist in the toolbar,
so a Genre-dropdown-only fix would have left one of the two primary entry
points with no clear mechanism whatsoever. Generalized the Series detail
page's existing BUG-010 banner pattern (a scoped-view indicator + a
real-navigation clear link) for the fieldview surface instead — it already
solved the identical shape of problem, and a real navigation sidesteps the
"JS state vs. URL" desync class of bug BUG-014 had just been fixed for.
**Where:** `frontend/js/app.js` (`renderFieldviewBanner()`), `archive/
bugs-fixed-archive.md` BUG-015 entry.

### BUG-015 fix: writer/artist fieldview display name carried via URL `label=` param, not resolved client-side from the id
**Decided:** 2026-07-08, BUG-015 fix session.
**Why:** Fieldview's `value` for writer/artist is a `Person.id`, not
human-readable. Resolving it via an extra API round-trip (e.g. fetching
`/browse/writers` on every writer/artist fieldview load) was rejected in favor
of carrying a `label=` query param, since the two credit-link-construction
sites already have the person's display name in scope at the moment the link
is built (BUG-014's shared `parseSurfaceState()`/`buildSurfaceUrl()`/
`writeSurfaceUrl()` path made adding a fourth param straightforward). The one
site without a name in hand client-side — admin home-strip "view all" links —
gets it resolved server-side instead (`field_value_label` in
`backend/routers/home.py`, mirroring `admin.js`'s existing
`ensureHsPersonNameCache()` pattern for the same underlying problem), since
that endpoint already has DB access and this avoids a second round-trip on
every library page load.
**Where:** `frontend/js/app.js` (credit links, `stripViewAllHref()`),
`backend/routers/home.py` (`_resolve_added_strip()`).

### Folder View "← Back" button replaces the Root/segment breadcrumb
**Decided:** 2026-07-09, v2.6 UI tweak-pass session — Tez's explicit call.
**Why:** Folder View's breadcrumb (`Root / 1981 / …`) let you jump directly
to any ancestor level, which a single "← Back" button can't do — only one
step at a time. Tez asked for the trade anyway, specifically because
`BUG-014`'s fix (2026-07-08) made `window.history.back()` reliable app-wide;
before that fix, a simple back button risked landing on the wrong place,
which is presumably why Folder View had a breadcrumb instead of the same
back-button pattern Series/Issue already used. Reusing that exact pattern
(`history.back()` when possible, `href="/"` fallback) also means the
underlying `pushState`-per-folder-level history is untouched — browser back/
forward, refresh, and bookmarks still land on the right level; only the
on-page control changed.
**Where:** `frontend/js/app.js` (`renderFolderBreadcrumb()` removed,
`renderFolderView()`), `frontend/index.html` (`#folderBackBtn`,
`#folderSearchLabel`), `frontend/css/style.css`, `CUSTOM_TABS_SPEC.md` §9.6.

### Publisher filter dropdown removed from Browse filters, kept as a Group By option
**Decided:** 2026-07-09, v2.6 UI tweak-pass session — Tez's explicit call.
**Why:** Tez asked to remove the Publisher dropdown from the secondary
filters row specifically (not Group By, a separate control that also lists
Publisher). Required removing every reference to `activePublisher` (pool
filter, Folder View filter, `hasActiveFilters()`, `clearAllFilters()`,
`bindSelect()`) rather than just the `<select>` markup — `populateFilterDropdowns()`'s
`addOpts()` helper has no null-guard on a missing element, so leaving the
population call in place would have thrown on every page load and silently
broken every *other* filter dropdown too, not just Publisher.
**Where:** `frontend/index.html`, `frontend/js/app.js`, `MENU_BAR_SPEC.md` §2.7.

### "Read" button removed from Issue detail
**Decided:** 2026-07-09, v2.6 UI tweak-pass session — Tez's explicit call.
**Why:** The button deep-linked via `comicvault://read/{id}`, a custom URL
scheme only the Flutter app registers a handler for. On a plain desktop
browser it did nothing — there's no web reader (`BUG-021`, `SPEC.md` §11,
by design). Removing it doesn't fix or worsen `BUG-021`; it just removes a
non-functional-outside-the-Flutter-app affordance from the page it was
confusingly sitting on. `buildStatusToggle()`'s "Mark as Read" button is a
separate, unrelated control and was not touched.
**Where:** `frontend/js/app.js` (`buildIssueDetail()`), `frontend/css/style.css`
(`.btn-read` removed), `SPEC.md` §11, `BUGS.md` BUG-021.

### Clear Filter pill unified across both trigger paths
**Decided:** 2026-07-09, v2.6 UI tweak-pass session, after two rounds of
back-and-forth with Tez pointing out the two paths still looked/sat
differently.
**Why:** Two independent systems both surface a "you're filtered, clear it"
affordance — the dropdown-filter `#filterClear` button and the fieldview
banner's own `.fieldview-banner-clear` link (reached via a Genre/Writer/
Artist link on an issue/series page). They'd drifted to different visual
treatments and different positions. Rather than pick one "correct" version
and special-case the other, gave both elements one shared CSS rule (solid
`var(--accent)` background, `var(--on-accent)` text — matching the collapsed
sidebar's single-letter Library badges, which Tez identified as the
reference "active" look) and moved `#filterClear` out of `#browseFilters`
into `.menu-bar-trailing`, the same slot the fieldview banner already used.
Deliberately did **not** add a "Field: Value" text label for the dropdown
case to match the fieldview banner's full layout — dropdown filters can be
several at once (Genre + Format + B&W simultaneously), and there's no single
"Field: Value" that unambiguously represents that combination the way
fieldview's always-exactly-one-field/value pair does. Position and pill
styling were the concrete, repeatedly-flagged complaint; the label text
wasn't asked for beyond the position/colour fix.
**Where:** `frontend/index.html`, `frontend/css/style.css`,
`frontend/js/app.js` (`renderFieldviewBanner()`), `MENU_BAR_SPEC.md` §2.7.

### Login/no-password modal narrowed via `.login-modal`, not the shared `.editor-modal`
**Decided:** 2026-07-09, v2.6 UI tweak-pass session.
**Why:** `.editor-modal` is shared by the login popup, the "no password set"
dialog, and the much larger Editor Basic/Full metadata-editor modals. Tez
asked to shrink the login popup by 60% with a tighter 10px inset — scoped
every change to `.login-modal` (already present on both the login popup and
the no-password dialog, applied alongside `.editor-modal`) so the Basic/Full
Editor modals are completely unaffected.
**Where:** `frontend/css/style.css` (`.login-modal`), `frontend/login_popup.html`
(`#loginCancelBtn`), `frontend/js/auth.js` (`hideLoginPopup()`), `ADMIN_SPEC.md` §7.1.2.

### Issue Detail cover restored as a comicvault:// link, protocol registration is manual not automatic
**Decided:** 2026-07-14, v2.6 Item 6 build session.
**Why:** The "Read" button removed 2026-07-09 (see the earlier "'Read'
button removed from Issue detail" entry) was removed because clicking it
did nothing — no Windows registry entry existed for the `comicvault://`
scheme, so the browser had no handler to hand the link to. That's now
fixed (the Windows Flutter reader, built as v2.6 Item 5, can register
itself), so the same underlying trigger is worth restoring — but as the
cover image itself rather than a separate button, since the cover is the
natural click target and a dedicated "Read" button reads as redundant next
to it.

Two things Tez confirmed explicitly before building, both real judgment
calls rather than obvious defaults: (1) scope is the Issue Detail page's
cover only — Browse/Series grid cards keep navigating to their detail
pages, not straight into the reader, since jumping past the detail page
from a grid would be a bigger behaviour change than just wiring up a page
that already had no other purpose for its cover click; (2) protocol
registration (a Windows registry write) happens via an explicit "Register
as this PC's comic reader" button in Settings, not automatically on every
app launch — modifying the registry, even a per-user key needing no admin
rights, should be a visible, deliberate action rather than something the
app does silently in the background.

The same-machine-only limitation flagged when this feature was originally
scoped and parked (`ROADMAP.md`) is real and inherent to a custom URI
scheme — not something this build could solve, only document.
**Where:** `frontend/js/app.js` (`buildIssueDetail()`), `frontend/css/style.css`
(`.issue-cover-link`), `flutter_app/lib/services/protocol_handler_service.dart`,
`flutter_app/lib/screens/settings_screen.dart`, `flutter_app/windows/runner/main.cpp`,
`SPEC.md` §11/§19, `ADMIN_SPEC.md` §7.6, `ROADMAP.md`.

### Card redesign: border carries no colour at all — read-state and favourite signals moved off it entirely
**Decided:** 2026-07-15, card redesign session (v2.6 Item 9), after several earlier
rounds had the border carrying colour.
**Why:** The build went through real iteration here, not a single call: first the
border was blue/green by read state; then favourite added a second stacked gold
ring outside it ("looked off," per Tez); then favourite was changed to replace the
read-state colour outright instead of stacking. Once Tez compared the accumulated
result at 100% card size against the original design reference, he asked to strip
it back further — one uniform border, no colour signal on it at all. Read-state
colour now lives only on the new genre ribbon (a 2px bottom border); favourite is
heart-badge-only; flagged-for-review is icon-only (the old red border removed too).
Multi-select's "selected" state is the one exception left — a temporary, unrelated
UI state, not a persistent card attribute, so it still turns the border gold.
**Where:** `frontend/css/style.css` (`.cover-card--redesign` box-shadow rules,
`.card-genre-ribbon`), `SPEC.md` §20.20.

### Card redesign: Home Strip cards widened rather than shrinking the design to fit
**Decided:** 2026-07-15, card redesign session, Round 2 (Home Strips extension).
**Why:** Home Strip cards were flex-pinned to `width: var(--card-min)` (~90-120px),
meaningfully narrower than the main grid's cards, which grow via `minmax(...,1fr)`.
The redesign's badges/ribbon/progress-pill are fixed-size, sized for the wider grid
card, and would crowd or overlap at the old strip width. Asked Tez directly: scale
the badges down to fit, or widen the cards to fit the badges? He chose to widen
(`max(var(--card-min), 160px)`) — a deliberate Home-page layout change (fewer cards
visible per strip before scrolling), not a cosmetic-only fix, so worth recording as
a real functional/layout tradeoff rather than assuming it was implied by "apply the
card design."
**Where:** `frontend/css/style.css` (`.continue-strip .cover-card.strip-card.cover-card--redesign`),
`SPEC.md` §20.20.

### Inbox triage paused indefinitely — capture-only in every session type
**Decided:** 2026-07-16, per Tez directly.
**Why:** Tez wants `INBOX.md` to keep working purely as his own entry/tracking log
for bugs, changes, and features for the foreseeable future — no session type
(Chat, Cowork, or Code) should triage it off its own initiative, including Code
opportunistically triaging it mid-session because it noticed the file growing.
Triage resumes only when Tez deliberately opens a Code session for that purpose
and says so explicitly. This doesn't change anything about how entries get
written into `INBOX.md`, or how triage itself works once it's switched back on —
only when it's allowed to run.
**Where:** `docs/meta/working-rules.md` "Inbox workflow", `docs/INBOX.md` header.

### Desktop reader Scroll-mode progress: fraction-of-scroll-extent estimate, not exact per-item tracking
**Decided:** 2026-07-17, fixing BUG-024 (Scroll mode never reported or resumed
reading progress).
**Why:** Scroll mode's `ListView.builder` has no native "current page" concept
the way `PageView.builder` does — getting an exact answer would mean tracking
each item's real rendered pixel extent (via per-item `GlobalKey`s or a
`RenderBox` lookup) or pulling in a package like `scrollable_positioned_list`
for its `ItemPositionsListener`. Chose a much simpler estimate instead:
`page = round((scrollController.pixels / maxScrollExtent) * (count - 1))`,
and the same formula inverted to resume position. This is only an
approximation — comic pages have slightly different rendered heights
depending on aspect ratio, and network images resolve their real height
asynchronously after the initial layout guess — but comic pages within a
single issue are close enough to uniform aspect ratio that the drift in
practice is small, and it added zero new dependencies for what is otherwise a
one-file fix. If this estimate turns out to be too imprecise in practice
(e.g. issues with a mix of full-page splash art and dense multi-panel pages),
revisit with real per-item extent tracking then rather than pre-emptively
building it now.
**Where:** `flutter_app/lib/widgets/comic_page_view.dart`
(`_handleScrollProgress()`, `_scrollToPage()`), `archive/bugs-fixed-archive.md`
BUG-024.

### Full Editor's no-XML filename fallback: repoint the existing dormant shim to `rename_tool`'s parser, not write new remap code
**Decided:** 2026-07-19, scoping Tez's request to wire filename parsing into the
Full XML Editor for files with no `ComicInfo.xml`.
**Why:** `backend/editor/xml_parser.py::parse_filename_for_comicinfo()` already
existed with exactly the Series/Number/Year/Title field-remapping this needed —
but it was wired to `backend/scanner.py::_parse_filename()` (the scanner's minimal
internal fallback, used for the full-library scan) and was never actually called
from anywhere. The Filename Editor's own parser
(`backend/rename_tool.py::parse_comic_filename()`) is the tested,
scene-release-tolerant one Tez actually meant — it's already reused once outside
its home file, by CT Auto-Tag's `ct_bridge.py::identify_file()`. Repointing the
existing shim's import and return-key remap to call that parser instead reused
built infrastructure and fixed a latent inconsistency in the same move, rather
than adding a second, parallel piece of remap code. `scanner._parse_filename()`
itself was left untouched — its own internal callers in the scanner are a
separate, unrelated use.
**Where:** `backend/editor/xml_parser.py` (`parse_filename_for_comicinfo()`),
`backend/routers/editor_full.py` (`get_file_xml()`), `EDITOR_SPEC.md` §3.1/§9.4.

### Mobile "Titles per page" setting: reactive `ValueNotifier`, `SegmentedButton`, own 25/50/75/100 range
**Decided:** 2026-07-24, building the Flutter mobile reader's new pagination
setting (follow-up to v2.6 Item 4).
**Why:** Settings is pushed via
`Navigator.of(context, rootNavigator: true).pushNamed('/settings')`
(`lib/widgets/app_top_bar.dart`) — on the *root* navigator, so a `BrowseScreen`
underneath stays mounted and is never recreated or otherwise notified when the
user backs out. A plain getter/setter (the pattern used for `readingMode`)
would leave a still-open library screen showing a stale page size/count until
some unrelated nav-rail reselection happened to recreate it. Gave the new
`itemsPerPage` setting the same `ValueNotifier<int>` treatment already used for
`themeMode`, and had `BrowseScreen` listen directly, so a change takes effect
immediately on return. Chose `SegmentedButton<int>` (plain "25"/"50"/"75"/"100"
labels, no icons) over a dropdown for the 4 options, since every other
choice-style setting on this screen (`_AppearanceTile`, `_ReadingModeTile`)
already uses `SegmentedButton` — a dropdown would've been the only tap-to-open
menu on the page. The option range itself (25/50/75/100) is deliberately
different from the web app's own page-size control (50/100/200/500, see
`ADMIN_SPEC.md` §6) — smaller, phone-appropriate numbers for a narrower screen
and slower mobile scroll; the two controls were never meant to be the same
range, so no reconciliation was needed.
**Where:** `flutter_app/lib/services/settings_service.dart`
(`itemsPerPageNotifier`/`itemsPerPage`), `flutter_app/lib/screens/settings_screen.dart`
(`_ItemsPerPageTile`), `flutter_app/lib/screens/browse_screen.dart`.

### Mobile Scroll-mode pinch-zoom: wrap the whole `ListView`, not per-item, with a dynamic `panEnabled` toggle
**Decided:** 2026-07-24, adding pinch-zoom to the Flutter reader's Scroll mode
(Page mode already had it via `InteractiveViewer`).
**Why:** Wrapping each `ListView.builder` item in its own `InteractiveViewer`
was the more obvious first approach but doesn't work — `InteractiveViewer`
needs bounded constraints, while Scroll-mode items currently size themselves
from the image's own intrinsic aspect ratio inside an unbounded-height list
(`fit: BoxFit.fitWidth` + `width: double.infinity`, no explicit height);
giving every item a fixed size just to make that work would have meant
either pre-fetching image dimensions or an `AspectRatio` estimate, adding
real complexity. Wrapping the *entire* `ListView` in one `InteractiveViewer`
instead sidesteps this completely — the list still gets the same bounded
constraints from its parent as before, and `InteractiveViewer` only applies
a paint-time scale/pan transform over the whole scrolling strip (the same
approach most continuous-strip/webtoon readers use). The remaining problem —
`InteractiveViewer`'s single-finger pan competing with `ListView`'s own
scroll drag in the gesture arena — is solved by leaving `scaleEnabled`
always on (2-finger pinch never competes with 1-finger scroll) but toggling
`panEnabled` dynamically: off at scale 1.0 so drags reach the list normally,
on above 1.0 so drags pan the zoomed image instead (list scroll pauses until
the user pinches back out). This is a known/standard pattern for this exact
`InteractiveViewer`-in-`Scrollable` conflict, not a novel workaround.
**Where:** `flutter_app/lib/widgets/comic_page_view.dart`
(`_scrollPanEnabled` field and the `InteractiveViewer` wrap in
`ComicPageViewState._buildScrollMode()` and
`LocalComicPageViewState.build()`'s scroll branch).

### Full Editor "+ Queue" readiness fields = Genre/Format/Age Rating (not Series or any other field)
**Decided:** 2026-07-25, implementing "turn + Queue blue once required
fields are filled."
**Why:** Tez's request didn't enumerate which fields count as "required," so
the field set had to be inferred. Chose Genre (≥1 chip) + Format + Age
Rating specifically because these are the only fields the codebase already
treats as "required" anywhere: they're the exact three fields `backend/
editor/validation.py::validate_enforced_fields()` checks server-side at
process time, and they're the exact three fields Basic Editor's own Save
button already gates on (`editor_basic.js::updateSaveButtonState()` —
`anyGenreChecked && formatSet && ratingSet`). Extending the same three
fields to Full Editor's Queue button keeps "required" meaning one consistent
thing across both editors instead of inventing a second, editor-specific
definition. Series was considered (it's required elsewhere, e.g. Search
Online) but excluded — it's not part of the enforced-dropdown set and isn't
what either editor currently blocks Save/Process on.
**Where:** `frontend/js/editor_full.js` (`updateActionButtonStates()`),
`frontend/css/style.css` (`.btn-admin-action.is-ready`).

### Tray app opens pages via Edge/Chrome `--app=` mode, not an embedded webview library
**Decided:** 2026-07-25, implementing "open pages in the app window instead
of the browser."
**Why:** Two ways to get an app-like window: (1) launch the system browser
with the Chromium `--app=<url>` flag, which opens a chromeless window (no
tabs/address bar) as a normal subprocess, or (2) embed a real webview
(e.g. `pywebview`) inside the tray process itself. Chose (1) — no new
dependency in `requirements.txt`, no change to the tray app's threading
model (a `pywebview` window needs its own run loop, which would compete
with `pystray`'s `icon.run()` for the main thread), and it reuses
whichever of Edge/Chrome is already installed and already logged in to any
site-specific state, rather than spinning up a separate cookie-less
embedded browser profile. Tradeoff accepted: each click launches a new OS
process/window rather than reusing one persistent embedded view, and it
depends on Edge or Chrome being installed (checked at runtime, falls back
to a normal `webbrowser.open()` tab if neither is found).
**Where:** `tray/tray_app.py` (`open_app_window()`,
`_find_app_browser_exe()`).

### `stress-test` skill deliberately runs a second server instance — an exception to `perf-diagnostics`'s "never start a second server" rule
**Decided:** 2026-07-29, building the stress-test skill.
**Why:** `perf-diagnostics`'s ground rules forbid starting a second server
because that skill measures the *live* tray-app instance against the real
DB — a second instance would be a different, uncomparable measurement.
`stress-test` has the opposite requirement: it needs to fire concurrent
scans/edits/rebuilds against data nobody cares about, which the live
instance can't safely provide. So it runs a fully isolated second
instance — its own copy of `backend`/`frontend` source, its own synthetic
library, its own DB, port 9427 (never 9424) — built fresh by
`0_setup_scratch.py` every run and torn down after. This isn't a relaxation
of the "never touch the real DB/library" rule, it's the same rule applied
via a different mechanism (isolation instead of avoidance), because this
skill's entire purpose requires triggering real writes concurrently.
**Where:** `.claude/skills/stress-test/SKILL.md` ("Ground rules" section
states this explicitly, to head off a future session assuming it's an
oversight).
