"""The script-contract layer: read intended world-state from the screenplay, then flag
footage that breaks a promise the script made. Fake client for the reading, pure Python for
the comparison — the comparison is the part that must never guess."""
from conftest import FakeClient
from continuity.script import (
    SceneContract, Fact, Violation,
    contract_violations, extract_contract,
)

# A two-scene story: scene 0 establishes a cut over Al's brow; scene 1 restates his coat and
# silently depends on the injury still being there. story_order tracks screen order here.
SCENES = [
    {"n": 0, "t_from": 0.0, "t_to": 60.0, "story_order": 0},
    {"n": 1, "t_from": 60.0, "t_to": 120.0, "story_order": 1},
]

TRANSCRIPT = [
    {"t": 5.0, "speaker": "Al", "text": "That cut on my brow won't stop stinging."},
    {"t": 65.0, "speaker": "Al", "text": "I kept the coat on the whole drive."},
]

CONTRACT_JSON = """
{"contracts": [
  {"scene": 0,
   "facts": [{"entity": "Al", "attribute": "injury", "value": "cut on brow", "slot": ""}],
   "must_match": []},
  {"scene": 1,
   "facts": [{"entity": "Al", "attribute": "wearing", "value": "coat", "slot": "outer"}],
   "must_match": [{"entity": "Al", "attribute": "injury", "value": "cut on brow", "slot": ""}]}
]}
"""


def _obs(entity, attribute, value, scene, slot="", **kw):
    return {"entity": entity, "attribute": attribute, "value": value,
            "scene": scene, "slot": slot, **kw}


# ── extract_contract ────────────────────────────────────────────────────────────

def test_extract_contract_returns_a_contract_per_scene_with_story_order():
    contracts = extract_contract(FakeClient(CONTRACT_JSON), TRANSCRIPT, SCENES, "x")

    assert [c.scene for c in contracts] == [0, 1]
    # story_order is mapped from the scene list, not taken from the model: the story position
    # is a fact about the film, not something the script reader gets to invent.
    assert {c.scene: c.story_order for c in contracts} == {0: 0, 1: 1}


def test_extract_contract_carries_the_inherited_must_match_fact():
    """The whole reason this layer exists: scene 1 depends on an injury it never restates."""
    contracts = extract_contract(FakeClient(CONTRACT_JSON), TRANSCRIPT, SCENES, "x")
    scene1 = next(c for c in contracts if c.scene == 1)

    assert Fact("Al", "injury", "cut on brow", "") in scene1.must_match
    assert Fact("Al", "wearing", "coat", "outer") in scene1.facts


def test_extract_contract_drops_a_fact_missing_its_value():
    """A promise with no value names nothing checkable and must not survive into the
    contract, where it would later match an empty observation and invent a violation."""
    raw = """
    {"contracts": [{"scene": 0, "facts": [{"entity": "Al", "attribute": "injury"}],
                    "must_match": []}]}
    """
    contracts = extract_contract(FakeClient(raw), TRANSCRIPT, SCENES, "x")

    assert contracts[0].facts == ()


def test_extract_contract_ignores_a_scene_not_in_the_scene_list():
    """The contract is anchored to the scenes we have. A scene number the model invents has
    no story position and no footage, so it is dropped rather than carried."""
    raw = """
    {"contracts": [
      {"scene": 0, "facts": [], "must_match": []},
      {"scene": 9, "facts": [{"entity": "X", "attribute": "hair", "value": "long", "slot": ""}],
       "must_match": []}]}
    """
    contracts = extract_contract(FakeClient(raw), TRANSCRIPT, SCENES, "x")

    assert [c.scene for c in contracts] == [0]


def test_extract_contract_returns_empty_on_unparseable_response():
    """Nothing read from the script means nothing to check; inventing promises from a broken
    parse would be worse than checking none."""
    assert extract_contract(FakeClient("not json"), TRANSCRIPT, SCENES, "x") == []


# ── contract_violations ───────────────────────────────────────────────────────────

def _contracts():
    return extract_contract(FakeClient(CONTRACT_JSON), TRANSCRIPT, SCENES, "x")


def test_a_vanished_inherited_injury_is_flagged():
    """The planted mismatch: the script promises the brow cut persists into scene 1, but the
    footage there reads an unmarked brow. No footage-internal search reaches this, because the
    script never restates the injury for a later frame to contradict."""
    observed = [
        _obs("Al", "injury", "cut on brow", scene=0, quote="visible cut"),
        _obs("Al", "wearing", "coat", scene=1, slot="outer"),
        _obs("Al", "injury", "none", scene=1, quote="clean brow"),
    ]
    violations = contract_violations(_contracts(), observed)

    assert len(violations) == 1
    v = violations[0]
    assert (v.scene, v.entity, v.attribute, v.kind) == (1, "Al", "injury", "must_match")
    assert v.expected == "cut on brow" and v.observed == "none"


def test_footage_consistent_with_the_contract_is_not_flagged():
    """The injury persists and the coat matches. Agreement is not a finding."""
    observed = [
        _obs("Al", "injury", "cut on brow", scene=0),
        _obs("Al", "wearing", "coat", scene=1, slot="outer"),
        _obs("Al", "injury", "cut on brow", scene=1),
    ]
    assert contract_violations(_contracts(), observed) == []


def test_a_scene_fact_contradiction_is_flagged_as_kind_scene():
    """A promise broken in the same scene it was made is still a violation — just one the
    footage-internal search might also have caught. It is tagged `scene`, not `must_match`."""
    observed = [_obs("Al", "wearing", "jacket", scene=1, slot="outer")]
    violations = contract_violations(_contracts(), observed)

    assert len(violations) == 1
    assert violations[0].kind == "scene"
    assert (violations[0].expected, violations[0].observed) == ("coat", "jacket")


def test_a_promise_the_footage_never_speaks_to_is_not_a_violation():
    """Silence is not contradiction. If the extractor never mentions the coat, the coat
    promise is unchecked, not broken — otherwise every unmentioned fact would flag."""
    observed = [_obs("Al", "injury", "cut on brow", scene=1)]
    violations = contract_violations(_contracts(), observed)

    # The must_match injury is honoured; the scene's coat fact is simply never observed.
    assert violations == []


def test_a_slotless_promise_matches_the_observed_slot():
    """A script that fixes a value but not which layer still checks against the frame's
    slotted reading — the promise is about the attribute at large."""
    contracts = [SceneContract(
        scene=2, story_order=2,
        facts=(Fact("Vera", "wearing", "coat"),), must_match=(),
    )]
    observed = [_obs("Vera", "wearing", "gown", scene=2, slot="outer")]
    violations = contract_violations(contracts, observed)

    assert len(violations) == 1
    assert violations[0].observed == "gown"


def test_comparison_ignores_case_and_surrounding_whitespace():
    """The contract and the extractor are two independent writers; a difference of casing is
    not a difference in the world and must not read as one."""
    contracts = [SceneContract(
        scene=3, story_order=3,
        facts=(Fact("Al", "holding", "Gun"),), must_match=(),
    )]
    observed = [_obs("al", "holding", "  gun  ", scene=3)]
    assert contract_violations(contracts, observed) == []
