"""The continuity bible, built against a real ClickHouse engine.

chdb runs the same story-order walk the deployed store runs, so these assert on the
timelines that come out of it rather than on a model of them. The point of the bible is
that each fact is current and placed, so the tests assert the values *and their order*,
and that the rendered document names the entities and carries those values.
"""
import chdb.session as chs
from continuity.store import load
from continuity.bible import build_bible, render_markdown


def _row(**kw):
    base = dict(shot=0, t=0.0, entity="Al", entity_kind="person", attribute="wearing",
                value="", confidence=0.9, source="image", quote="", slot="", scene=0,
                story_order=0)
    base.update(kw)
    return base


def _bible(rows, top=6):
    sess = chs.Session()
    load(sess, rows, "w")
    return build_bible(sess, "w", top=top)


def test_a_track_records_each_change_in_story_order():
    b = _bible([
        _row(slot="hat", value="fedora", scene=1, t=10, story_order=0),
        _row(slot="hat", value="fedora", scene=1, t=11, story_order=0),   # unchanged
        _row(slot="hat", value="cap", scene=4, t=90, story_order=4),
    ])
    track = b.entities[0].timelines["wearing/hat"]
    # Two establishments, not three: the repeat is the same fact still holding.
    assert [f.value for f in track] == ["fedora", "cap"]
    assert [f.story_order for f in track] == [0, 4]
    assert track[1].scene == 4 and track[1].t == 90


def test_story_order_governs_the_timeline_not_screen_order():
    """The flashback fact is established before the framing one it precedes in the story,
    even though its timecode is later on screen."""
    b = _bible([
        _row(slot="top", value="present shirt", t=5, scene=0, story_order=8),
        _row(slot="top", value="past shirt", t=100, scene=3, story_order=3),
    ])
    track = b.entities[0].timelines["wearing/top"]
    assert [f.value for f in track] == ["past shirt", "present shirt"]


def test_slots_are_separate_tracks():
    """A hat and a coat are held at once; they are two facts, not one overwriting the
    other, so a change of hat must not read as the coat changing."""
    b = _bible([
        _row(slot="hat", value="fedora", story_order=0, t=1),
        _row(slot="outer", value="coat", story_order=0, t=1),
        _row(slot="hat", value="cap", story_order=5, t=50),
    ])
    tl = b.entities[0].timelines
    assert [f.value for f in tl["wearing/hat"]] == ["fedora", "cap"]
    assert [f.value for f in tl["wearing/outer"]] == ["coat"]


def test_principals_are_ranked_by_assertion_count_and_capped():
    rows = []
    for i in range(6):
        rows.append(_row(entity="Al", slot="hat", value=f"h{i}", story_order=i, t=i))
    for i in range(3):
        rows.append(_row(entity="Vera", entity_kind="person", attribute="hair",
                         value=f"v{i}", story_order=i, t=i))
    rows.append(_row(entity="Waiter", value="apron", slot="outer"))
    b = _bible(rows, top=2)

    assert [e.entity for e in b.entities] == ["Al", "Vera"]
    assert b.entities[0].assertions == 6
    # The lone-shot extra carries no continuity burden and is left out of the bible.
    assert "Waiter" not in {e.entity for e in b.entities}


def test_render_names_entities_and_carries_their_values():
    b = _bible([
        _row(entity="Al", slot="hat", value="fedora", scene=1, t=65, story_order=0),
        _row(entity="Al", slot="hat", value="cap", scene=4, t=125, story_order=4),
        _row(entity="Vera", entity_kind="person", attribute="hair",
             value="dark waves", scene=2, t=200, story_order=2),
    ], top=6)
    md = render_markdown(b)

    assert "## Al" in md
    assert "## Vera" in md
    assert "fedora" in md and "cap" in md and "dark waves" in md
    # Timecode is rendered so a change can be found in the cut.
    assert "1:05" in md
