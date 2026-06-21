# Working Rules

These are the habits Tez and Claude (Chat) have settled into over this
project. Follow them the same way here.

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

## How the docs are structured (don't treat them all the same)
- `progress.md` and `BUGS.md` — always-active logs. Append, never rewrite
  history.
- `comicvault-changes.md` — the only active build plan. What's next, in what
  order. This is the one doc that's allowed to change shape as priorities
  shift; the others below generally aren't.
- `SPEC.md`, `EDITOR_SPEC.md`, `CUSTOM_TABS_SPEC.md`, `HOME_STRIPS_SPEC.md` —
  reference docs for features that are already built. "Done" doesn't mean
  "retired" — these stay the live reference for how that feature actually
  works, and only get a Change Log entry when reality diverges from what they
  originally said (e.g. a deliberate deviation from the original design).
  They don't drive what gets built next; `comicvault-changes.md` does that.

## Quality bar (carried over from how Claude Code works on this project)
- Never touch real library files when testing or verifying anything — use
  scratch copies.
- A change isn't "done" until it's actually been checked working, not just
  written and assumed correct.
- Clean up any test data or scratch files created during verification.

## Scope discipline
- Genuinely new ideas that come up mid-conversation go into a fresh doc to be
  discussed properly later — not folded into whatever's already agreed and in
  motion. Tez has explicitly said this is how he wants ad hoc ideas handled.
- Decisions, once confirmed, don't get silently revisited. If you think a past
  decision should change, say that explicitly and ask — don't just act
  differently next time without flagging it.
