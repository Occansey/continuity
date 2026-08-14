"""Precision checks: a vote that drops confabulations, a forced closed choice, and a
skeptic whose failures keep the flag rather than lose it. Fake client, real logic."""
from conftest import FakeClient
from continuity.verify import consensus, reverify, skeptic


def _a(entity, attribute, value, **kw):
    return {"entity": entity, "attribute": attribute, "value": value, **kw}


# ── consensus ─────────────────────────────────────────────────────────────────

def test_a_majority_assertion_survives_and_a_singleton_is_dropped():
    """The coat is in every pass; the 0.95 earring is in one. A vote is what separates a
    real observation from a one-off confabulation, and only the coat should come back."""
    runs = [
        [_a("Vera", "wearing", "coat"), _a("Vera", "accessory", "earring")],
        [_a("Vera", "wearing", "coat")],
        [_a("Vera", "wearing", "coat")],
    ]
    calls = iter(runs)
    kept = consensus(lambda: next(calls), k=3)

    values = {(a["entity"], a["attribute"], a["value"]) for a in kept}
    assert ("Vera", "wearing", "coat") in values
    assert ("Vera", "accessory", "earring") not in values


def test_repeats_within_one_run_are_one_vote_not_a_majority():
    """A single pass repeating itself is still a single opinion. Three mentions in one run
    must not clear a three-run majority on their own."""
    runs = [
        [_a("Al", "holding", "gun"), _a("Al", "holding", "gun"), _a("Al", "holding", "gun")],
        [_a("Al", "holding", "wallet")],
        [_a("Al", "holding", "wallet")],
    ]
    calls = iter(runs)
    kept = consensus(lambda: next(calls), k=3)

    values = {a["value"] for a in kept}
    assert values == {"wallet"}


def test_consensus_preserves_the_full_assertion_not_just_the_key():
    """The vote decides survival; it must not strip the columns the store needs."""
    runs = [
        [_a("Vera", "wearing", "coat", confidence=0.9, shot=12)],
        [_a("Vera", "wearing", "coat", confidence=0.9, shot=12)],
    ]
    calls = iter(runs)
    kept = consensus(lambda: next(calls), k=2)

    assert len(kept) == 1
    assert kept[0]["confidence"] == 0.9 and kept[0]["shot"] == 12


# ── reverify ──────────────────────────────────────────────────────────────────

def test_reverify_returns_the_value_the_model_names():
    got = reverify(FakeClient("fedora"), object(), "wearing", "fedora", "homburg", "x")
    assert got == "fedora"


def test_reverify_returns_none_when_the_answer_matches_neither_value():
    """An unreadable answer to a two-way question is not a licence to pick one."""
    got = reverify(FakeClient("a bowler hat"), object(), "wearing", "fedora", "homburg", "x")
    assert got is None


# ── skeptic ───────────────────────────────────────────────────────────────────

def test_skeptic_parses_a_refutation():
    out = skeptic(FakeClient('{"refuted": true, "reason": "an hour passed"}'), "f", "x")
    assert out["refuted"] is True


def test_skeptic_parses_a_survived_flag():
    out = skeptic(FakeClient('{"refuted": false, "reason": "nothing accounts for it"}'), "f", "x")
    assert out["refuted"] is False


def test_an_unparseable_skeptic_keeps_the_flag():
    """Fail safe: the skeptic is built to kill flags, so when it cannot be read we default
    to keeping the flag, never to discarding it on a broken response."""
    out = skeptic(FakeClient("not json at all"), "f", "x")
    assert out["refuted"] is False


def test_a_skeptic_missing_the_verdict_key_keeps_the_flag():
    out = skeptic(FakeClient('{"reason": "forgot the verdict"}'), "f", "x")
    assert out["refuted"] is False


# ── canonicalization and adversarial confirmation (wired into the pipeline) ──

def test_canonical_map_collapses_synonyms_and_keeps_the_rest():
    from conftest import FakeClient
    from continuity.canonicalize import canonical_map
    import json as _j
    c = FakeClient(_j.dumps({"canonical": {"dark combed hair": "dark hair",
                                           "dark slicked-back hair": "dark hair"}}))
    m = canonical_map(c, "hair", ["dark combed hair", "dark slicked-back hair", "blonde hair"], "x")
    assert m["dark combed hair"] == "dark hair" and m["dark slicked-back hair"] == "dark hair"
    assert m["blonde hair"] == "blonde hair"   # unmentioned keeps itself


def test_canonicalize_rows_reports_and_applies_changes():
    from conftest import FakeClient
    from continuity.canonicalize import canonicalize_rows
    import json as _j
    rows = [{"attribute": "hair", "value": "dark combed hair"},
            {"attribute": "hair", "value": "dark slicked-back hair"}]
    c = FakeClient(_j.dumps({"canonical": {"dark combed hair": "dark hair",
                                           "dark slicked-back hair": "dark hair"}}))
    changed = canonicalize_rows(c, rows, "x")
    assert changed == 2 and all(r["value"] == "dark hair" for r in rows)


def test_confirm_only_attacks_errors():
    from conftest import FakeClient
    from continuity.confirm import confirm
    class V:  # noqa: minimal stand-in for a Verdict
        verdict = "explained"
    r = confirm(FakeClient("{}"), V(), "x")
    assert r["survived"] is True and "nothing to refute" in r["reason"]


def test_a_world_relative_error_resists_a_time_passed_excuse():
    """The fix that took the skeptic from 0/10 to discriminating: a bruise cannot move off
    screen, so 'time elapsed' must not refute it. The note is injected only for world-relative
    attributes."""
    import json as _j
    from conftest import FakeClient
    from continuity.confirm import confirm
    class V:
        verdict = "error"; entity = "x"; attribute = "injury"
        value_from = "bruise on right"; value_to = "bruise on left"
        t_from = 10.0; t_to = 300.0; reason = "moved"
    # A skeptic that refutes anyway is overridden by nothing — but we assert the finding text
    # carries the world-relative constraint, which is what makes the skeptic discriminate.
    seen = {}
    class Rec(FakeClient):
        def generate_content(self, **kw):
            seen["text"] = kw["contents"][0]
            return super().generate_content(**kw)
    c = Rec(_j.dumps({"refuted": False, "reason": "grounded"}))
    r = confirm(c, V(), "x")
    assert "not move a watch" in seen["text"] or "fixed to the body" in seen["text"]
    assert r["survived"] is True
