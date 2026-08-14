"""Turn a finding into a recommendation: not just *this contradicts*, but *do this about it*.

Adjudication answers whether a change is an error. A crew still has to act on it, and the
action is not the same for every error — that is the whole of this step. The database
already carries the one fact that decides which action applies, so the decision is
arithmetic on that fact and stays out of the model's hands (CLAUDE.md 3: the model never
sets a number, and here it does not set the kind either).

## Why the scene boundary decides the kind

The search partitions by story order and reports the scene on each side of a transition
(store.py, `scene_from` vs `scene`). Two disagreeing assertions *inside one scene* are
almost never a fault in the world — they are two takes of the same setup that were cut
together, and one of them matches the rest of the scene. The fix is an edit, not a
reshoot: use the take that agrees. Nobody goes back to set for it, so proposing a pickup
there would be the expensive wrong answer.

A contradiction *across* scenes is the opposite: the two values were meant to be the same
world seen at different points, and they are not. That is what a pickup exists for — unless
the discrepancy is small enough that the honest, cheap resolution is to record the chosen
value in the continuity bible and move on, rather than send a unit back out.

## What the model does and does not do

The kind is decided here, deterministically, from the scene numbers. The model, when one is
supplied, only phrases the rationale for a reader. With no model the rationale is a plain
assembled sentence, so the recommendation is complete and testable offline.
"""

from __future__ import annotations

# Cross-scene changes in these attributes are cosmetic enough that the cheaper resolution is
# a note to the continuity bible rather than a pickup. The costlier attributes — a garment,
# a wound, the state of a vehicle or location — move the story enough that a mismatch across
# scenes is worth a reshoot decision. The split is deliberately conservative: when in doubt
# it lands on flag_for_pickup, because under-flagging a real error is the failure this tool
# exists to prevent (CLAUDE.md 3: defaults resolve toward escalating).
MINOR_ATTRIBUTES = frozenset({"accessory", "facial_hair", "hair", "prop_state"})


def _rationale(client, kind: str, finding: dict, scene_context) -> str:
    entity = finding.get("entity", "the entity")
    attribute = finding.get("attribute", "attribute")
    value_from = finding.get("value_from", "")
    value_to = finding.get("value_to", "")

    if kind == "use_alternate_take":
        basis = (f"{entity}'s {attribute} reads {value_from!r} and {value_to!r} within one "
                 f"scene; these are alternate takes, so cut to the take matching the rest of "
                 f"the scene rather than reshooting.")
    elif kind == "note_to_bible":
        basis = (f"{entity}'s {attribute} changes from {value_from!r} to {value_to!r} across "
                 f"scenes; the change is minor, so fix the chosen value in the continuity "
                 f"bible.")
    else:  # flag_for_pickup
        basis = (f"{entity}'s {attribute} changes from {value_from!r} to {value_to!r} across "
                 f"scenes with nothing to explain it; flag for a pickup.")

    if client is None:
        return basis

    # The model only rephrases an already-decided recommendation for a human reader; it has no
    # say in the kind. A parse or call failure must not lose the recommendation, so fall back
    # to the plain sentence rather than raise.
    prompt = (
        "Rewrite this continuity recommendation as one clear sentence for a script "
        "supervisor. Do not change what is being recommended.\n\n"
        f"Recommendation ({kind}): {basis}\n"
        f"Scene context: {scene_context or '(none)'}\n"
    )
    try:
        text = client.models.generate_content(model="", contents=[prompt]).text
    except Exception:
        return basis
    return (text or "").strip() or basis


def propose(finding: dict, scene_context=None, client=None) -> dict:
    """Recommend an action for one finding.

    A within-scene contradiction (scene_from == scene) becomes `use_alternate_take`. A
    cross-scene one becomes `note_to_bible` for a minor attribute and `flag_for_pickup`
    otherwise. The kind is decided here from the scene numbers; `client`, if given, only
    phrases the rationale.
    """
    scene_from = int(finding.get("scene_from", -1))
    scene = int(finding.get("scene", -1))

    if scene_from == scene:
        kind = "use_alternate_take"
    elif finding.get("attribute") in MINOR_ATTRIBUTES:
        kind = "note_to_bible"
    else:
        kind = "flag_for_pickup"

    return {"kind": kind, "rationale": _rationale(client, kind, finding, scene_context)}
