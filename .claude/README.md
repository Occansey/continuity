# Subagents, skills and hooks

## Subagents

| Agent | When |
|---|---|
| `spec-auditor` | Every phase boundary, before starting the next phase |
| `calibration` | Whenever a number about accuracy is about to be claimed anywhere |
| `deploy-prober` | After every deploy, without exception |

They exist to ask questions the author is worst placed to ask about their own work. Each
gets a brief and the relevant clause, never a transcript: handing context is how a
subagent inherits the mistake you wanted it to find.

## Hooks

Two, both cheap and both about a rule that is easy to break quietly:

- **ruff on Python edits** — style drift is not worth a review comment.
- **spec files must cite** — a threshold with no source is the failure mode the
  specification calls out by name, and a hook catches it at the moment it is written
  rather than at the gate.

Hooks that would slow an edit to a crawl belong in CI instead. See `docs/CI.md`.
