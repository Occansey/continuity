"""Decide whether a change is an error.

This is the product. Everything before it finds *changes*, and a story is made of changes,
so a list of them is worth nothing — 713 on one film, or 1,340 in a competing product's
own marketing. The question that matters is never *did it change*. It is **did anything
happen that explains it**.

## What the model is asked, and what it is not

It is asked one question about one pair, with both frames and the dialogue around them. It
is not asked to find anything, rank anything, or consider the film as a whole. Search
already happened, in the database, over everything; this is judgement on a shortlist.

That division is deliberate. A model asked to search a corpus it cannot afford to read
will answer anyway, about the part it saw, and there is no way to tell from the answer.

## Why the verdicts are these four

`explained` is the common case and the one that keeps the tool switched on: he changed
his shirt, an hour passed, she healed. `error` is the finding. `unresolvable` is for when
the frames genuinely cannot settle it — a 494x360 transfer of a 1945 print will not
resolve a wristwatch — and it exists so the model does not have to choose between lying
and staying silent. `not_comparable` catches our own bugs: two assertions that were never
about the same thing, which on the first run was most of the cross-modal candidates.

The last one matters more than it looks. Without it, a schema failure arrives dressed as
a continuity error, and we would tune the model to fix a bug in the vocabulary.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from pathlib import Path

VERDICTS = ["error", "explained", "unresolvable", "not_comparable"]

PROMPT = """\
You are a script supervisor checking one pair of observations from the 1945 film Detour,
a black and white feature shot in six days.

Two claims were made about the same thing at different points in the film. Decide whether
this is a continuity error.

  Entity:     {entity}  ({entity_kind})
  Attribute:  {attribute}

  At {t_from} ({source_from}): {value_from}
  At {t_to} ({source_to}): {value_to}
{quotes}
Dialogue around the first observation:
{ctx_from}

Dialogue around the second observation:
{ctx_to}

Answer with one verdict:

- **explained** — the change is normal. Time passed, the character changed clothes, they
  moved, the wound healed, a different scene entirely. This is the usual answer and you
  should reach for it first.
- **error** — the world contradicts itself and nothing accounts for it. A wound that moves
  to the other hand. A ring worn before it was given. Something described one way and
  shown another.
- **unresolvable** — it might be an error but this print cannot settle it. Low resolution,
  motion blur, the detail is out of frame or too small.
- **not_comparable** — the two claims were never about the same thing, so there is nothing
  to contradict. A claim about where someone *was picked up* is not a claim about where
  they are *sitting*.

**Before judging any claim about left or right, work out where the camera is.** These two
frames may be shot from opposite sides of the subject. When the camera crosses the line,
left and right swap in the frame: a driver on the left of a shot taken from behind a car
is on the right of a shot taken through the windscreen, and that is not a change in the
world. A person's own left and right never change; which side of the frame they appear on
changes constantly.

**This print is {width} by {height} and was struck from a 1945 release.** A detail smaller
than roughly a fiftieth of the frame width cannot be resolved on it. If your judgement
depends on such a detail — an earring, a ring, the spacing of marks on skin, the length of
a cigarette — then this print cannot settle it and the answer is **unresolvable**, whatever
you think you can see. Saying so is a correct answer here, not a failure to answer.

Judge the film, not the print. Scratches, grain, dirt and splices are not continuity
errors. Reused backdrops and stock footage are this film's normal condition.

Be strict about **error**. A false alarm on a working set costs a crew's time, and two of
them get the tool switched off.

JSON only:
{{"verdict": one of {verdicts}, "confidence": float, "reason": str (one sentence)}}
"""


@dataclass(frozen=True)
class Verdict:
    entity: str
    attribute: str
    t_from: float
    t_to: float
    value_from: str
    value_to: str
    verdict: str
    confidence: float
    reason: str
    cross_modal: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _img(path: Path) -> dict | None:
    if not path.exists():
        return None
    return {"inline_data": {"mime_type": "image/jpeg",
                            "data": base64.b64encode(path.read_bytes()).decode()}}


def _context(transcript: list[dict], t: float, window: float = 22.0) -> str:
    lines = [l for l in transcript if abs(l["t"] - t) <= window]
    if not lines:
        return "  (no dialogue nearby)"
    return "\n".join(f"  {l['t']:.0f}s {l.get('speaker','?')}: {l['text'][:150]}" for l in lines[:8])


def adjudicate(client, tr: dict, transcript: list[dict], model: str,
               frames_dir: Path = Path("work/frames"),
               print_size: tuple[int, int] = (494, 360)) -> Verdict | None:
    quotes = ""
    if tr.get("quote_from"):
        quotes += f'\n  Spoken at {tr["t_from"]:.0f}s: "{tr["quote_from"]}"'
    if tr.get("quote_to"):
        quotes += f'\n  Spoken at {tr["t_to"]:.0f}s: "{tr["quote_to"]}"'
    if quotes:
        quotes += "\n"

    prompt = PROMPT.format(
        entity=tr["entity"], entity_kind=tr["entity_kind"], attribute=tr["attribute"],
        t_from=f'{tr["t_from"]:.0f}s', t_to=f'{tr["t_to"]:.0f}s',
        source_from=tr["source_from"], source_to=tr["source_to"],
        value_from=tr["value_from"], value_to=tr["value_to"],
        quotes=quotes,
        ctx_from=_context(transcript, tr["t_from"]),
        ctx_to=_context(transcript, tr["t_to"]),
        verdicts=VERDICTS,
        width=print_size[0], height=print_size[1],
    )

    contents: list = [prompt]
    for label, shot in (("first", tr["shot_from"]), ("second", tr["shot_to"])):
        part = _img(frames_dir / f"s{int(shot):04d}.jpg") if int(shot) >= 0 else None
        if part:
            contents += [f"--- {label} observation, shot {shot} ---", part]

    raw = client.models.generate_content(
        model=model, contents=contents,
        config={"response_mime_type": "application/json", "temperature": 0.0},
    ).text or ""

    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if d.get("verdict") not in VERDICTS:
        return None

    return Verdict(
        entity=tr["entity"], attribute=tr["attribute"],
        t_from=tr["t_from"], t_to=tr["t_to"],
        value_from=tr["value_from"], value_to=tr["value_to"],
        verdict=d["verdict"], confidence=float(d.get("confidence", 0.5)),
        reason=str(d.get("reason", ""))[:300],
        cross_modal=tr["source_from"] != tr["source_to"],
    )
