# Working Rules

These are the habits Tez and Claude have settled into over this project —
originally established across Chat, Cowork, and Code sessions; Code is now
the master controller for all of it (see "Master controller" below). Follow
them the same way here.

## Master controller (settled 2026-07-12)
Claude Code is the master controller for this project — planning, triage,
build, and docs all happen in a Code session with Tez directly. This
replaces the old three-way split (Chat for planning/triage, Cowork for
nightly drift-scanning, Design for UI mockups, Code for building), now that
Cowork's Drive-based access is gone for good (see "Cowork nightly doc-scan
(retired 2026-07-12)" below — the scan was cancelled and won't be running
again) and session continuity is covered by two other layers instead: a
`SessionEnd` hook that drops a plain-text conversational summary into
`the_brain` (a personal, cross-project record — separate from, and
additional to, this project's own docs), and this project's own doc set
(`progress.md`, `CHANGELOG.md`, `DECISIONS.md`, etc.) exactly as this file
already describes. Neither replaces the other.
**Exception:** outside planning docs — a Design mockup, notes from a Chat
conversation Tez had elsewhere — still get dropped into the repo as
reference material when they exist. They're input to a Code session, not a
required upstream stage Code waits on.

## Decision-making
- Ask one clarifying question at a time, not a list of three or four at once.
- If something Tez asks for conflicts with what's already in the docs, say so
  and ask rather than quietly picking a side or silently overriding it.
- Don't assume priority or sequencing — if there's more than one thing that
  could happen next, ask which order, don't guess.
- When something is genuinely ambiguous or has real trade-offs, lay out the
  options and the reasoning behind each rather than giving one confident
  answer that hides the judgment call.
- Tez's own written instructions to you (in chat, in this file, anywhere)
  won't always be tightly worded — he's said so himself. Read for intent,
  ask if genuinely unclear, and feel free to suggest a tighter version of
  something he's asked for rather than executing a literal but clunky
  instruction.
- **Plain-English companion for technical plans (added 2026-07-15, broadened
  2026-07-16).** The technical plan produced in Plan Mode is what Code
  actually works from in auto-mode — keep it, in full, every time. But
  that's not what Tez reads to decide whether to approve it: every Plan
  Mode plan gets a short plain-English paragraph alongside the technical
  plan — what's actually changing, in non-technical terms, and the
  practical impact/risk. This now applies to every plan, not just ones that
  look "genuinely technical" — the judgment call about which plans need
  simplifying was itself a source of drift. This is additive — keep the
  full technical plan too, don't replace it. Grew out of a real session
  (2026-07-15, the legacy credit-column drop) where an overly technical plan
  left Tez unable to confidently approve or reject it until it was
  re-explained in plain terms.
- **Reporting back to Tez (settled 2026-07-16).** When explaining an issue
  or a proposed change, two things only: (A) confirm you understand what
  the issue actually is — one line, not a full technical report; (B) state
  plainly whether the change has any negative impact on the current working
  state — "if you change X, the impact is Y on Z." If there's no negative
  impact, say so explicitly rather than leaving it implied. If Tez needs to
  do something manually, say so explicitly. Don't proactively dump extra
  detail he hasn't asked for — if he needs more, he'll ask for it. Keep the
  whole response short — a few sentences, not a report.

## Structural vs. cosmetic threshold (settled 2026-07-08)
- Small UI changes don't need to go through the full process (scoping, a
  build-queue item, a bug ticket, `DECISIONS.md` entry) the way features and
  bugs do. The line: **cosmetic** (colour, spacing, typography, copy, element
  position/sizing within an existing layout) needs none of that — just make
  it and note it in `progress.md`. **Structural** (navigation, routing,
  information architecture) still follows the full scope→docs→build→docs→git
  workflow (see "Master controller" above — run entirely in a Code session
  now) and gets a `DECISIONS.md` entry, same as always.
- If it's ambiguous — a cosmetic-looking change that touches shared
  components, state, or data flow — treat it as structural and ask rather
  than assume it's "just styling." See `CLAUDE.md` Section 5 for the same
  rule stated for Code sessions.

