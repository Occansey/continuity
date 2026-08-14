"""Group shots into scenes, and tell story order from screen order.

Three things depend on this and none of them work without it.

**The thesis depends on it.** The claim that separates this from the prior art is that we
catch contradictions *across* scenes, where no two frames resemble each other. Without
scene boundaries there is no across, and every result is indistinguishable from what a
registration-based method already does.

**Precision depends on it.** A person's position changes constantly inside a scene, because
that is what acting is. The same change across a cut between scenes is worth a look. The
attribute is identical; only the boundary tells them apart. That was the last remaining
false positive: Vera moves during her own strangling, and the search called it a
discontinuity.

**Ordering depends on it.** *Detour* is told almost entirely in flashback, so timecode
order is not story order, and a window function ordered by timecode is comparing the
present with the past and calling it a change. Every scene therefore carries a story
position as well as a screen position, and they are allowed to disagree.

## Why the model and not a cut detector

A scene boundary is not a visual event. Two shots of the same room minutes apart are one
scene; two shots of the same actor in different rooms are two. What makes a scene is
continuity of time and place, and reading that requires following the film. Shot
boundaries are arithmetic; scene boundaries are comprehension.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

PROMPT = """\
Below is a list of shots from the 1945 film Detour, with the dialogue spoken during each.

Group consecutive shots into **scenes**. A scene is a stretch of continuous time in one
place. A new scene begins when the story moves to a different place, or jumps forward or
backward in time.

Then give each scene its position in the **story**, which is not the same as its position
in the film. Detour is narrated in flashback: a man sits in a diner and tells us what
happened to him. The diner is the latest point in the story and it appears first and last
on screen.

For each scene give:

- `shots`: first and last shot number
- `place`: short description, e.g. "roadside diner", "Haskell's convertible, desert road"
- `story_order`: an integer. Scenes that happen at the same point in the story share a
  number. The earliest thing that happens in the story is 0.
- `frame`: `"present"` if this is the narration frame, `"flashback"` if it is the story
  being told.

Shots:
{shots}

JSON only:
{{"scenes": [{{"shots": [int, int], "place": str, "story_order": int, "frame": str}}]}}
"""


@dataclass(frozen=True)
class Scene:
    n: int
    shot_from: int
    shot_to: int
    t_from: float
    t_to: float
    place: str
    story_order: int
    frame: str

    def to_dict(self) -> dict:
        return asdict(self)


def _listing(shots: list[dict], transcript: list[dict]) -> str:
    out = []
    for s in shots:
        said = [l["text"] for l in transcript if s["start"] <= l["t"] < s["end"]]
        line = f'{s["n"]:>3} [{s["start"]:.0f}s-{s["end"]:.0f}s]'
        if said:
            joined = " / ".join(said)[:180]
            line += f"  {joined}"
        out.append(line)
    return "\n".join(out)


def segment(client, shots: list[dict], transcript: list[dict], model: str,
            chunk: int = 90, overlap: int = 8) -> list[Scene]:
    """Segment in overlapping chunks, then stitch.

    Overlap matters: a boundary decided at the very edge of a chunk is decided without the
    context on the other side of it, which is exactly where a scene change is hardest to
    see. Where two chunks disagree about the shots they share, the later chunk wins,
    because it had more of what follows.
    """
    scenes: list[Scene] = []
    i = 0
    while i < len(shots):
        window = shots[i : i + chunk]
        raw = client.models.generate_content(
            model=model,
            contents=PROMPT.format(shots=_listing(window, transcript)),
            config={"response_mime_type": "application/json", "temperature": 0.0},
        ).text or ""
        try:
            got = json.loads(raw).get("scenes", [])
        except json.JSONDecodeError:
            got = []

        by_n = {s["n"]: s for s in window}
        for sc in got:
            pair = sc.get("shots") or []
            if len(pair) != 2:
                continue
            a, b = int(pair[0]), int(pair[1])
            if a not in by_n or b not in by_n:
                continue
            # Drop anything the previous chunk already covered, except in the overlap,
            # where this chunk is the better-informed one.
            if scenes and a <= scenes[-1].shot_to and b <= scenes[-1].shot_to:
                continue
            if scenes and a <= scenes[-1].shot_to:
                scenes[-1] = Scene(**{**scenes[-1].to_dict(), "shot_to": a - 1,
                                      "t_to": by_n[a]["start"]})
            scenes.append(Scene(
                n=len(scenes), shot_from=a, shot_to=b,
                t_from=by_n[a]["start"], t_to=by_n[b]["end"],
                place=str(sc.get("place", ""))[:80],
                story_order=int(sc.get("story_order", 0)),
                frame=str(sc.get("frame", "flashback")),
            ))
        i += chunk - overlap
    return scenes


def renumber(scenes: list[Scene]) -> list[Scene]:
    """Make story order global rather than per chunk.

    The model sees ninety shots at a time and numbers the story from zero inside each
    chunk, so scene 8 and scene 9 both came back as story position 4. Locally correct,
    globally meaningless — and the ordering is the thing the whole contradiction search
    depends on, so a per-chunk number is worse than none.

    Detour's structure makes the global answer recoverable: a framing device in the
    present, and a flashback told forwards. So flashback scenes take their screen order,
    and present scenes go last, because the narration is the latest thing that happens.

    This is specific to a film told this way. A film that intercuts two timelines needs
    the model to order it globally, with the previous chunk's scenes in view, and that is
    a bigger job than this one. Recorded rather than pretended away.
    """
    out, n = [], 0
    for s in scenes:
        if s.frame == "present":
            out.append(Scene(**{**s.to_dict(), "story_order": 10_000 + s.n}))
        else:
            out.append(Scene(**{**s.to_dict(), "story_order": n}))
            n += 1
    return out


def scene_of(scenes: list[Scene], t: float) -> Scene | None:
    for s in scenes:
        if s.t_from <= t <= s.t_to:
            return s
    return None
