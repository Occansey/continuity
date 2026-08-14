"""The maintained world-state and its global contradictions, against a real ClickHouse
engine (chdb). Every assertion is on a returned record or on the state set — never on a
printed label — because the two things this module exists to find are exactly the two a
pairwise diff misses, and a test that watched the wrong output would not know it.
"""
import chdb.session as chs
from continuity.store import load
from continuity.worldstate import global_inconsistencies, state_at


def _row(**kw):
    base = dict(shot=0, t=0.0, entity="Al", entity_kind="person", attribute="wearing",
                value="", confidence=0.9, source="image", quote="", slot="", scene=0,
                story_order=0)
    base.update(kw)
    return base


def _load(rows):
    sess = chs.Session()
    load(sess, rows, "w")
    return sess


def test_state_at_returns_the_latest_value_still_standing():
    """At a story point, a slot holds the last thing asserted about it at or before then,
    not the first and not the last in the whole film."""
    sess = _load([
        _row(slot="hat", value="fedora", story_order=0, t=1),
        _row(slot="hat", value="cap", story_order=5, t=2),
        _row(slot="hat", value="beret", story_order=9, t=3),
    ])
    assert state_at(sess, "w", 5) == {("Al", "wearing", "hat", "cap")}


def test_state_at_excludes_slots_the_story_has_not_reached():
    sess = _load([
        _row(slot="hat", value="fedora", story_order=0),
        _row(slot="outer", value="coat", story_order=8),
    ])
    # At story point 3 the coat has not been established yet.
    assert state_at(sess, "w", 3) == {("Al", "wearing", "hat", "fedora")}


def test_state_at_keeps_distinct_slots_apart():
    sess = _load([
        _row(slot="hat", value="fedora", story_order=1, t=1),
        _row(slot="outer", value="coat", story_order=2, t=2),
    ])
    assert state_at(sess, "w", 9) == {
        ("Al", "wearing", "hat", "fedora"),
        ("Al", "wearing", "outer", "coat"),
    }


def test_a_revert_is_flagged_where_a_value_returns():
    """A -> B -> A. Each leg looks like an ordinary change to a pairwise walk; the loop is
    the error, and only a view of the whole history sees it."""
    sess = _load([
        _row(slot="hat", value="fedora", story_order=0, t=1),
        _row(slot="hat", value="cap", story_order=3, t=2),
        _row(slot="hat", value="fedora", story_order=7, t=3),
    ])
    found = [i for i in global_inconsistencies(sess, "w") if i.kind == "revert"]
    assert len(found) == 1
    r = found[0]
    assert (r.attribute, r.slot, r.value_from) == ("wearing", "hat", "fedora")
    assert (r.story_from, r.story_to) == (0, 7)


def test_a_vanished_injury_is_flagged():
    """An injury is a standing fact. Established and then asserted gone, with nothing that
    brings it back, is a continuity error the transition search cannot name — nothing
    changed *into* anything."""
    sess = _load([
        _row(attribute="injury", value="cut on brow", story_order=2, t=1),
        _row(attribute="injury", value="none", story_order=6, t=2),
    ])
    found = [i for i in global_inconsistencies(sess, "w") if i.kind == "vanished"]
    assert len(found) == 1
    v = found[0]
    assert (v.attribute, v.value_from, v.value_to) == ("injury", "cut on brow", "none")
    assert (v.story_from, v.story_to) == (2, 6)


def test_a_reestablished_injury_does_not_vanish():
    """If the wound comes back after the absence, the feature still stands at the end and
    the absence was a gap in observation, not a loss."""
    sess = _load([
        _row(attribute="injury", value="cut on brow", story_order=2, t=1),
        _row(attribute="injury", value="none", story_order=6, t=2),
        _row(attribute="injury", value="cut on brow", story_order=9, t=3),
    ])
    assert [i for i in global_inconsistencies(sess, "w") if i.kind == "vanished"] == []


def test_a_plain_monotonic_change_is_flagged_by_neither():
    """The control. A single A -> B that never returns is what stories do all the time; it
    is neither a revert nor a vanishing, and flagging it is the noise this whole design
    exists to avoid."""
    sess = _load([
        _row(slot="hat", value="fedora", story_order=0, t=1),
        _row(slot="hat", value="cap", story_order=4, t=2),
    ])
    assert global_inconsistencies(sess, "w") == []
