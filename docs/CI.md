# Agentic CI/CD

The gates in `docs/GATES.md` are the pipeline. CI runs them; it does not invent its own
standards, because two sets of standards means the weaker one wins.

## On every push

| Stage | Gate | Blocking |
|---|---|---|
| lint + types | — | yes |
| unit tests | — | yes |
| spec lint | G1 | yes |
| determinism | G2 | yes |
| authority + wiring | G3 | yes |
| calibration | G4 | no — reports, does not block |

Calibration reports rather than blocks on purpose. A blocking accuracy threshold creates
pressure to tune the number, and the number is the thing we are trying to observe
honestly. It is published on every run and a regression is visible; it just does not get
to be the reason someone quietly changes a label.

## On every deploy

`deploy-prober` runs against the deployed URL and its report is attached to the
deployment. Deploys are not considered complete until it has run, because on the previous
project every deploy-time bug was invisible to the test suite and obvious to one request.

## What CI must never do

- **Never regenerate a claimed number without also updating the claim.** If calibration
  moves, the README moves in the same commit or the build is wrong.
- **Never auto-merge on green.** Green means the gates passed, which is a floor.
