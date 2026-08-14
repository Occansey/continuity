"""Recall against third-party ground truth — the blind exam we did not write.

Continuity's whole claim (SPECIFICATION.md §8) is falsifiable by anyone with the film: of
the documented *cross-scene* continuity errors in Detour (1945), how many does the system
actually surface. This harness holds a FROZEN, hand-entered list of errors documented by
strangers in published continuity listings (IMDb "Goofs" and continuity-error compendia),
transcribed here only as a timecode plus a short claim — the minimal fact needed to test
against, never the listing's prose — and reports recall with an interval and an explicit N.

Recall is the number this method is *allowed* to be modest on. The spec optimises precision
and reports recall without trading against it; a low recall printed honestly is the point,
not an embarrassment. So this file never prints a bare percentage: k/n, a Wilson score
interval, and the fact that N is tiny and this is one film, every time.

Run: ./.venv/bin/python evals/blind.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Match tolerance on timecode, in seconds. The published timecodes are approximate ("~"),
# and our own timecodes are the midpoint of a shot, so a wide-ish window is honest; we
# additionally require entity/attribute plausibility so tolerance alone cannot manufacture
# a match.
TOL_S = 180.0

# ---------------------------------------------------------------------------------------
# SCOPE RULE (fixed, stated before the list so it cannot be tuned to the answer).
#
# A documented error is IN-SCOPE for this method iff it is either:
#   (a) a CROSS-SCENE state contradiction — the same entity+attribute holding two values
#       that disagree across a scene boundary (a wound, a hairstyle, a garment that should
#       persist), which is precisely what a claims-not-pixels method can reach; or
#   (b) a SAID-vs-SHOWN contradiction — dialogue asserts one value, the image another.
#
# It is OUT-OF-SCOPE iff it is a WITHIN-SHOT artifact or a SHOT-TO-SHOT take-matching goof
# inside a single continuous scene (a burning cigarette's length across a cut, a flipped
# negative, a prop nudged between takes). That is the registration-based prior art's domain
# (SPECIFICATION.md §1), and this system deliberately does not chase it — store.TRANSITIONS
# even filters same-scene position changes back out. Counting those against our recall would
# be scoring ourselves on an exam we explicitly refuse to sit.
#
# Out-of-scope items are listed too, and shown, so the exclusion is visible and auditable
# rather than a quiet omission — but they are not in the denominator.
# ---------------------------------------------------------------------------------------

DOCUMENTED = [
    {
        "id": "scratches-hand-vs-wrist",
        "claim": "Haskell's scratches: described on the right HAND, later called the WRIST",
        "timecodes": [1043, 2349],
        "scope": "in",              # cross-scene contradiction about an injury's location
        "entity_kind": "person",
        "attributes": {"injury"},
        "entity_hint": None,        # any person; the driver is Haskell in our entity set
    },
    {
        "id": "vera-hair-convertible",
        "claim": "Vera's hair changes repeatedly during the convertible sequence",
        "timecodes": [3050, 3700],
        "scope": "in",              # cross-scene grooming-state that should persist
        "entity_kind": "person",
        "attributes": {"hair"},
        "entity_hint": "vera",
    },
    {
        "id": "cigarette-length-piano",
        "claim": "Al's cigarette jumps in length between shots at the piano",
        "timecodes": [220],
        "scope": "out",             # within-scene, shot-to-shot take mismatch: prior-art domain
        "entity_kind": "person",
        "attributes": {"holding"},
        "entity_hint": "al",
    },
    {
        "id": "sedan-to-convertible",
        "claim": "A closed sedan cuts to an open convertible",
        "timecodes": [2224, 2228],
        "scope": "out",             # a body-style flip across one cut inside a continuous
                                    # driving scene — adjacent-shot goof, not cross-scene state
        "entity_kind": "vehicle",
        "attributes": {"vehicle_state"},
        "entity_hint": None,
    },
]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion. Correct at k=0 and k=n, where
    the normal approximation gives nonsense — which matters here because n is tiny and the
    point estimate will often sit at a boundary."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def matches(doc: dict, transitions: list[dict]) -> dict | None:
    """A documented error is 'found' if some transition is plausibly the same event:
    a value change of the right kind of entity and attribute, within TOL of a documented
    timecode. Plausibility (kind + attribute) guards against a match on timecode alone."""
    for tr in transitions:
        if tr.get("attribute") not in doc["attributes"]:
            continue
        if tr.get("entity_kind") != doc["entity_kind"]:
            continue
        if doc["entity_hint"] and doc["entity_hint"] not in str(tr.get("entity", "")).lower():
            continue
        near = min(
            min(abs(float(tr["t_from"]) - tc), abs(float(tr["t_to"]) - tc))
            for tc in doc["timecodes"]
        )
        if near <= TOL_S:
            return {**tr, "_gap_s": round(near, 1)}
    return None


def main() -> int:
    transitions = json.loads((ROOT / "work" / "transitions.json").read_text())

    in_scope = [d for d in DOCUMENTED if d["scope"] == "in"]
    out_scope = [d for d in DOCUMENTED if d["scope"] == "out"]

    print("Blind recall — Detour (1945), against published third-party continuity listings")
    print("=" * 78)
    print(f"System output under test: work/transitions.json ({len(transitions)} transitions)\n")

    print("IN-SCOPE documented errors (cross-scene state / said-vs-shown) — the denominator:")
    matched = 0
    for d in in_scope:
        m = matches(d, transitions)
        if m:
            matched += 1
            print(f"  [FOUND ] {d['id']}: {d['claim']}")
            print(f"           via {m['entity']!r} / {m['attribute']} "
                  f"{m['value_from']!r} -> {m['value_to']!r} "
                  f"(t {m['t_from']:.0f}->{m['t_to']:.0f}s, {m['_gap_s']}s from documented)")
            print(f"           match is on entity-kind + attribute + timecode, NOT verified")
            print(f"           value-identity — the surfaced transition is the same class of")
            print(f"           error at the same place, which may or may not be the exact goof.")
        else:
            print(f"  [MISSED] {d['id']}: {d['claim']}")
    print()

    print("OUT-OF-SCOPE documented errors (shot-to-shot / within-shot) — shown, not scored:")
    for d in out_scope:
        m = matches(d, transitions)
        tag = "incidentally surfaced" if m else "not surfaced"
        print(f"  [ OUT  ] {d['id']}: {d['claim']}  ({tag})")
    print()

    n = len(in_scope)
    lo, hi = wilson(matched, n)
    print("Result")
    print("------")
    print(f"  recall = {matched}/{n} in-scope documented cross-scene errors found")
    print(f"  point estimate {matched / n:.2f}, Wilson 95% interval [{lo:.2f}, {hi:.2f}]")
    print(f"  N = {n}. This N is tiny and this is a single film (Detour, 1945).")
    print("  The interval is correspondingly wide; treat the point estimate as indicative,")
    print("  not as a measured recall rate. Recall is reported, never traded against")
    print("  precision (SPECIFICATION.md §5), and the honest reading of one film with N=%d" % n)
    print("  is that this establishes the method reaches cross-scene errors at all, not how")
    print("  often — that needs many more labelled films before any rate is defensible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
