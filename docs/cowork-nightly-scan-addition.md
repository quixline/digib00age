# Addition to Cowork's Nightly Doc Scan — Inbox Monitoring

This isn't a standalone doc Cowork reads on its own — it's instruction text
to fold into the existing nightly doc-scan scheduled task's prompt/config
(the one that already produces `doc-scan-issues.md` entries and the daily
summary message to Tez). Paste the relevant part into that task's setup.

---

## New step: check INBOX.md

In addition to the existing consistency-scan work, each nightly run should:

1. Read `INBOX.md`.
2. Count lines under "Unprocessed" (i.e. not struck through).
3. Find the oldest unprocessed line's date, if dated; if lines aren't
   individually dated, note the file's last-modified time as a fallback
   signal instead.
4. Include both in the nightly summary message to Tez, e.g.:
   > 4 items sitting in INBOX.md, oldest about 3 days old.
   - If there are zero unprocessed items, a short "Inbox's clear" line is
     enough — don't omit the line entirely, since a consistent presence/
     absence is itself useful signal.
5. This is a passive nightly nudge only. Do **not** attempt to triage,
   classify, or move INBOX.md items — that only ever happens in a live
   session between Tez and Claude Chat. Cowork's role here is visibility,
   not action.

## Sunday prune addition

On the existing Sunday prune pass (the one already pruning
`doc-scan-issues.md` into its archive), also move any **struck-through**
`INBOX.md` line that is 7+ days old into `inbox-archive.md` (create the file
on first use, same append-only convention as other archives). Leave
unprocessed lines untouched regardless of age — only triaged/struck-through
lines are eligible for pruning.

## No reclassification role

Cowork should never correct or flag a mismatched tag in `INBOX.md` (e.g. a
`[bug]` that was actually triaged as a change) — that comparison is something
Claude Chat does deliberately, in-session, against the archive history, as
a way of helping Tez notice his own classification patterns over time.
Cowork's job stays limited to reporting volume and age, same as it does for
every other doc in scope.