## How the docs are structured (don't treat them all the same)
- **`docs/vN.M/`** — the current version's own working folder, created fresh each
  version: `comicvault-changes-vN.M.md` (the build plan — what's next, in what
  order; the one doc allowed to change shape as priorities shift) and `progress.md`
  (narrative log, scoped to just this version's sessions, append-only). When a
  version closes, **the whole folder moves into `docs/archive/vN.M/` as one
  bundle** — don't pick it apart into separately-rotated files; anyone digging into
  that version's history later should find everything together in one place. The
  next version's folder is created fresh once Tez has the next batch of work
  defined — there isn't always an active one.
- **`BUGS.md`** — always-active, but **open bugs only**. A fixed bug moves out to
  `archive/bugs-fixed-archive.md` rather than staying in the live file — that
  archive is flat, not version-scoped, since a bug found during one version can get
  fixed during a later one and shouldn't need hunting across multiple version
  folders to find. Move fixed entries out promptly rather than letting them
  accumulate in the live file; don't wait for a dedicated cleanup session.
- **`SPEC.md`, `EDITOR_SPEC.md`, `CUSTOM_TABS_SPEC.md`, `HOME_STRIPS_SPEC.md`,
  `MENU_BAR_SPEC.md`, `ADMIN_SPEC.md`** — reference docs for features that are
  already built. "Done" doesn't mean "retired" — these stay the live reference for
  how that feature actually works, and only get a Change Log entry when reality
  diverges from what they originally said (e.g. a deliberate deviation from the
  original design). They don't drive what gets built next; the active
  `docs/vN.M/comicvault-changes-vN.M.md` does that. Crucially, **these are not
  version-scoped** — closing a version never moves a feature spec to archive. A
  spec only retires when the feature it describes is replaced or removed, which is
  a much rarer event than a build queue closing.
- **`ROADMAP.md`, `TESTING.md`** — same logic as the feature specs: span every
  version by design, never move to archive just because a version closed.
- **`INBOX.md`** — raw, unsorted capture only (bugs/changes/features Tez jots as
  they occur to him). Not authoritative for anything — see "Inbox workflow"
  below for how items move out of it.
- **`docs/archive/`** (not `historical/` — renamed 2026-06-29) — closed-out version
  folders, fixed-bug history, one-time setup docs. **Out of focus, not out of
  mind** — Code has full access any time something needs revisiting. Don't
  write or speak about this folder as if its contents no longer matter.

## Inbox workflow
- Tez captures freely into `INBOX.md` — paper, phone, whatever's at hand,
  consolidated there when convenient. No formatting expected beyond the tag
  (`[bug]` / `[change]` / `[feature]` / `[unknown]`) he assigns as he writes
  it. The tag is his instinct at the time, not a final classification.
  **`INBOX.md` is Tez's personal scratchpad, entry-only (settled
  2026-07-16, restated 2026-07-18 after Code wrote an unprompted entry
  into it mid-session)** — Code never adds to it, edits it, or triages it
  unprompted, and doesn't need to factor its contents into unrelated work
  either. It's not a queue Code works down on its own, and it's not a
  place for Code to park findings from a session (stray bugs, doc drift,
  decisions to revisit later) just because they seem inbox-shaped — surface
  those directly in conversation instead and let Tez decide where they go,
  if anywhere. The only exception is a session Tez explicitly opens to work
  through Inbox items (see "Session shape" and "Triage is on hold" below).
- **Session shape for working through Inbox items (settled 2026-07-16).**
  When Tez does open a session to work through Inbox items: small/cosmetic
  UI changes get bundled together into one session covering several of them
  at once; a larger change (a feature, or anything needing real scoping)
  gets its own dedicated session. This governs how the *work* is split
  across sessions — it's additive to the tagging/placement/archive mechanics
  below, not a replacement for them.
- **Triage is on hold, effective 2026-07-16, until Tez says otherwise.**
  Chat and Cowork sessions never triage the Inbox — they're entry-only, same
  as always. Code sessions don't triage opportunistically either while this
  hold is in effect: capture-only applies everywhere now. Triage happens
  only when Tez deliberately opens a Code session for that purpose and says
  so explicitly ("let's work through the inbox," or points at specific
  lines) — it is not a background task Code initiates on its own, and
  finding an aging or growing Inbox during an unrelated session is not a
  cue to start triaging it. When that instruction comes, the rest of this
  section (below) describes how triage works.
- Real classification and placement happens in a triage session (run in
  Code, per "Master controller" above, and only when Tez explicitly starts
  one per the hold above) — going through each line, expanding it with
  enough detail to be useful, deciding where it actually belongs (`BUGS.md`,
  `comicvault-changes-N.M.md`, `ROADMAP.md`, or directly noted in
  `progress.md`), and writing it there properly.
