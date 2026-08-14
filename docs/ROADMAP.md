# V2 and V3 — what was built, and what is still a bet

Implemented as tested modules on 14 Aug 2026. "Implemented" here means *the buildable
core, unit-tested and validated against the real three-film corpus* — not the full
multi-month vision. Each entry says plainly whether it is engineering (works, or is a
mechanism with no research risk) or a research bet (works in principle, precision or
end-to-end value unproven), with the criterion that would kill it.

89 tests pass. All eight modules are importable and unit-green; the notes below are from
running them on the real corpus, which is where the honest limits show.

## V2 — state and canon

| Module | Status | Live finding |
|---|---|---|
| `worldstate.py` | **engineering (correct), research (precision)** | `state_at` builds a real 70–137 fact world model per film. `global_inconsistencies` is *correct* but fires on extraction-vocabulary noise — 62 "reverts" on Detour are mostly `dark combed hair`↔`dark slicked-back hair`, not errors. **Kill/next: value canonicalization; if the revert detector can't beat the pairwise diff on measured precision after canonicalization, it stays a research note, not a feature.** |
| `verify.py` | **engineering** | Consensus, symmetric re-verify, adversarial skeptic — the precision rigor. Deterministic, tested. Not yet run at scale (costs K× the calls); it is the lever for the measured precision number V1 lacks. |
| `embed_resolve.py` | **research bet** | Cross-film entity resolution: vector similarity + structured predicate in one ClickHouse query (`cosineDistance`, verified in chdb). This is the workload that makes ClickHouse genuinely load-bearing. Tested on fake vectors; **unproven until run on real Vertex appearance embeddings — that is the bet.** |
| `frame_of_reference.py` | **engineering** | The structural fix for V1's left/right false positives: world-relative (a watch on a wrist) vs camera-relative (screen side). A person's own left/right never flips with the camera. Tested. |

## V3 — script and set

| Module | Status | Live finding |
|---|---|---|
| `bible.py` | **engineering (works on real data)** | The living continuity bible: a timecoded, per-entity table of established facts, derived from the store and rendered to markdown. Runs on the real corpus today — a genuine deliverable, not a scaffold. |
| `ratchet.py` | **engineering** | The earned right to interrupt — SHADOW → PROVISIONAL → LIVE per error class, one bad call demotes, append-only ledger, restrict-only. The mechanism from Geminga, finally in the domain where a false alarm is the expensive failure. Deterministic, tested. Vestigial until there is a set to interrupt (V3 proper). |
| `script.py` | **research bet** | Intended world-state and per-scene `must_match` contracts from the screenplay — the upstream, predictive move. The `must_match` path is the reason it exists: footage internally consistent but wrong about what the script established. Tested on mocks; **unproven until run on a real screenplay against real footage.** |
| `propose.py` | **engineering** | Detect → propose the fix: within-scene contradiction → use the alternate take; cross-scene → flag for pickup or note to the bible. Deterministic decision, tested. |

## The honest shape of it

V1 was a diff engine. These modules are the skeleton of V2 (a maintained world model + the
rigor to trust it + the cross-film store that needs ClickHouse) and V3 (the script contract,
the interrupt ratchet, the bible, the fix proposal). The engineering pieces work. The three
research bets — the world-state precision after canonicalization, cross-film resolution on
real embeddings, and the script contract on a real screenplay — are exactly the three places
the value is unproven, and each has a criterion above that would kill it rather than let it
coast on a green unit test.

That is the same discipline as the P0 partner gate: a bet is a bet until it is measured.
