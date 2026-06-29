# Daily Doc Scan & Telegram Notification — Cowork Task

> **How to use this document:** this is the authoritative copy of Cowork's nightly
> task instructions — paste the body below into Cowork's scheduled task config
> verbatim when it changes, so the live task and this record never diverge. Last
> consolidated 2026-06-28 (folded in Inbox monitoring, folder-scope exclusion, and a
> fix for the `doc-scan-state.md` duplicate-file problem).

---

## Purpose

Every night, scan the project docs folder for anything that's drifted out of sync,
check on the Inbox, and send a short, friendly daily update via Telegram — whether or
not anything's wrong. The message should read like a quick heads-up from a teammate,
not a status report.

---

## Scope

- **In scope:** root-level files directly inside
  `C:\Users\tezdr\My Drive (quixlinedesign@gmail.com)\Dev_Folders\Workshop\comicvault_v2\project_docs`
  only.
- **Out of scope — do not read, scan, or check dates on these at all:**
  - `historical\` — closed-out build queues and one-time setup docs. Not current,
    never flag anything found only in here.
  - `meta\` — Claude-facing working-process docs (`working-rules.md`,
    `voice-and-style.md`, `about-me.md`, `build-plan.html`). Process docs, not
    project facts — not subject to the consistency checks below.
- **`INBOX.md`** is in scope but gets different treatment — see its own section
  below, not the consistency-check categories.

---

## Step-by-step process

1. **Read the last-scan timestamp** from `doc-scan-state.md` (root of the project
   docs folder). If the file doesn't exist, create it (treat this as a first run —
   scan all in-scope docs).

2. **Compare each in-scope doc's modified-date** against that timestamp. Build a
   list of docs changed since the last scan. Don't check dates on anything in
   `historical\` or `meta\`.

3. **Read only the changed docs.** Don't re-summarize unchanged docs or the whole
   project from scratch.

4. **Check each changed doc for issues** (see "What counts as an issue" below). If
   issues are found, append a dated entry to `doc-scan-issues.md` (append-only —
   never overwrite). Each entry includes: the file, the issue category, a one-line
   description, and — if there's something Tez actually needs to *do* about it — a
   short "action needed" note.

5. **Check `INBOX.md` every night, regardless of whether it changed.** This is a
   volume/age check, not a consistency check:
   - Count lines under its "Unprocessed" heading (lines not struck through).
   - Find the oldest unprocessed line's age. If lines aren't individually dated,
     fall back to the file's last-modified time as a rough signal.
   - Don't read for content quality, don't flag mismatched tags, don't suggest
     reclassification, and don't move or edit anything in this file — triage only
     ever happens in a live session between Tez and Claude Chat. This step is
     visibility only.

6. **Write tonight's brief Telegram message** (see "Notification format" below),
   based on what changed in the docs read today, the Inbox check, and the overall
   state of `progress.md`.

7. **Send the Telegram notification** using Desktop Commander. Use `start_process`
   to run this Python command:

   ```
   python -c "import urllib.request, urllib.parse; msg = urllib.parse.quote('YOUR_MESSAGE_HERE'); urllib.request.urlopen(f'https://api.telegram.org/bot8936595317:AAFxS6DK9UkxD9wuFqmBrNKuHIz43338m6A/sendMessage?chat_id=515830540&text={msg}')"
   ```

   Replace `YOUR_MESSAGE_HERE` with the composed message before running. Keep the
   message under 300 characters so the URL stays short. Set `timeout_ms` to 15000.

8. **Update `doc-scan-state.md`**, regardless of outcome, with tonight's timestamp.
   **Use Desktop Commander's `write_file` directly at the local synced path**
   (`C:\Users\tezdr\My Drive (quixlinedesign@gmail.com)\Dev_Folders\Workshop\comicvault_v2\project_docs\doc-scan-state.md`)
   to overwrite it in place. **Do not use the Google Drive `create_file` tool for
   this** — it creates a new file alongside the existing one rather than truly
   overwriting it, which is exactly how a duplicate `doc-scan-state.md` ended up in
   the folder previously. One file, one update method, every night.

9. **If today is Sunday:**
   - Move any entries in `doc-scan-issues.md` older than 7 days into
     `doc-scan-issues-archive.md` (append, then remove from the live file).
   - Move any **struck-through** lines in `INBOX.md` that are 7+ days old into
     `inbox-archive.md` (create it on first use, same append-only pattern).
     Unprocessed lines are never pruned by age — only triage moves them out, so
     leave them untouched regardless of how old they are.

---

## What counts as an "issue" (applies to step 4 only, not the Inbox check)

An issue is something that would actually mislead or trip someone up if left
unflagged — not every small wording change. Use this as the bar: **would this cause
someone to act on wrong information, or notice a contradiction and wonder which doc
is right?** If yes, flag it. If it's just phrasing, formatting, or a harmless typo,
skip it.

**Categories to check, with the threshold for each:**

- **Internal inconsistency** — the doc contradicts itself (e.g., states a deadline or
  number in one section, then a different one later in the same doc).
- **Contradiction with another doc** — two docs make incompatible factual claims
  (e.g., one doc says a feature is "not started," another says it's "in testing").
- **Outdated statement** — a doc states something as current/true that is
  contradicted by a more recently modified doc or by `progress.md` (e.g., a spec
  still describes a discarded approach that `progress.md` shows was replaced two
  weeks ago). **Status/summary blocks at the top of a doc are a recurring hotspot for
  this** — they tend to get left behind when a detail section or change log further
  down gets updated. Worth a second look at top-of-doc status lines specifically.
- **Broken cross-reference** — a doc references another file, section, or doc by
  name that no longer exists or has been renamed/moved.
- **Conflict with `progress.md`** — a changed doc's claims about status, scope, or
  next steps don't match what `progress.md` says is actually happening.

**Worked examples:**
- ✅ Flag: `api-spec.md` says the rate limit is 100 requests/min; `integration-notes.md` says 60/min. → Contradiction with another doc.
- ✅ Flag: `architecture.md` references "see section on caching strategy in storage-design.md" but that section was removed. → Broken cross-reference.
- ✅ Flag: `feature-x.md` describes the comment system as "planned," but `progress.md` logged it as shipped last week. → Conflict with progress.md.
- ❌ Don't flag: a doc was reworded for clarity but says the same thing. Not an issue.
- ❌ Don't flag: a typo or grammar fix needed, with no factual impact. Not an issue.

**Avoiding duplicate noise:** if the same unresolved issue was already logged in a
previous entry and the underlying doc hasn't changed again, don't re-log it every
night. Only re-flag it if the doc itself changed and the issue is still present, or
if it's genuinely a new occurrence.

---

## Notification format

Write this like you're catching Tez at the water cooler — casual, brief, no jargon.
The Telegram message must stay under ~300 characters total. Cover, in priority order
(drop from the end if it won't fit):

1. **One-line status** — no issues / N issues found.
2. **One sentence on what changed today** — plain language. "You fleshed out the home
   strips flow" not "Updated HOME_STRIPS_SPEC.md."
3. **Inbox line** — only mention it if there's something to say: "Inbox clear" if
   zero unprocessed items, or "Inbox: N items, oldest ~Xd" if not. Skip silently if
   you're out of room — don't let this push out item 1 or 2.
4. **One short sentence on what's next** — the natural next thing based on the docs.
   First to drop if space is tight.

**Skip** the "what Tez needs to do" detail in Telegram — if action is needed on a doc
issue, it's already in `doc-scan-issues.md`. The Inbox line is the one exception
(it's a nudge, not a doc issue, so it belongs in the message itself).

**Examples:**
```
ComicVault scan: all clear. Fleshed out the home strips flow. Inbox clear. Next: wire up the strip ordering UI.
```
```
ComicVault scan: 2 issues logged — check doc-scan-issues.md. Inbox: 4 items, oldest ~3d.
```

---

## Hard rules for Cowork

- Never edit the source docs being scanned — flag only (this includes `INBOX.md`:
  report on it, never edit, move, or correct it).
- Never read, scan, or flag anything in `historical\` or `meta\`.
- Never overwrite `doc-scan-issues.md` — append only (except the Sunday prune, which
  removes only entries already copied to the archive).
- Never use the Google Drive `create_file` tool to update `doc-scan-state.md` — use
  Desktop Commander's `write_file` to overwrite it in place, every time.
- Always send the nightly Telegram message, whether or not issues were found — never
  skip it on a clean scan.
- Never invent or guess at progress — base the summary only on what's actually in the
  docs and `progress.md`.
- Keep the Telegram message under 300 characters so the API URL stays short.

---

## Project

ComicVault

## Folders

- `D:\workshop\comicvault_v2`
- `C:\Users\tezdr\My Drive (quixlinedesign@gmail.com)\Dev_Folders\Workshop\comicvault_v2\project_docs`
