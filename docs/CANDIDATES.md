# Candidates

Five ideas, scored against what `docs/INTEL.md` says the track actually rewards. The
first one written down is included and did not win, which is the point of writing five.

Scoring is 1–5 on the four things that decide this: whether ClickHouse is load-bearing
(25% of the track score), whether the agent *acts* (§2 of the intel), how crowded the
idea is, and whether it can be built and proven in 26 days.

| | ClickHouse load-bearing | Agent acts | Uncrowded | Buildable | Σ |
|---|---|---|---|---|---|
| A · Answer Print — delivery QC | 3 | 3 | 5 | 3 | **14** |
| B · Live QoE incident agent | 5 | 5 | 4 | 4 | **18** |
| **F · Raccord — continuity errors** | **5** | **4** | **5** | **4** | **18** |
| C · Ad-break integrity | 4 | 3 | 5 | 2 | **14** |
| D · Cut/variant performance | 4 | 1 | 2 | 4 | **11** |
| E · Leak detection from telemetry | 3 | 2 | 5 | 1 | **11** |

---

## A · Answer Print — delivery QC against a spec

The first idea, and written up in full before the research was done. Still a good product.

**Why it lost.** Frame-level QC is a few million rows *per title*, batch, and computed
once. It is a perfectly reasonable ClickHouse table and an entirely reasonable Parquet
file, which is exactly the outcome the P0 kill gate was designed to detect — better to
detect it now than on 17 Aug. It also acts only at the end, on a copy, offline: the
"agent acts" story is real but tame.

**What survives.** The insight that a false pass costs more than a false fail carries over
intact, and applies harder when the blast radius is a live audience.

## B · Live QoE incident agent — **chosen**

During a live event, playback telemetry streams in at millions of events per minute.
Quality drops. The agent localises the fault across CDN × region × ISP × device × player
version × ladder rung, says which combination explains it, proposes a mitigation, and
executes it only where it has earned the right to.

**Why it wins on every axis.**

- **ClickHouse is the product.** Attribution is a combinatorial scan over billions of rows
  answered in seconds. This is the "impossible on another database" case the track asks
  for, and it benchmarks cleanly: the same search on Postgres is the before/after.
- **It acts, in the workflow.** CDN failover, ladder change, player config rollback. The
  same shape as Gitdefender, which won the Google Cloud grand prize by fixing rather than
  reporting.
- **The blast radius is enormous**, which is precisely why nobody lets software do it
  today, and precisely what the earned-autonomy architecture is for. The carried-over
  spine stops being reuse and becomes the reason the product is possible.
- **The pain is documented**, not imagined: 27% of teams report ongoing difficulty with
  root-cause identification.

**Risks, stated now.** No real live event to point at, so telemetry is synthesised with
injected faults — legitimate only if declared everywhere it is reported. And "did it find
the right cause" needs ground truth, which means the fault injector must record what it
injected and the agent must never see it.

## C · Ad-break integrity

Server-side ad insertion fails quietly: the break plays, the impression does not count,
the money does not arrive. High-cardinality, real revenue, genuinely uncrowded.

**Why it lost.** Building a credible SSAI pipeline plus a beacon model inside 26 days is
most of the budget before the agent exists, and the domain needs explaining before a judge
can see why it matters. B has the same data shape and a problem that explains itself.

## D · Cut and variant performance

Which trailer variant retains viewers, which cold open loses them. Good ClickHouse fit.

**Why it lost.** It is analytics. The agent recommends and a human decides, which is the
read-only advisor pattern the last project spent a month arguing against. Also the most
crowded idea here after generation.

## E · Leak detection from playback telemetry

Spot piracy by session fingerprints in the telemetry.

**Why it lost.** Ground truth is unobtainable in 26 days, so nothing could be measured,
and a security claim that cannot be measured should not be made.

---

## F · Raccord — continuity errors — **chosen, replacing B**

Scored level with B on the original four axes, and then beat it on two the first table did
not have, which is a fault in the table rather than a tie.

| | B · Live QoE | F · Raccord |
|---|---|---|
| Is it *cinema* | infrastructure carrying video | a named craft role |
| Is **Gemini** load-bearing | no — the search is SQL | yes — "is this an error" is judgement |
| Ground truth | my own fault injector | published listings, written by other people |
| Prior art | Conviva, Mux Data, Watchdog | little |
| Design surface | a dashboard | two frames, side by side, with the difference |

The two axes I had left out are the ones that decide it. **Gemini load-bearing** is half
the brief's opening sentence. **Ground truth I did not write** is the difference between
a measured claim and a demonstration.
