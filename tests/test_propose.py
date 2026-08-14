"""The detect->propose step: the recommendation kind is decided by the scene boundary, not
by the model. Fake client, real logic — the decision must hold offline and be the same every
time."""
from conftest import FakeClient
from continuity.propose import propose


def _finding(**kw):
    base = dict(scene_from=3, scene=3, entity="Vera", entity_kind="person",
                attribute="wearing", value_from="fur coat", value_to="no coat")
    base.update(kw)
    return base


def test_within_scene_contradiction_uses_an_alternate_take():
    """Same scene on both sides means two takes of one setup, resolved by an edit, not a
    trip back to set."""
    r = propose(_finding(scene_from=3, scene=3))
    assert r["kind"] == "use_alternate_take"


def test_cross_scene_costly_change_flags_a_pickup():
    r = propose(_finding(scene_from=3, scene=7, attribute="wearing"))
    assert r["kind"] == "flag_for_pickup"


def test_cross_scene_minor_change_goes_to_the_bible():
    """A cosmetic mismatch across scenes is cheaper to resolve by fixing the value in the
    continuity bible than by ordering a pickup."""
    r = propose(_finding(scene_from=3, scene=7, attribute="accessory"))
    assert r["kind"] == "note_to_bible"


def test_the_kind_ignores_the_model():
    """The scene numbers decide the kind; a model, when present, only phrases the rationale
    and cannot move the decision."""
    r = propose(_finding(scene_from=3, scene=3), client=FakeClient("send it to the bible"))
    assert r["kind"] == "use_alternate_take"


def test_a_supplied_client_phrases_the_rationale():
    r = propose(_finding(scene_from=3, scene=7), client=FakeClient("Reshoot Vera's coat."))
    assert r["rationale"] == "Reshoot Vera's coat."


def test_without_a_client_the_rationale_is_a_plain_sentence():
    r = propose(_finding(scene_from=3, scene=7))
    assert r["rationale"] and isinstance(r["rationale"], str)
