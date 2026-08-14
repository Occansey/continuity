"""Give multi-valued attributes a slot, so a comparison compares like with like.

`wearing` is not one value. A person wears a hat and a jacket and a tie at once, and the
extractor emits one assertion per garment. Ordering those by time and comparing each with
the next asks whether a beret turned into a coat, which is not a question.

That bug accounted for **485 of 724 transitions on the first film, of which 78% compared
different garments** — roughly half of everything the search produced was noise of a kind
no amount of model quality could fix, because the query was malformed.

The fix is a slot: hat, outer, top, neck, legs, feet. Partitioning by
(entity, attribute, slot) instead of (entity, attribute) asks the right question — did
what was on their head change — and leaves the rest alone.

Slots are assigned once, over the distinct values, rather than during extraction. There
are a few hundred distinct garment descriptions in a film and tens of thousands of
assertions, so this is one cheap call instead of a re-run, and it can be re-done when the
vocabulary grows without touching the footage.
"""

from __future__ import annotations

import json

# Attributes where a subject can hold several values at once. Anything not listed here is
# single-valued and needs no slot: you are in one position, it is one time of day.
MULTIVALUED = {"wearing", "accessory", "holding", "injury", "prop_state"}

PROMPT = """\
Each line below is a value recorded for the attribute "{attribute}" in a film.

Assign each one a slot: the place on the body, or the kind of thing, that it occupies.
Two values in the same slot are alternatives — you cannot wear two hats. Two values in
different slots are worn or held at the same time and must never be compared.

Use these slots for `wearing`: hat, outer, top, neck, legs, feet, whole.
For `accessory`: head, ears, neck, wrist, hand, waist, eyes, other.
For `holding`: left_hand, right_hand, unknown_hand.
For `injury`: name the body part — hand, wrist, arm, face, head, leg, torso.
For `prop_state`: name the property — level, length, open_closed, lit, position.

If a value does not fit any slot, use "other".

Values:
{values}

JSON only: {{"slots": {{"<value>": "<slot>"}}}}
"""


def assign(client, attribute: str, values: list[str], model: str) -> dict[str, str]:
    if attribute not in MULTIVALUED or not values:
        return {}
    raw = client.models.generate_content(
        model=model,
        contents=PROMPT.format(attribute=attribute, values="\n".join(f"- {v}" for v in sorted(values))),
        config={"response_mime_type": "application/json", "temperature": 0.0},
    ).text or ""
    try:
        got = json.loads(raw).get("slots", {})
    except json.JSONDecodeError:
        return {}
    # Only values we actually asked about. A slot for something we never saw is a
    # hallucinated key and would partition rows that do not exist.
    return {v: str(got[v]) for v in values if v in got and isinstance(got[v], str)}
