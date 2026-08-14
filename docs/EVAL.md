# Evaluations

Two programs under `evals/`. Both run standalone against the checked-in `work/` data with
no cluster, no credentials, and no Gemini call.

## `evals/partner_benchmark.py` — G0, the partner is load-bearing

The before/after the ClickHouse track rewards (`docs/INTEL.md`: "use cases impossible on
other databases", shown with "before/after benchmarking"). It runs the product's actual
contradiction search — the partitioned window from `src/continuity/store.py`
(`TRANSITIONS`) — on the same data at three scales (feature 1x, season ~20x, franchise
~100x, replicated with a distinct `work` id per copy) across four engines:

| engine | what it represents |
|---|---|
| `chdb` | the real store: columnar MergeTree + `lagInFrame` window |
| `py_loop` | a competent engineer with no OLAP engine: group + sort + walk in Python |
| `sqlite_win` | the same SQL on a row store that has window functions |
| `sqlite_join` | the row store the *naive* way: correlated self-join + `NOT EXISTS` |

It prints an equivalence check (the windowed engines must agree on the transition set, or
the timings are noise), a timing table with a `sqlite_join / chdb` ratio, and a plain-
language reading. The reading is deliberately not triumphant: once the search is
partitioned, partitions are tiny and every partition-respecting engine stays near-linear,
so the naive-quadratic framing is false and we say so. The genuine before/after is the
`sqlite_join` column, which balloons as the corpus grows — the failure mode the spec
names — and the point stands that ClickHouse gives the windowed formulation as the natural
indexed path, in-store, next to ingest and the entity-resolution scans.

Run: `./.venv/bin/python evals/partner_benchmark.py`

## `evals/blind.py` — recall against third-party ground truth

A blind exam we did not write (SPECIFICATION.md §8). It holds a frozen, hand-entered list
of documented Detour (1945) continuity errors from published listings, transcribed only as
timecode + short claim. A fixed scope rule (stated in the file before the list) splits them
into IN-SCOPE (cross-scene state or said-vs-shown — what a claims-not-pixels method can
reach) and OUT-OF-SCOPE (within-shot / shot-to-shot goofs — the registration prior art's
domain, which this system deliberately does not chase). It matches each in-scope error to a
transition in `work/transitions.json` by approximate timecode plus entity/attribute
plausibility, then reports recall as `k/n` with a self-implemented Wilson 95% interval, N
printed explicitly, and the caveat that N is tiny and this is one film. It never prints a
bare percentage.

Run: `./.venv/bin/python evals/blind.py`
