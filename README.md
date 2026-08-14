# Continuity

**An agent that finds film continuity errors by comparing claims about the story world
instead of pixels.**

> Continuity is the department whose job is that the world of the story stays the same
> world. Not that the shots match — that the *facts* match. The wound is on the left
> cheek. The ring goes on after the wedding. The dog is still alive.

Read `SPECIFICATION.md` first; it is the contract this repository honours.

Hosted: **https://continuity-468826425509.us-central1.run.app** (`/` is the product,
`/api/health` reports the backend).

## The problem

There are two continuity problems and the industry uses one word for both.

**Shot continuity** — two takes cut together, the glass full then empty — is solved. The
frames look alike, so you register one onto the other and diff the pixels. Pickup &
Zisserman published this in 2009 (CIVR) and a startup is commercialising it now. We do not
do this; see `docs/PRIOR-ART.md`.

**Story continuity** is open, for a structural reason: the shots look nothing alike. A cut
on the left cheek in scene 12, shot in April; on the right in scene 30, shot in June on
another location. Different angle, lighting, sometimes a different year. Nothing registers,
so every pixel method has nothing to say — the 2009 paper is explicit that it operates on
"pairs of shots within a scene" from similar camera angles. Story continuity is also the
harder human job: a script supervisor holds one scene in their head; nobody holds seventy
hours of a series.

## The move

Stop comparing images. Compare claims about the world. For every shot and every line of
dialogue, extract what is *true* — who is present, what they wear and carry, what is
injured and where, the time of day, the weather — with provenance (title, scene, shot,
timecode, confidence). Store the claims. Then find pairs that cannot both be true, given
the order of the story and whether anything in between explains the change.

Two shots that share no pixels can still contradict each other, and contradiction is a
query, not a distance. The most direct case is **said-vs-shown**: in *Detour* the dialogue
places three scratches "about a quarter of an inch apart" while the hand shown has them
roughly three times that — a contradiction with no two frames to compare, invisible to
every pixel method by construction.

## The two-partner division of labour

Neither partner can do the other's job.

- **ClickHouse narrows the search.** Contradiction search is quadratic in story length —
  a feature is thousands of shots, each yielding tens of assertions — so checking an
  attribute's history means ordering and self-joining the assertions and asking, for every
  pair, whether an explaining event lies between them. A windowed query on the cluster
  turns billions of possible comparisons into a shortlist of transitions. The database
  finds transitions; it never judges whether one is an error.
- **Gemini judges the shortlist.** Deciding whether *left cheek → right cheek* is an error
  needs world knowledge and narrative reasoning: that cuts do not move across faces, that
  four days passed, that nothing in between explains it. There is no threshold for that.
  Gemini adjudicates the candidates the database hands it; it does not — and cannot afford
  to — scan the whole corpus and guess.

## How it runs

Continuity runs as a **Google ADK agent** whose only data access is the **ClickHouse MCP
server** (`mcp-clickhouse`), mounted as its toolset over stdio and pointed at a ClickHouse
Cloud cluster at runtime. Gemini reasons about *which* contradiction to look for; the MCP
server runs the SQL against the cluster; Gemini reads the rows back and never touches the
database directly. The exact call sites are listed in `docs/PARTNER.md`; the cluster setup
is in `docs/CLICKHOUSE.md`.

The hosted app additionally queries the same cluster directly per request for the product
page (`/api/search`), so a visitor sees a live query rather than a fixture.

## Reachability — why this is not the prior art

The claim that separates this from registration-based tools is "we reach pairs a
registration method cannot". We measured it rather than asserting it, by running the prior
art's own technique — ORB features, RANSAC homography, counting geometric inliers. Below
15 inliers no homography fits and no registration-based tool reaches the pair.

| pairs | unreachable by registration |
|---|---|
| our findings (cross-scene + flagged errors) | **146 / 159 — 92%** |
| control: two frames 0.5s apart, same shot | 2 / 60 — 3% |

So on *Detour* (1945), about 92% of what Continuity finds connects frames a
registration-based method cannot line up, against about 3% for guaranteed-same-camera
pairs. This is classical computer vision, not a model — it runs the competitor's actual
method and shows where it stops. Regenerate with `evals/reachability.py`.

## Running it

The film is not committed. Fetch it and its provenance first:

```bash
scripts/fetch_corpus.sh          # downloads Detour (1945) to corpus/, prints its sha256
```

The pipeline, in order (extraction and transcription call Gemini; both need credentials):

```bash
python scripts/extract.py        # world-state assertions from sampled frames
python scripts/transcribe.py     # dialogue, and the assertions the dialogue makes
python scripts/segment.py        # scene boundaries and story order
python scripts/resolve_and_judge.py   # entity resolution, re-search, adjudication
python scripts/contradictions.py # load assertions, find transitions (local chdb)
```

Stand the cluster up and drive the agent through the MCP server per `docs/CLICKHOUSE.md`
(create a ClickHouse Cloud service, `scripts/load_cluster.py`, then
`scripts/run_agent.py`). Serve the app locally with the `Procfile` command
(`uvicorn app.main:app`).

Check the submission's outside-facing claims — hosted URL, licence, partner call sites —
with:

```bash
CONTINUITY_URL=https://continuity-468826425509.us-central1.run.app bash scripts/preflight.sh
```

## Limits

Stated plainly, because the specification requires it.

- **One film.** *Detour* (1945), 68 minutes, 494×360, public domain. Small footage, one
  title, one genre. Its rights basis is widely asserted but not yet independently confirmed
  (`corpus/MANIFEST.md`).
- **Precision is not independently measured.** The search demonstrably finds cross-scene
  and said-vs-shown contradictions no pixel method can reach, but the count of true errors
  rests on a small, self-adjudicated sample on a film we chose. It must not be quoted as a
  precision figure; see `docs/FINDINGS-P0.md`.
- **The cluster is on a free trial**, and story-time ordering, entity resolution, and the
  attribute schema each still have known failure modes recorded in the findings.

## Provenance

The architecture is carried over from a previous project of ours — reuse of our own ideas
and prior work — but the code here is written for this contest. See `docs/REQUIREMENTS.md`.

## Licence

Apache 2.0.
