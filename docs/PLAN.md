# Plan

Deadline: **plan to 7 Sep 2026**, not the 9th. The rules page and the trade press both
say the 7th while the front page says the 9th; see `docs/REQUIREMENTS.md`. Today is 14
Aug. **Twenty-four days.**

Phases are sequenced so that the thing most likely to be wrong is tested earliest. The
riskiest assumption is not the agent — it is whether frame-level telemetry in ClickHouse
actually answers spec questions better than a flat file would. If that is false the
partner choice is decorative and we should know in week one, not week four.

Each phase ends at a gate in `docs/GATES.md`. A phase is done when its gate passes, not
when its code exists.

---

## P0 · Prove the partner is load-bearing — by 17 Aug

Before any agent work. The track weights *use of ClickHouse* at 25% and rewards
before/after comparisons, so this is a deliverable rather than a warm-up.

- [ ] Telemetry generator: a live-shaped event, six dimensions at realistic cardinality,
      with a fault injected on a known schedule and the ground truth written where the
      agent cannot read it
- [ ] Land it in ClickHouse continuously, from the generator, while queries run
- [ ] The localisation query: for a breached window, rank dimension combinations by how
      much of the excess they explain
- [ ] Same localisation against a row-store baseline on the same data
- [ ] Publish both timings and both implementations

**Kill criterion:** if the baseline is within 2× at 50M rows, the partner choice is
decoration. Say so in `docs/PARTNER.md` and change track — there would still be 23 days.

**Loop, not a march.** Generate → land → localise → time → widen the data → repeat. Each
pass raises the row count and adds a dimension. The interesting number is where the
baseline stops being viable, and finding it requires walking up to it.

## P1 · The spec compiler — by 21 Aug

- [ ] Spec file format: threshold, unit, scope, citation. Citation is mandatory.
- [ ] One real spec encoded, clause by clause, with sources
- [ ] Each clause compiles to a query and a comparison
- [ ] A clause without a citation fails to load, loudly

## P2 · Findings and triage — by 26 Aug

- [ ] Finding record: clause, timecode, measured value, threshold, severity
- [ ] Gemini classifies *will be rejected* vs *will not*, given the finding and the clause
- [ ] The model sees measurements and clauses. It never sees filenames, embedded metadata
      or anything else an upstream vendor writes.
- [ ] Findings re-derived from the store at verification time

## P3 · Repair under authority — by 31 Aug

- [ ] Repair classes, each declaring its inverse
- [ ] Gates ahead of every repair, carried over from the previous project
- [ ] Ratchet: rehearse against a copy, commit under verification, then under sampling
- [ ] Verifier re-measures the output rather than trusting the repair's own report

## P4 · Calibration — by 3 Sep

- [ ] Labelled set: masters with known verdicts, including synthesised defects, declared
      as synthesised
- [ ] False-pass and false-fail measured separately, with intervals
- [ ] Published in the repository next to the claim it supports

## P5 · Deploy, film, submit — by 8 Sep

- [ ] Hosted URL, Agent Builder in the runtime path
- [ ] Three-minute trailer. It must show a refusal.
- [ ] `docs/PARTNER.md` showing the ClickHouse calls
- [ ] Open source licence, public repo, Devpost form

**One day of margin, deliberately.** Last time the final day was spent finding six wiring
bugs in a deployed service that every test had passed.

---

## Task breakdown convention

A task is written so that its completion is checkable by someone who was not there:

- **Bad:** "improve the extractor"
- **Good:** "extractor writes luma stats for a 10s clip into ClickHouse; `SELECT count()`
  returns 240 rows; a second run against the same clip produces identical rows"

Anything that cannot be written that way is not a task yet, it is a topic.
