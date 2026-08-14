# Decisions

Each entry records the option not taken, because a decision whose alternatives are
unrecorded gets relitigated every time someone new reads the code.

---

## D1 · Build the thing that ships film, not the thing that makes it — SUPERSEDED BY D4

**Date:** 14 Aug 2026. Superseded the same day, after the market study that should have
come first. Kept in full because the reasoning that replaced it reused half of this.

Every obvious entry to a hackathon called *Agentic Cinema* generates: trailers, 
storyboards, synthetic actors, edit assistants. With 5,676 registered, the generation
space is where the crowd is and where a judge has seen forty variants before lunch.

The industry bottleneck is delivery, not creation. Masters get rejected against
specifications, rejections cost days on a fixed date, and the tools that check for it
produce tens of thousands of undifferentiated flags that a human still has to read.

**Not taken:** a trailer cutter, which would have demoed better in ten seconds and been
indistinguishable from the field by minute two.

**Risk accepted:** delivery QC is unglamorous, and "Design" is a judging criterion. The
answer is that the design work goes into making a refusal legible, which is exactly the
thing the domain has never had.

## D2 · ClickHouse, and it has to earn it

**Date:** 14 Aug 2026

One partner track per submission, so this is a single bet. ClickHouse chosen because a
feature-length title is single-digit millions of telemetry rows and the questions asked of
it are analytical — worst window, longest run, aggregate over a filtered range.

**Not taken:** Grafana, which fits the dashboard half but would leave the data layer
unexplained; Replit and IBM, where the integration would more easily become a wrapper.

**Held open:** P0 is a kill gate. If a flat file is within 2× on the three benchmark
questions, this decision was wrong and the track changes. That is written into
`docs/PLAN.md` with a date rather than left as good intentions.

## D3 · Carry the engineering spine, not the product

**Date:** 14 Aug 2026

The gates, the authority ratchet, the re-deriving verifier, the append-only ledgers and
the post-commit reviewer all carry over from Geminga. They answer *whether an agent may
act*, and that question does not change with the domain.

Everything above them is new: the spec compiler, the finding model, the triage, the
repair inverses, the calibration harness.

**Not taken:** starting from a blank scaffold, which would have spent a week re-deriving
lessons that are already written down and already cost something to learn.

**Not taken either:** reusing the product framing. Cost optimisation and delivery QC share
an architecture and nothing else, and a submission that reads as a reskin deserves to lose.

## D4 · Live QoE incident response, not delivery QC — SUPERSEDED BY D5

**Date:** 14 Aug 2026. Superseded the same day. The reasoning about *where the crowd is*
and *that winners act* survived; the domain did not.

`docs/INTEL.md` changed the picture in three ways, and D1 was written before any of them
were known.

1. The ClickHouse track weights *use of ClickHouse* at 25% and rewards "use cases
   impossible on other databases" shown with "before/after benchmarking". Frame-level QC
   is a few million rows per title, computed once, in batch. That is a fine ClickHouse
   table and an equally fine Parquet file.
2. The agent hackathons that have actually been judged were won by agents that **act
   inside an existing workflow** — Gitdefender writes the fix and opens the review.
   Delivery QC acts offline, on a copy, at the end.
3. The canonical media workload on ClickHouse is not QC at all. It is **live playback
   telemetry**: Sony LIV, Mux and Vimeo all run it, and Mux monitors the world's largest
   livestreams on it.

So: an agent that works a live streaming incident. It localises a quality drop across
CDN × region × ISP × device × player version, and mitigates it under earned authority.

**Not taken:** ad-break integrity, which is equally uncrowded and needs most of the 26
days to build a credible pipeline before the agent exists. See `docs/CANDIDATES.md`.

**What this makes of the carried-over architecture.** Under D1 the gates and the ratchet
were reuse. Here the blast radius is a live audience of millions, which is the reason no
one lets software do this today — so the earned-autonomy spine stops being a convenience
and becomes the thing that makes the product possible at all.

