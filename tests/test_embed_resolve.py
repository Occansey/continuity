"""Cross-corpus entity resolution, tested against the real chdb engine.

Like test_store.py these run the actual ClickHouse SQL rather than a model of it, and they
assert on the pairs the query returned, never on a printed label. The embedding is faked so
the test is offline and deterministic; the thing under test is the vector-plus-structured
query, not the embedder.
"""
import math

import chdb.session as chs

from continuity.embed_resolve import embed, load, resolve_across


def _fake_embed(texts):
    """A deterministic stand-in for the Vertex embedder.

    Each string is hashed into a small fixed-length unit vector. Determinism is the whole
    point: the same name always lands in the same place, so a planted near-duplicate is
    genuinely near and the test does not depend on a real model.
    """
    dim = 8
    out = []
    for text in texts:
        vec = [0.0] * dim
        for i, ch in enumerate(text):
            vec[i % dim] += (ord(ch) % 17) + 1
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        out.append([x / norm for x in vec])
    return out


def test_embed_delegates_to_the_injected_fn():
    got = embed(["clerk"], _fake_embed)
    assert got == _fake_embed(["clerk"])


def test_resolve_finds_a_planted_cross_work_duplicate():
    """A near-identical name appears in two different films. It should surface as a merge
    candidate, and a genuinely different entity in one of the films should not."""
    sess = chs.Session()

    # Same string in both works embeds to the same vector -> distance ~0, well inside the
    # threshold. "night sky" is unrelated and stays out.
    a_names = ["hotel clerk", "night sky"]
    b_names = ["hotel clerk", "roadside diner"]
    load(sess, "film_a", list(zip(a_names, _fake_embed(a_names))))
    load(sess, "film_b", list(zip(b_names, _fake_embed(b_names))))

    pairs = resolve_across(sess, threshold=0.05)

    matched = {(p["entity_a"], p["entity_b"]) for p in pairs}
    assert ("hotel clerk", "hotel clerk") in matched
    # The pair is drawn across the two works, not within one.
    hit = next(p for p in pairs if p["entity_a"] == "hotel clerk")
    assert hit["work_a"] != hit["work_b"]
    assert hit["distance"] < 0.05

    # A distant pair is excluded: nothing pairs "night sky" with "roadside diner".
    assert ("night sky", "roadside diner") not in matched
    assert ("roadside diner", "night sky") not in matched


def test_same_work_pairs_are_never_candidates():
    """Resolution is cross-film only; two entities inside one work are the contradiction
    search's territory, not this one's. Even at a permissive threshold they must not
    appear."""
    sess = chs.Session()
    names = ["clerk", "clerk"]
    load(sess, "film_a", list(zip(["clerk_one", "clerk_two"], _fake_embed(names))))

    pairs = resolve_across(sess, threshold=1.0)

    assert all(p["work_a"] != p["work_b"] for p in pairs)
    assert pairs == []
