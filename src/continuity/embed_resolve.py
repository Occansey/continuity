"""Cross-corpus entity resolution by vector similarity.

The contradiction search in `store.py` runs inside one work: the same entity, walked in
story order. This module is the other axis. A franchise reuses people, props and places
across films, and the extractor names them independently each time — "the flophouse
clerk", "hotel clerk", "night manager" may be one character across three pictures, or
three. Deciding that by hand does not scale past a couple of films, which is the point of
running a series through this at all.

The resolution is a single ClickHouse query that is a vector search *and* a structured
filter at once: nearest neighbours by `cosineDistance`, constrained to pairs drawn from
different works. Neither half is enough alone — a pure vector index would surface a
character next to itself, and a pure `WHERE work != work` join would return the whole
cross product. Doing both in one query over `entity_vectors` is the workload that makes a
columnar store load-bearing here rather than incidental.
"""

from __future__ import annotations

# Distance builtin. Verified against the bundled chdb engine (2026-08): `cosineDistance`
# is present and returns 1 - cosine similarity, so smaller means closer and a threshold is
# an upper bound. `L2Distance` and `L2SquaredDistance` are also available if a Euclidean
# metric is ever wanted, but cosine is the right one for text embeddings, whose magnitude
# carries no meaning.
DISTANCE = "cosineDistance"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entity_vectors (
    work    LowCardinality(String),
    entity  String,
    vec     Array(Float32)
) ENGINE = MergeTree
ORDER BY (work, entity)
"""

# Cross-work nearest neighbours in one pass. `a.work < b.work` does two things: it drops
# same-work pairs (an entity is never a merge candidate with itself or its neighbours in
# its own film — that is the other search's job), and it keeps each unordered pair once
# rather than returning both (a, b) and (b, a). The distance predicate is what makes this a
# similarity query rather than a full cross product; ClickHouse evaluates it during the
# join, so the store does the vector arithmetic and the model only ever sees the shortlist.
RESOLVE = """
SELECT
    a.work   AS work_a,
    a.entity AS entity_a,
    b.work   AS work_b,
    b.entity AS entity_b,
    {distance}(a.vec, b.vec) AS distance
FROM entity_vectors a
CROSS JOIN entity_vectors b
WHERE a.work < b.work
  AND {distance}(a.vec, b.vec) < {threshold}
ORDER BY distance ASC, work_a, entity_a, work_b, entity_b
"""


def embed(texts: list[str], embed_fn) -> list[list[float]]:
    """Return one float vector per input text.

    `embed_fn` is injected so the call is swappable. In production it wraps Vertex text
    embeddings (a model such as 'text-embedding-005'); tests pass a deterministic fake that
    hashes each string, so the suite needs no network and no credentials.
    """
    return embed_fn(texts)


def create(sess) -> None:
    sess.query(SCHEMA)


def load(sess, work: str, entity_vecs: list[tuple[str, list[float]]]) -> int:
    """Insert (entity, vector) pairs for one work.

    The vector is written as a ClickHouse array literal. Entity names are escaped the same
    way `store.load` escapes them, because a character named with an apostrophe would
    otherwise end the statement early and silently drop the rest of the batch.
    """
    create(sess)
    if not entity_vecs:
        return 0

    def esc(s: str) -> str:
        return str(s).replace("\\", "\\\\").replace("'", "\\'")

    def arr(v: list[float]) -> str:
        return "[" + ",".join(repr(float(x)) for x in v) + "]"

    values = ",".join(
        "('{}','{}',{})".format(esc(work), esc(entity), arr(vec))
        for entity, vec in entity_vecs
    )
    sess.query(f"INSERT INTO entity_vectors VALUES {values}")
    return len(entity_vecs)


def resolve_across(sess, threshold: float) -> list[dict]:
    """Candidate cross-film identity merges: entity pairs from different works whose
    vectors are closer than `threshold` under `cosineDistance` (smaller is closer).

    Returns rows of work_a, entity_a, work_b, entity_b, distance, nearest first. These are
    candidates, not conclusions — a model still judges each pair — but the store has already
    thrown away every pair that is not plausibly the same thing.
    """
    import json

    sql = RESOLVE.replace("{distance}", DISTANCE).replace(
        "{threshold}", repr(float(threshold))
    )
    res = sess.query(sql, "JSON")
    return json.loads(str(res))["data"]
