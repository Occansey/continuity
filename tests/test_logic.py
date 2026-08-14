"""The guardrails around the model calls: parsing, and the rules that keep a bad answer
from becoming a bad action. Fake client, real logic."""
import json
from conftest import FakeClient
from continuity.entities import resolve
from continuity.slots import assign
from continuity.scenes import Scene, renumber
from continuity.adjudicate import adjudicate


# ── entity resolution ─────────────────────────────────────────────────────────

def test_a_confident_merge_maps_members_to_canonical():
    c = FakeClient(json.dumps({"groups": [
        {"canonical": "Charles Haskell Jr.",
         "members": ["Haskell", "Charles Haskell"], "confidence": 0.95, "why": ""}]}))
    m = resolve(c, [("Haskell", "person", 5), ("Charles Haskell", "person", 3)], "w", "x")
    assert m["Haskell"] == "Charles Haskell Jr."
    assert m["Charles Haskell"] == "Charles Haskell Jr."


def test_a_cross_kind_merge_is_rejected():
    """A person and a car sharing a name is a mistake in the answer, and merging them
    invents a timeline that contradicts itself out of nothing."""
    c = FakeClient(json.dumps({"groups": [
        {"canonical": "Vera", "members": ["Vera", "convertible"], "confidence": 0.9}]}))
    m = resolve(c, [("Vera", "person", 9), ("convertible", "vehicle", 4)], "w", "x")
    assert m["Vera"] == "Vera" and m["convertible"] == "convertible"


def test_an_unmentioned_name_keeps_itself():
    """Silence is not a merge."""
    c = FakeClient(json.dumps({"groups": []}))
    m = resolve(c, [("Sue", "person", 2)], "w", "x")
    assert m["Sue"] == "Sue"


def test_a_hallucinated_member_is_dropped():
    c = FakeClient(json.dumps({"groups": [
        {"canonical": "Al Roberts", "members": ["Al", "someone we never saw"], "confidence": 0.9}]}))
    m = resolve(c, [("Al", "person", 400)], "w", "x")
    assert m == {"Al": "Al Roberts"}


# ── slots ─────────────────────────────────────────────────────────────────────

def test_single_valued_attributes_get_no_slot():
    """time_of_day is not a set; asking for slots would be a call with no purpose."""
    assert assign(FakeClient("{}"), "time_of_day", ["night", "day"], "x") == {}


def test_slots_only_returned_for_values_asked_about():
    c = FakeClient(json.dumps({"slots": {"fedora": "hat", "ghost garment": "hat"}}))
    got = assign(c, "wearing", ["fedora"], "x")
    assert got == {"fedora": "hat"}


# ── scenes ────────────────────────────────────────────────────────────────────

def test_renumber_puts_the_present_last_and_flashback_in_screen_order():
    scenes = [
        Scene(0, 0, 3, 0, 100, "diner", 0, "present"),
        Scene(1, 4, 9, 100, 200, "club", 0, "flashback"),
        Scene(2, 10, 15, 200, 300, "road", 0, "flashback"),
    ]
    out = renumber(scenes)
    assert out[1].story_order == 0 and out[2].story_order == 1   # flashback, in order
    assert out[0].story_order >= 10_000                          # present, last


# ── adjudication ──────────────────────────────────────────────────────────────

def _tr(**kw):
    base = dict(entity="Vera", entity_kind="person", attribute="accessory",
                t_from=10.0, t_to=20.0, value_from="hoop", value_to="stud",
                shot_from=-1, shot_to=-1, source_from="image", source_to="image",
                quote_from="", quote_to="")
    base.update(kw)
    return base


def test_an_unknown_verdict_is_rejected():
    """The model returning a word outside the vocabulary must not become a silent
    error or a silent pass."""
    v = adjudicate(FakeClient(json.dumps({"verdict": "probably fine", "confidence": 0.9})),
                   _tr(), [], "x")
    assert v is None


def test_a_cross_modal_pair_is_flagged_as_such():
    v = adjudicate(FakeClient(json.dumps({"verdict": "error", "confidence": 0.8, "reason": "x"})),
                   _tr(source_from="dialogue", source_to="image"), [], "x")
    assert v is not None and v.cross_modal is True


def test_unparseable_output_is_dropped_not_guessed():
    assert adjudicate(FakeClient("not json at all"), _tr(), [], "x") is None


def test_segment_accepts_a_bare_array_or_wrapped_object():
    """A second film returned the scenes as a top-level JSON array instead of
    {"scenes":[...]}. Both are valid answers to 'list the scenes' and losing a film to the
    shape would be absurd."""
    from conftest import FakeClient
    from continuity.scenes import segment
    shots = [{"n": i, "start": i * 10.0, "end": i * 10.0 + 9} for i in range(3)]
    arr = '[{"shots":[0,2],"place":"road","story_order":0,"frame":"flashback"}]'
    obj = '{"scenes":[{"shots":[0,2],"place":"road","story_order":0,"frame":"flashback"}]}'
    for payload in (arr, obj):
        out = segment(FakeClient(payload), shots, [], "x")
        assert len(out) == 1 and out[0].place == "road"
