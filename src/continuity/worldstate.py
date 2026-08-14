"""A maintained world-state, and the contradictions that only a maintained state can see.

`store.TRANSITIONS` compares each assertion with the one before it. That catches a change
across a cut, but it is blind to anything whose two ends are not adjacent: a hat that comes
back three scenes later reads, pairwise, as two ordinary changes, and a wound that simply
stops being mentioned reads as nothing at all. Neither is a *transition*, so neither is
found by looking at transitions.

So this module keeps, for every (entity, attribute, slot), the ordered history of what was
asserted, and asks two questions of the whole history rather than of a pair:

  * `state_at` — what is true *now*, at a story point: the latest assertion still standing
    for each (entity, attribute, slot). This is the model the rest of V2 diffs against.

  * `global_inconsistencies` — the two shapes a pairwise walk cannot reach:
      - **revert**: a value returns to one it held earlier (A -> B -> A). Each leg is an
        innocent-looking change; the loop is the error.
      - **vanished**: a value under a permanent-by-nature attribute (an injury, facial
        hair) is established and then goes absent and never comes back. Nothing *changed
        into* anything, so there is no transition to flag — only a state that should have
        persisted and did not.

The ordering and the run-collapse are done in SQL, where story order is a guarantee rather
than a hope; the small combinatorial checks over the collapsed runs are done here, because
"a value that appears twice" and "the last run is an absence" are awkward to say in SQL and
plain to say in a loop.
"""

from __future__ import annotations

from dataclasses import dataclass

# An injury and facial hair do not heal or shave themselves between two shots of the same
# afternoon. Continuity treats them as standing facts, so a later assertion that one is
# gone is a claim about the world that contradicts the earlier one — unlike `wearing`,
# where taking a coat off is just Tuesday.
PERMANENT = frozenset({"injury", "facial_hair"})

# Values that assert the *absence* of a permanent feature rather than a different one.
# "cut on brow" -> "bruise" is a changed injury; "cut on brow" -> "none" is a vanished one,
# and only the second is what `vanished` is for. Matched after lower/strip.
_ABSENT = frozenset({
    "", "none", "no injury", "no injuries", "uninjured", "unmarked", "healed", "gone",
    "clean-shaven", "clean shaven", "clean shaved", "no facial hair", "beardless",
})


@dataclass(frozen=True)
class Inconsistency:
    """A contradiction the pairwise transition search cannot reach.

    For a revert, `value_from` and `value_to` are the same value — that equality, held at
    two non-adjacent story points with a different value between them, *is* the finding.
    For a vanished feature, `value_from` is what was established and `value_to` is the
    absence that replaced it.
    """
    kind: str            # 'revert' | 'vanished'
    entity: str
    entity_kind: str
    attribute: str
    slot: str
    story_from: int      # story point where the earlier / established value held
    story_to: int        # story point where the return or the disappearance is asserted
    value_from: str
    value_to: str


def _lit(s: str) -> str:
    """A single-quoted SQL string literal. Escaped, not formatted: a film is full of
    apostrophes and one of them will otherwise end the statement early (see store.load)."""
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"


# The latest surviving assertion per (entity, attribute, slot) at or before a story point.
# argMax over the (story_order, t) tuple picks the value that was asserted last in story
# time, with the timecode as the within-point tie-break — the same ordering the transition
# window uses, so "current" here means the same thing as "most recent" there.
_STATE_AT = """
SELECT entity, attribute, slot, argMax(value, (story_order, t)) AS value
FROM assertions
WHERE work = {work} AND story_order <= {so}
GROUP BY entity, attribute, slot
"""


