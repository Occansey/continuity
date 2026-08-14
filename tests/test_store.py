"""The contradiction search, tested against a real ClickHouse engine.

chdb is the same query engine as the cluster, so these run the actual SQL rather than a
model of it. Every test here asserts what came out of the *window*, never what a row was
labelled, because this project's recurring failure was an eval that scored the label and
missed the world.
"""
import json
import chdb.session as chs
from continuity.store import TRANSITIONS, load


def _row(**kw):
    base = dict(shot=0, t=0.0, entity="Al", entity_kind="person", attribute="wearing",
                value="", confidence=0.9, source="image", quote="", slot="", scene=0,
                story_order=0)
    base.update(kw)
    return base


def _search(rows):
    sess = chs.Session()
    load(sess, rows, "w")
    res = sess.query(TRANSITIONS.replace("{work:String}", "'w'"), "JSON")
    return json.loads(str(res))["data"]


def test_a_change_in_the_same_slot_is_a_transition():
    out = _search([
        _row(slot="hat", value="fedora", t=1, scene=0, story_order=0),
        _row(slot="hat", value="cap", t=2, scene=1, story_order=1),
    ])
    assert len(out) == 1
    assert out[0]["value_from"] == "fedora" and out[0]["value_to"] == "cap"


def test_different_slots_never_compare():
    """The bug that was half of all transitions on the first film: a hat and a coat are
    worn at once, and comparing them asks whether one became the other."""
    out = _search([
        _row(slot="hat", value="fedora", t=1),
        _row(slot="outer", value="coat", t=2),
    ])
    assert out == []


def test_person_position_within_a_scene_is_suppressed():
    """Vera moves during her own strangling. Inside a scene, a body moving is acting."""
    same = _search([
        _row(attribute="position", value="sitting", scene=5, story_order=5, t=10),
        _row(attribute="position", value="lying", scene=5, story_order=5, t=11),
    ])
    assert same == []

    across = _search([
        _row(attribute="position", value="sitting", scene=5, story_order=5, t=10),
        _row(attribute="position", value="lying", scene=6, story_order=6, t=11),
    ])
    assert len(across) == 1


def test_the_window_walks_story_order_not_screen_order():
    """Detour is a flashback: the diner is latest in the story and first on screen. A
    window ordered by timecode compares the present with the past and calls it a change."""
    out = _search([
        _row(slot="top", value="present shirt", t=5, scene=0, story_order=8),   # diner, screen-early
        _row(slot="top", value="past shirt", t=100, scene=3, story_order=3),    # flashback, screen-late
    ])
    assert len(out) == 1
    # Story order 3 precedes 8, so the transition runs past -> present, not the reverse.
    assert out[0]["value_from"] == "past shirt"


def test_cross_scene_candidates_rank_first():
    """The class the prior art cannot reach is the one a human should see first."""
    out = _search([
        _row(slot="hat", value="a", t=1, scene=0, story_order=0),
        _row(slot="hat", value="b", t=2, scene=0, story_order=0),   # same scene
        _row(slot="top", value="c", t=3, scene=0, story_order=0),
        _row(slot="top", value="d", t=4, scene=7, story_order=7),   # crosses a scene
    ])
    assert out[0]["scene_from"] != out[0]["scene"]


def test_apostrophes_survive_insertion():
    """A film is full of them, and one unescaped quote ends the INSERT early and silently
    drops every row after it."""
    out = _search([
        _row(slot="outer", value="Haskell's coat", t=1),
        _row(slot="outer", value="Al's jacket", t=2),
    ])
    assert len(out) == 1
    assert "Haskell's" in out[0]["value_from"]
