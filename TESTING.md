# ComicVault — Testing & Verification Standard

Standing verification approach for any Claude Code session on this repo. Expands
`CLAUDE.md` Section 6 into a concrete runbook. Every close-of-session checklist
(`CLAUDE.md` §4) requires stating what was checked and how — this is the "how."

---

## Ground rules (non-negotiable)

- **Never touch real library files or Tez's real `Processing` folder during testing.**
  Always use scratch copies. Confirm afterward that real files are untouched.
- **Backend changes:** verify against scratch DB rows/files where possible. If the
  feature only touches a small file (a JSON list, a config value) rather than the main
  DB, a documented backup-and-restore of that one file is an acceptable substitute for
  a full scratch DB — see the pattern below.
- **UI changes:** verify live where practical, check for console errors, confirm no
  real file was touched unless that specific save action is the thing under test and
  has been explicitly approved.
- **Always clean up.** Temporary values, scratch files, and any tooling installed
  purely for verification should not be left behind at session end.

---

## Backend verification pattern: diff against a pre-test backup, byte-for-byte

For any change that writes to a file ComicVault depends on (`genres.json`,
`formats.json`, `config.json`, etc.), don't just check the *content* round-trips —
check the *bytes* do too:

```bash
cp backend/editor/genres.json /tmp/genres_backup.json   # before touching anything
# ... exercise the feature with throwaway values, end by removing them again ...
diff /tmp/genres_backup.json backend/editor/genres.json && echo "byte-identical"
```

This matters: during the 2026-06-20 Genre/Format admin editor session, a content-only
check would have passed while the file's line endings had silently flipped from LF to
CRLF (Python's text-mode write translates `\n` → `os.linesep` on Windows unless you
open with `newline=''`). A real `diff` caught it; a JSON-equality check would not have.
Always restore the real file from the backup immediately if a test run leaves it in a
non-original state — don't leave a "temporarily shrunk to one item" or similar
intermediate state sitting in a real config file between steps.

Exercise the actual running server over HTTP (not just calling the Python function
directly) when the change adds or modifies an API route — this is what actually proves
the route, validation, and error responses work end to end, not just the underlying
logic.

---

## UI verification pattern: scratch Playwright, not a permanent dependency

This repo has **no Node/Playwright tooling checked in** — it's a vanilla-JS frontend
with no build step. Don't add `package.json`/Playwright as a project dependency just
to verify one session's UI change. Instead, set up a throwaway instance outside the
repo:

```bash
mkdir -p /tmp/cv-verify && cd /tmp/cv-verify
npm init -y
npm install playwright@<version>
npx playwright install chromium
```

Drive the **already-running** real server (`python start_server.py`) with a small
script: `chromium.launch()` → `page.goto('http://localhost:8000/...')` → act
(`fill`/`click`) → `screenshot()` → check `page.on('console', ...)` for `error`-type
messages and `page.on('pageerror', ...)`. A few things that bit during the first use
of this pattern:

- The Admin page route is `/admin`, **not** `/admin.html` — check `backend/main.py`
  for the actual registered route before assuming a static filename.
- Settings behind the "Advanced" lock checkbox (`#advancedLock`) still render and are
  present in the DOM even while the fieldset is `disabled` — you don't need to unlock
  it just to assert a list rendered, only to click/type into it.
- For destructive-looking actions like delete buttons, intercept `page.on('dialog', ...)`
  and `dismiss()` it when you want to verify the *cancel* path without actually
  performing the action on real data (e.g. confirming a real in-use value's delete
  confirmation message is correct, without actually deleting it).

Delete the scratch directory (`rm -rf /tmp/cv-verify`) when done. If a future session
finds itself reaching for this pattern often, that's a signal to consider a proper
project-level run/test skill instead of re-deriving it each time (see the `run` skill's
own guidance on this).

---

## After any verification pass

- `git status` / `git diff` should show no unintended changes to real data files —
  only the code/doc files you actually meant to touch.
- If you backed up a real file before testing, confirm it's been restored
  byte-identical (per the diff pattern above) and then remove the backup.
- State explicitly, in the close-of-session summary, what was checked and how —
  "tested" with no detail doesn't meet `CLAUDE.md` §4's bar.