# The value history per (entity, attribute, slot), ordered by story time and with
# consecutive repeats collapsed to a single run. Collapsing matters: after it, a value that
# appears twice is guaranteed to have had a *different* value between its two appearances
# (the row in between cannot be equal, or it would have been collapsed), which is exactly
# the A -> B -> A condition — so the Python side does not have to re-check for a gap.
_RUNS = """
SELECT entity, entity_kind, attribute, slot, value, story_order, t
FROM (
    SELECT entity, entity_kind, attribute, slot, value, story_order, t,
           row_number()     OVER w AS rn,
           lagInFrame(value) OVER w AS prev_value
    FROM assertions
    WHERE work = {work}
    WINDOW w AS (PARTITION BY entity, attribute, slot ORDER BY story_order, t)
)
WHERE rn = 1 OR value != prev_value
ORDER BY entity, attribute, slot, story_order, t
"""


def _rows(sess, sql: str) -> list[dict]:
    import json
    res = sess.query(sql, "JSON")
    return json.loads(str(res))["data"]


def state_at(sess, work: str, story_order: int) -> set[tuple[str, str, str, str]]:
    """The world as of `story_order`: the set of (entity, attribute, slot, value) tuples
    that are currently true, one per (entity, attribute, slot). A slot the story has not
    reached yet is simply absent from the set."""
    sql = _STATE_AT.replace("{work}", _lit(work)).replace("{so}", str(int(story_order)))
    return {
        (r["entity"], r["attribute"], r["slot"], r["value"])
        for r in _rows(sess, sql)
    }


def global_inconsistencies(sess, work: str) -> list[Inconsistency]:
    """Reverts and vanished permanent features across the whole work.

    Ordered so the collapsed runs of one (entity, attribute, slot) arrive contiguously;
    each partition is examined once.
    """
    sql = _RUNS.replace("{work}", _lit(work))
    rows = _rows(sess, sql)

    # Group the already-ordered runs by their partition without reordering.
    partitions: dict[tuple[str, str, str], list[dict]] = {}
    for r in rows:
        partitions.setdefault((r["entity"], r["attribute"], r["slot"]), []).append(r)

    out: list[Inconsistency] = []
    for (entity, attribute, slot), runs in partitions.items():
        kind = runs[0]["entity_kind"]
        out.extend(_reverts(entity, kind, attribute, slot, runs))
        if attribute in PERMANENT:
            v = _vanished(entity, kind, attribute, slot, runs)
            if v is not None:
                out.append(v)
    return out


def _reverts(entity, kind, attribute, slot, runs) -> list[Inconsistency]:
    """A value that reappears in the collapsed run list held it earlier, lost it, and got
    it back. Report the first return per value; a value that oscillates is one finding, not
    one per swing."""
    first_seen: dict[str, int] = {}
    reported: set[str] = set()
    found: list[Inconsistency] = []
    for r in runs:
        v = r["value"]
        if v in first_seen and v not in reported:
            found.append(Inconsistency(
                "revert", entity, kind, attribute, slot,
                first_seen[v], r["story_order"], v, v,
            ))
            reported.add(v)
        elif v not in first_seen:
            first_seen[v] = r["story_order"]
    return found


def _vanished(entity, kind, attribute, slot, runs) -> Inconsistency | None:
    """A permanent feature was established (a present value) and the history ends on an
    absence. Ending on the absence is what proves there was no later re-establishment."""
    def absent(v: str) -> bool:
        return v.strip().lower() in _ABSENT

    if not absent(runs[-1]["value"]):
        return None  # the feature still stands at the last we heard of it

    present = [r for r in runs if not absent(r["value"])]
    if not present:
        return None  # never established; an absence that was always absent is not a loss

    established = present[0]
    # The disappearance is the first absent run after the feature was last present, so the
    # reported story point is where the world actually drops it, not merely the last row.
    last_present_order = present[-1]["story_order"]
    disappearance = next(
        r for r in runs if absent(r["value"]) and r["story_order"] > last_present_order
    )
    return Inconsistency(
        "vanished", entity, kind, attribute, slot,
        established["story_order"], disappearance["story_order"],
        established["value"], disappearance["value"],
    )
