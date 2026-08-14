"""Turn shots into claims about the world.

This is the step that makes the whole approach possible and it is worth being precise
about what it is for. We are not describing the image. A description is prose, and prose
does not contradict prose in any way a machine can check. We are extracting **assertions**:
subject, attribute, value — small enough to join on, specific enough to be wrong.

The difference matters. "Al sits at the piano smoking, in a dark bar" cannot be compared
with anything. `(Al Roberts, holding, cigarette)` and `(cigarette, length, short)` can.

## Why the schema is this shape

An assertion has to survive being compared against another assertion made twenty minutes
of screen time later, by a different call, about a shot that looks nothing like this one.
So:

- **`entity` is a name, not a description.** "Vera", not "the woman in the passenger seat".
  Descriptions are relative to the shot; names are relative to the film. Entity resolution
  is a separate problem and pushing it into extraction makes it invisible.
- **`attribute` comes from a closed list.** An open vocabulary means `hair_colour` and
  `hairColor` and `hair` never join, and the contradiction search finds nothing while
  appearing to work. Closed lists are the difference between a query and a hope.
- **`value` is short and comparable.** "brown, shoulder length, worn down" is three
  assertions, not one.
- **`confidence` is the model's, and it is used to rank, never to filter.** A low-confidence
  assertion that contradicts a high-confidence one is exactly the case worth looking at.

## What it must not do

It must not decide anything is wrong. This step has no idea what came before and no
business having an opinion. Judgement happens later, over the store, with both sides
visible.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from pathlib import Path

# A closed vocabulary. Anything the film does that is not on this list is either not
# continuity or is an argument for extending the list on purpose.
ATTRIBUTES = [
    "wearing",        # garment, per garment
    "holding",        # object in hand
    "hair",           # style or state, not colour of the print
    "injury",         # visible damage, with its location
    "facial_hair",
    "accessory",      # watch, ring, glasses, hat
    "position",       # seated, standing, driving, at the wheel
    "time_of_day",
    "weather",
    "location",
    "vehicle_state",  # top up or down, door open, lights on
    "prop_state",     # glass full, cigarette length, door open
]

ENTITY_KINDS = ["person", "prop", "vehicle", "location", "environment"]

PROMPT = f"""\
You are extracting continuity assertions from single frames of a 1945 black and white
film. A continuity supervisor uses these to check that the world of the story stays
consistent across shots filmed days apart.

For each frame, list what is true of the world in it. Rules that matter:

- **Name entities, do not describe them.** Use a person's name if it is knowable from the
  frame or obvious from context; otherwise a stable descriptor you would use again for the
  same person ("the diner waitress"), never one that depends on this shot ("the man on the
  left").
- **One fact per assertion.** A garment, a single injury, one held object.
- **Only what you can see.** Do not infer that it is night because the story is at night.
  If it cannot be determined from the frame, leave it out.
- **The print is black and white.** Do not assert colour. Assert tone only when it is the
  point ("dark suit", "light dress").
- **Ignore film artefacts.** Scratches on the print, grain, dirt and splices are not
  injuries or props.

`attribute` must be one of: {", ".join(ATTRIBUTES)}
`entity_kind` must be one of: {", ".join(ENTITY_KINDS)}

Return JSON only:
{{"frames": [{{"shot": <int>, "assertions": [
  {{"entity": str, "entity_kind": str, "attribute": str, "value": str, "confidence": float}}
]}}]}}
"""


@dataclass(frozen=True)
class Assertion:
    shot: int
    t: float
    entity: str
    entity_kind: str
    attribute: str
    value: str
    confidence: float
    source: str = "image"   # or "dialogue"

    def to_dict(self) -> dict:
        return asdict(self)


def _part(path: Path) -> dict:
    return {"inline_data": {"mime_type": "image/jpeg",
                            "data": base64.b64encode(path.read_bytes()).decode()}}


def extract_batch(client, frames: list[tuple[int, float, Path]], model: str) -> list[Assertion]:
    """One call over several frames.

    Batched because a per-frame call costs the same prompt every time and the prompt is
    most of it. Small batches on purpose: a long batch invites the model to describe the
    sequence, and a sequence is a story, and a story is where inference creeps in.
    """
    contents = [PROMPT]
    for shot, _t, path in frames:
        contents.append(f"--- frame from shot {shot} ---")
        contents.append(_part(path))

    raw = client.models.generate_content(
        model=model,
        contents=contents,
        config={"response_mime_type": "application/json", "temperature": 0.0},
    ).text or ""

    by_shot = {shot: t for shot, t, _ in frames}
    out: list[Assertion] = []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return out

    for fr in parsed.get("frames", []):
        shot = fr.get("shot")
        if shot not in by_shot:
            # A shot number the batch did not contain. Dropped rather than guessed at:
            # an assertion attached to the wrong shot is worse than a missing one, because
            # it will contradict something truthfully and waste a human's time.
            continue
        for a in fr.get("assertions", []):
            if a.get("attribute") not in ATTRIBUTES:
                continue
            if a.get("entity_kind") not in ENTITY_KINDS:
                continue
            out.append(Assertion(
                shot=int(shot), t=by_shot[shot],
                entity=str(a.get("entity", "")).strip()[:80],
                entity_kind=a["entity_kind"],
                attribute=a["attribute"],
                value=str(a.get("value", "")).strip()[:80],
                confidence=float(a.get("confidence", 0.5)),
            ))
    return out
