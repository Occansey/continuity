"""The assertion store, and the contradiction search over it.

The search is the product, so it is worth saying plainly what it is: for every entity and
attribute, walk its assertions in story order and find consecutive pairs whose values
disagree. That is a self-join with a window function over an assertions table, and it
grows with the square of the work's length, which is why nobody does it by hand for a
whole series and why the store has to be able to take it.

## Why a contradiction is not a difference

Almost every pair of consecutive assertions differs, because stories move. People change
clothes, wounds heal, night follows day. If the query returned differences it would
return everything and be worthless — which is what a list of *1,340 differences* looks
like in a competing product.

So the query does the part a database can do well: it finds transitions, sizes them, and
throws away the ones that are structurally uninteresting. The part it cannot do — whether
a transition has an innocent explanation — is left for a model, with both sides attached.
The division is the whole design.

## Why ClickHouse

A partitioned window over every assertion for an attribute across a whole work, plus the
scan to build it. On one film it would
run anywhere. The workload this is aimed at is a series or a franchise, where the same
query runs over two orders of magnitude more rows, and the benchmark in
`evals/partner_benchmark.py` is there to find the point where the alternative stops
finishing.
"""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS assertions (
    work         LowCardinality(String),
    shot         Int32,
    t            Float64,
    entity       String,
    entity_kind  LowCardinality(String),
    attribute    LowCardinality(String),
    value        String,
    confidence   Float32,
    source       LowCardinality(String),
    quote        String,
    slot         LowCardinality(String),
    scene        Int32,
    story_order  Int32
) ENGINE = MergeTree
ORDER BY (work, entity, attribute, slot, t)
"""

# Consecutive assertions about the same entity and attribute, where the value changed.
#
# PARTITION BY entity, attribute, slot ORDER BY t is the load-bearing line. `slot` is
# there because `wearing` is a set, not a value: without it the window compares a beret
# with a coat and asks whether one became the other. That single missing column was 52% of
# all transitions on the first film.
#
# The rest of the reasoning: the partition is what
# makes two rows comparable at all, and the order is what makes a change a *transition*
# rather than an unordered pair. An earlier version used neighbor(), which ClickHouse
# deprecates precisely because it reads adjacent rows of the whole result rather than of a
# group — it needed a subquery sorted just so, and a stray ORDER BY anywhere upstream would
# have silently compared one character's hat with another's. It is also the thing that will be
# wrong first, because screen order is not story order once a film has flashbacks — and
# Detour is told almost entirely in flashback. Recorded in SPECIFICATION.md 10.
TRANSITIONS = """
SELECT * FROM (
    SELECT
        entity, attribute, entity_kind, slot, scene, story_order,
        lagInFrame(scene)       OVER w AS scene_from,
        lagInFrame(story_order) OVER w AS story_from,
        lagInFrame(t)          OVER w AS t_from,
        lagInFrame(value)      OVER w AS value_from,
        lagInFrame(shot)       OVER w AS shot_from,
        lagInFrame(source)     OVER w AS source_from,
        lagInFrame(quote)      OVER w AS quote_from,
        lagInFrame(confidence) OVER w AS conf_from,
        t AS t_to, value AS value_to, shot AS shot_to, source AS source_to,
        quote AS quote_to, confidence AS conf_to
    FROM assertions
    WHERE work = {work:String}
    WINDOW w AS (PARTITION BY entity, attribute, slot ORDER BY story_order, t
                 ROWS BETWEEN 1 PRECEDING AND CURRENT ROW)
)
WHERE t_from > 0 AND value_from != value_to
  -- A person's position changes constantly inside a scene, because that is what acting
  -- is. Vera moves during her own strangling; the search called it a discontinuity. Across
  -- a scene boundary the same change is worth looking at, so the boundary is the filter,
  -- not the attribute.
  AND NOT (attribute = 'position' AND entity_kind = 'person' AND scene_from = scene)
ORDER BY (scene_from != scene) DESC, least(conf_from, conf_to) DESC, (t_to - t_from) ASC
"""



def load(sess, rows: list[dict], work: str) -> int:
    """Insert assertions. Values are escaped rather than formatted, because a film is full
    of apostrophes and one of them will otherwise end the statement early."""
    sess.query(SCHEMA)
    if not rows:
        return 0
    def esc(s: str) -> str:
        return str(s).replace("\\", "\\\\").replace("'", "\\'")
    values = ",".join(
        "('{}',{},{},'{}','{}','{}','{}',{},'{}','{}','{}',{},{})".format(
            esc(work), int(r.get("shot", -1)), float(r.get("t", 0.0)),
            esc(r.get("entity", "")), esc(r.get("entity_kind", "")),
            esc(r.get("attribute", "")), esc(r.get("value", "")),
            float(r.get("confidence", 0.5)), esc(r.get("source", "image")),
            esc(r.get("quote", "")), esc(r.get("slot", "")),
            int(r.get("scene", -1)), int(r.get("story_order", -1)),
        )
        for r in rows
    )
    sess.query(f"INSERT INTO assertions VALUES {values}")
    return len(rows)


def read_jsonl(*paths: str | Path) -> list[dict]:
    out: list[dict] = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out