- If Tez's original tag turns out to be wrong once discussed, the tag in
  `INBOX.md` is **not corrected** — it stays exactly as first entered, with a
  note on what it actually got filed as. This is deliberate: the mismatch is
  the record Tez wants kept, so a repeated pattern (e.g. consistently tagging
  something a `[bug]` when it's really a `[change]`) can be pointed out
  in-session, against past examples, rather than silently smoothed over.
- Once triaged, the line gets struck through in `INBOX.md` and annotated with
  where it landed. Struck-through lines 7+ days old move to
  `inbox-archive.md` on a Sunday prune. Unprocessed lines never get pruned by
  age — only triage moves them out.
- **Triage includes a placement decision, not just a destination doc.** For
  each item: where does this sit on `meta/roadmap.html` — Now (it's part of
  the active build queue), Next (ordered — state where in the sequence and
  why), or Later (parked, no committed order unless one's been explicitly
  given)? This is a separate question from which doc the item's detail goes
  in (`BUGS.md` / `comicvault-changes-vN.M.md` / `ROADMAP.md`) — a bug can go
  straight into `BUGS.md` without touching the roadmap at all (bugs ride along
  with whatever's being built, they're not their own lane), but a feature or
  change needs an explicit Now/Next/Later call, not a default.
- `meta/roadmap.html` is **regenerated wholesale**, never hand-edited
  piecemeal — same convention as `build-plan.html`. It updates at two points:
  during a triage session (new item placed, or an existing item's lane/order
  changes), and after a Code session if that session's work changes what's
  Now or Next (an item completes, something blocks the next item, scope
  shifts). It is a readable snapshot, not a source of truth — if it ever
  disagrees with `ROADMAP.md`, `BUGS.md`, or `comicvault-changes-vN.M.md`,
  those win.
  - **Item-completion update is the one Code-session edit that's a targeted
    hand-edit, not a wholesale regen (settled 2026-06-29):** remove the
    completed item's card from its lane, decrement the lane's `lane-count`,
    and renumber the remaining cards' `order-badge` sequence back to a
    contiguous 1..N. "Wholesale regeneration" describes triage sessions
    re-deciding placement/order across the whole board — a Code session
    closing out one item is a narrower, mechanical edit and doesn't need a
    full triage pass to do it. See `CLAUDE.md` Section 4 for the exact
    mechanics. The `Item N` reference inside each card (pointing at
    `comicvault-changes-vN.M.md`) is untouched by this renumber — only the
    display-order badge shifts, never the doc's actual item number.

## Versioning
- Version labels (`comicvault-changes-vN.M.md`) stay coarse — one number per build
  queue, no finer-grained SemVer-style scheme (`v2.4.545` etc.). That granularity
  exists to help multiple independent consumers track compatibility across releases
  of something they depend on; digib00age has one deployment and one user, so there's
  no compatibility surface to track and no one to read the extra precision.
- The version label is tied to an actual git ref via a lightweight tag at close-out
  time — see `CLAUDE.md` Section 7 for the convention. This is the one piece that's
  actually load-bearing: it turns "what shipped in v2.3" from something only
  reconstructable by reading docs into a real, checkout-able point in history.

## Quality bar (carried over from how Claude Code works on this project)
- Never touch real library files when testing or verifying anything — use
  scratch copies.
- **The dev DB is disposable (settled 2026-07-18).** `comicvault_v2.db` is
  development data and gets wiped before production. Read/unread states and
  saved page positions in it are artefacts of testing, not real user
  history — don't weigh them as something to preserve when a wipe or rebuild
  is on the table, and don't propose export/restore ceremony around them.
  The real asymmetry is the bullet above: the archives on `L:` are
  irreplaceable, the DB isn't. Wiping it is routine — flag it plainly, take
  a `.bak` copy, move on. See `CLAUDE.md` Section 6 for the same rule stated
  for Code sessions.
- A change isn't "done" until it's actually been checked working, not just
  written and assumed correct.
- Clean up any test data or scratch files created during verification.
- **Doc updates wait for a passing manual test, not just a passing code-level
  check (settled 2026-06-29).** A unit test or scratch script proves the logic
  is internally consistent, but it can still miss the actual intended
  behaviour — e.g. v2.4 Item 1's first pass blocked remote admin access
  correctly at the code level, but hid the cog icon entirely instead of just
  disabling it, which wasn't the intention and also shifted the Login button.
  Sequence going forward: implement → Tez manually tests → **passes** → write
  docs. If the manual test fails or reveals a mismatch, fix and re-test before
  writing anything to `progress.md`/`CHANGELOG.md`/the spec — don't leave
  docs describing a round that didn't actually pass.

## Scope discipline
- Genuinely new ideas that come up mid-conversation go into a fresh doc to be
  discussed properly later — not folded into whatever's already agreed and in
  motion. Tez has explicitly said this is how he wants ad hoc ideas handled.
- Decisions, once confirmed, don't get silently revisited. If you think a past
  decision should change, say that explicitly and ask — don't just act
  differently next time without flagging it.
- **Personal, non-project notes don't belong in any project doc, including
  `INBOX.md`.** Confirmed 2026-06-29 after a personal brainstorming aside (a
  reminder to check a draw.io tutorial video) ended up sitting in `ROADMAP.md`
  for two days. `INBOX.md`'s four tags (`[bug]`/`[change]`/`[feature]`/`[unknown]`)
  are for things that are, or might be, actionable project work — not a catch-all
  for any thought that occurs mid-session. Tez now keeps purely personal notes in
  his own external records, not in this repo at all.

## Version lifecycle (settled 2026-06-29, starting with v2.4)
- Tez brings everything intended for a version in one go — a closed, numbered list
  agreed with Code before any building starts. No new items get added to that list
  once it's finalized; genuinely new ideas go to `INBOX.md` or the next version.
- **Scoping output goes directly into its permanent home doc** (`ADMIN_SPEC.md`,
  `SPEC.md`, whichever governs it) — never into a separate standalone scoping
  fragment. This is the fix for how `admin-spec-section-12-processing-tools.md`
  ended up an orphan: it was scoped with nowhere permanent to land yet. Writing
  scope straight into its final home means there's nothing left to "fold in"
  later — it was already there.
- `docs/vX.Y/` holds only `comicvault-changes-vX.Y.md` (the build queue) and
  `progress.md` (the session log). Build → test → fix, one item at a time, before
  moving to the next — not all-scope-then-all-build. Tez's call, 2026-06-29: this
  keeps quality tighter per item, even though it means scoping sessions happen
  interleaved with build sessions rather than batched.
- At version close: confirm anything still only living in the version folder that
  should be permanent has actually been written into its real home, then move the
  whole `docs/vX.Y/` folder into `docs/archive/vX.Y/` as one bundle (already
  established — see "How the docs are structured" above).

## Version-qualified references (settled 2026-06-29)
- **Never write a bare "Item N" in any doc** — always write "v2.3 Item 12" or
  "v2.4 Item 10". Item numbers reset every version, so "Item 13" is ambiguous the
  moment more than one version exists. This is what actually caused the
  2026-06-29 Item 12/13 mixup in `ROADMAP.md` — a bare number with no version
  attached.
- `BUG-NNN` IDs stay exactly as they are — flat, unversioned, no change. But a
  bug's "Found" line should reference the version-qualified item if one's
  relevant ("Found: v2.3 Item 12 manual test pass", not "Found: Item 12 manual
  test pass").

## Cowork nightly doc-scan (retired 2026-07-12)
- `docs/` used to be a Windows directory junction into a Google Drive folder
  specifically so Cowork could run a nightly scan for drift/contradictions
  across the doc set (logged to `doc-scan-issues.md`, tracked in
  `doc-scan-state.md`, configured via `cowork-doc-scan-instructions.md`). Tez
  no longer needs Google Drive in the loop, so the junction was removed and
  `docs/` is now a plain folder in the repo — see `CLAUDE.md` Section 2.
- That removes the mechanism the nightly scan relied on. The three
  scan-specific files above have been moved into `docs/archive/` as a
  point-in-time record, alongside the already-archived `cowork-notes.md` and
  `doc-scan-issues-archive.md`. **The scan itself was cancelled and won't be
  running again (confirmed 2026-07-12)** — this isn't "no replacement yet,"
  it's retired for good. Doc consistency is Code's job directly now (see
  "Master controller" above), backed by the `SessionEnd` hook's per-session
  summary and this project's own doc set — no scanning mechanism in the
  loop at all.

## 3rd Party Apps
- ComicTagger Repo has been cloned into D:\workshop\3rd_party_apps\ComicTagger. You will be asked to view the source code and either use or adapt what you find. When using or adapting code from a third-party reference repo, add a comment at the point of use in this format:
# Adapted from <Project Name> (<License>) - <relative path in source repo>

Example: # Adapted from ComicTagger (Apache 2.0) - comictagger/scanner.py