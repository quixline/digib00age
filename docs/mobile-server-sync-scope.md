## SCOPE: Mobile ↔ Server Reading-State Sync

Scoped 2026-07-05 (Cowork discovery session). Ready for Code — see `ROADMAP.md`
"v2.5 — holding list" Item 2 for hand-off status.

**The actual problem:** Reading progress currently lives only on whatever device
you're reading on. There's no shared source of truth, so progress made offline
(e.g. on a tablet with comics downloaded for a trip) doesn't show up in the library
elsewhere until manually reconciled — and there's no defined behavior for what
happens if the same comic's progress diverges between devices before a sync
happens.

**Who it's for:** Just you — single-user dogfooding scenario (tablet with
downloaded comics, home server as source of truth). Not designing for concurrent
multi-user or multi-device-active-simultaneously yet.

**Status quo today:** No sync exists. Reading state is per-device, no persistence
back to server, no offline/online distinction tracked at all (per `SPEC.md`).

**Smallest version:**
- Reading state tracked locally on tablet client, independent of connectivity —
  grain is (last page read, timestamp of that update) per comic
- Sync path: tablet → server, one direction is the primary case (progress made
  offline gets pushed up); server → tablet on next open handles the reverse
  (resume a comic started elsewhere)
- Sync triggers: manual ("sync now" action) and on network reconnect/app
  foreground — timer-based sync is a nice-to-have, not required for v1
- Library view on server reflects last-synced progress per comic, with a visible
  "last synced" indicator so stale state is never presented as current
- Basic conflict rule defined and implemented (even if simple): last-write-wins by
  timestamp (see Open Questions — this is the recommended default, not yet
  eng-confirmed) — must be an explicit, documented rule, not implicit behavior

**Deliberately excluded (for now):**
- Multi-device concurrent sync (phone + tablet + web all writing at once) —
  tablet+server only for v1
- Real-time/live sync while online — this is checkpoint sync, not continuous
  streaming
- Any UI/UX polish beyond a functional sync status indicator
- Automatic conflict merge logic beyond one simple, stated rule
- Timer-based background sync (manual + reconnect-triggered is enough to start)

**Kill signal:** If the conflict rule turns out to be hit often enough that "one
simple rule" doesn't hold up in practice (progress gets silently overwritten
wrong, or you find yourself needing to manually pick which device's state wins
more than rarely), that's the sign the offline model needs a rethink before going
further — not a sign to bolt on more special-casing.

**Fit check:** On-strategy — natural next layer once core library/reading features
are stable, no tangent here.

**Open questions for eng review:**
- What's the actual grain of "reading state" being synced — confirmed as (last
  page number, timestamp) per comic. This affects both storage and conflict
  comparison.
- Conflict rule: with (page, timestamp) tracked, default is last-write-wins by
  timestamp — confirm this over highest-page-wins (a re-read/rewind should be able
  to move progress backward, which highest-page-wins would block).
- Sync trigger set: confirmed manual + reconnect/foreground for v1 — does
  reconnect detection already exist on the tablet client, or is that new plumbing?
- Failure/partial sync handling: if a sync is interrupted mid-transfer, does it
  retry, roll back, or leave state ambiguous? Needs an explicit answer before this
  is "done."
- Auth/session validity for sync calls after extended offline periods (e.g. a
  week-long trip) — does the existing session model already handle this or does
  it need attention here too?