**Declared risk:** there is no real live event to point at. Telemetry is synthesised with
injected faults. That is legitimate and must be declared in the README, the film and the
Devpost write-up, and the fault injector's ground truth must never be visible to the
agent.

## D5 · Continuity errors on a film set, not streaming infrastructure

**Date:** 14 Aug 2026

D4 was scored against the four published criteria instead of against how much I liked it,
and it failed two of them.

- **Quality of idea.** The hackathon is called Agentic Cinema. A CDN failover agent is an
  SRE product that happens to carry video. It is infrastructure, not cinema.
- **Technological implementation.** ClickHouse was load-bearing and *Gemini was not*: the
  localisation is SQL and the model only chose the next query. That is the decorative-
  partner failure I keep warning about, with the roles swapped, in a brief whose first
  line is "powered by Gemini".
- **Innovation.** Conviva, Mux Data and Datadog Watchdog already do anomaly attribution
  for streaming. An expert judge knows that.
- **Evidence — the disqualifying one.** No real event, so ground truth came from my own
  fault injector. Geminga survived a synthetic estate because its claims were about
  *refusal*, which is verifiable whatever the data. D4's core claim was "it finds the real
  cause", and a synthetic exam I wrote cannot support it.

**Raccord** finds continuity errors — the glass that refills, the day that becomes night
across a cut — by comparing everything in a scene against everything else in it.

**What makes it better on every axis that failed:**

- It is a named craft role. Productions employ a person to do exactly this.
- Gemini is unavoidable: whether a difference is an *error* is judgement about the
  physical world, not a distance threshold.
- ClickHouse is unavoidable: all-pairs within one three-minute scene is ~18 million
  comparisons, and the product only exists because they are affordable.
- **The ground truth is third-party and public.** IMDb and moviemistakes.com publish
  continuity-error listings for films that are verified public domain. Somebody else wrote
  the exam.

**Not taken:** dailies triage (focus, exposure, boom in shot), which shares the shape but
has no public ground truth; and territory-compliance cutting, which is high-impact,
politically fraught, and has no labels.

**The inversion is inverted, deliberately.** Geminga defaulted toward refusing because a
false pass cost more. On a set a false *alarm* is the expensive one: stop a shoot for a
moving leaf twice and the tool gets switched off, costing everything it would ever have
caught. So Raccord earns the right to interrupt, and precision is the metric.

**Declared risks.** Public domain status is verified per film and recorded, not assumed.
Published listings are used as facts — a timecode and a claim — never reproduced as text.
Precision reviewed by us is weak evidence and gets labelled as such.

## D6 · The transition search is portable; the ClickHouse story is the store, not this query

**Date:** 14 Aug 2026

`evals/partner_benchmark.py` was built to be the before/after the ClickHouse track
rewards. It produced an honest, inconvenient result: once the contradiction search is
partitioned by (work, entity, attribute, slot), the partitions are small and every
partition-respecting engine — the ClickHouse window, a SQLite LAG, a plain Python loop —
stays near-linear. A Python loop is the *fastest* column at every scale to 112k rows.

So the strong claim I had been making — "a scan over billions of rows, impossible on
another database" — is false for this query, and our own tool falsifies it. The rule is
the project's own: when a measurement disagrees with a claim, the claim changes.

**What changes.** The film, the README and the write-up must not say the transition search
needs ClickHouse. They say what is true: the naive row-store formulation (a correlated
self-join) does balloon ~17x by franchise scale, and ClickHouse earns its place as the
*store* for the full workload — this search run repeatedly and concurrently, alongside
ingest and the appearance-embedding entity-resolution scans that need vector similarity
and structured predicates in one query. That last workload is the genuine "hard
elsewhere" case, and it is the one still unbuilt.

**What does not change.** The partner requirement (MCP server → cluster → runtime) is
satisfied and deployed regardless. And the differentiation from the prior art — the 92%
reachability figure — is a property of the method, not the database, so it stands
untouched.

**Not taken:** quietly keeping the "impossible without ClickHouse" line because it sounds
better. That is the exact move this project refuses, and a ClickHouse judge with a laptop
would falsify it in the time it takes to write a Python loop.
