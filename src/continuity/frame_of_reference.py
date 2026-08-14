"""Tell a mirror artifact apart from a real change of side.

V1's largest false-positive class was left/right. The search would find a person on the
left of one shot and the right of the next and call it a discontinuity — but a reverse
angle swaps left and right in the *frame* without anything moving in the *world*. Cross
the line and the driver on the left of a shot from behind the car is on the right of a
shot through the windscreen; nobody changed seats.

The distinction is not left-versus-right, it is *whose* left. A person's placement within
the frame is measured against the camera, and the camera moves. A watch on their left
wrist, a scar on their left cheek, a hat worn to one side — those are measured against the
body, and the body's left is the body's left from every angle. So a wrist that swaps is a
candidate worth judging; a screen side that swaps is a coordinate artifact to explain away.

This module does not decide anything on its own. It marks the camera-relative flips so the
adjudicator is not handed a mirror as if it were a mistake, and it carries the same
distinction into the prompt as `GUIDANCE`, because the model has to apply it to the one
case a token match cannot see — a value that names a side without the word "left" in it.
"""

from __future__ import annotations

import re

# Every attribute in the store's schema, tagged by whose frame its values are measured in.
#
# Only `position` is camera-relative: it is where the subject sits *in the shot*, and the
# shot can be taken from anywhere. Everything else is measured against the world or the
# body and does not flip when the camera crosses the line — a left wrist, a left-hand
# hold, a scar on the left cheek read the same from every angle, and a road, a sky or a
# time of day has no screen side at all. Defaulting the unlisted-by-hand cases toward
# 'world' is the safe direction here: it keeps a genuine left/right change as a candidate
# rather than silently discarding it as an artifact.
REFERENCE: dict[str, str] = {
    "wearing": "world",
    "holding": "world",
    "hair": "world",
    "injury": "world",
    "facial_hair": "world",
    "accessory": "world",
    "position": "camera",
    "time_of_day": "world",
    "weather": "world",
    "location": "world",
    "vehicle_state": "world",
    "prop_state": "world",
}

_SIDE = re.compile(r"\b(left|right)\b", re.IGNORECASE)


def _side(value: str) -> str | None:
    """The side a value names, or None. When a value names both (a rare 'left to right'),
    it is not a clean side and we decline to read one rather than guess."""
    found = {m.lower() for m in _SIDE.findall(value or "")}
    if len(found) == 1:
        return found.pop()
    return None


def is_spurious_flip(attribute: str, value_from: str, value_to: str) -> bool:
    """True when the only difference is a left/right side and that side is camera-relative
    — a reverse-angle mirror to explain away, not a change in the world.

    False when either value names no side (there is no flip to explain), when both name
    the same side (the difference is elsewhere), or when the attribute is world-relative
    (a watch does not change wrists; that is a genuine candidate)."""
    a, b = _side(value_from), _side(value_to)
    if a is None or b is None or a == b:
        return False
    return REFERENCE.get(attribute) == "camera"


# Injected into the adjudication prompt. The token match above catches the values that say
# "left"; this is for the ones that don't, and for the judgement the database cannot make.
GUIDANCE = (
    "A person's own left and right are fixed to their body and read the same from every "
    "angle: a watch on the left wrist, a scar on the left cheek, an object in the left "
    "hand. Treat those as world-relative — a swap to the other side is a real change. "
    "Which side of the frame a subject appears on is measured against the camera, and a "
    "reverse angle mirrors it without anything moving. Treat screen side as "
    "camera-relative and do not report it as an error."
)
