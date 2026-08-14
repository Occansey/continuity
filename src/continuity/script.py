"""The contract the script writes, checked against the footage that was shot.

Everything else in this system reads the film and looks for a place where it disagrees with
itself. That finds the errors that are *internal* to the footage — a coat that changes
between two cuts — but it is blind to a whole other class: the footage is internally
consistent and consistently *wrong about what the story said should be true*. If the
screenplay establishes a scar in scene 4 and every later shot agrees there is no scar, the
transition search sees no transition, the world-state sees no revert, and the error is
invisible. Nothing in the footage contradicts anything else in the footage.

So this module derives the *intended* world-state from the script before a frame is judged.
The screenplay is an assertion about what should hold, made independently of the camera, and
that independence is the point: two sources that were produced separately can disagree, and
the disagreement is the finding a single source cannot produce.

Two pieces, deliberately split the way the rest of the system splits them:

  * `extract_contract` — the reading of the script, which is comprehension and therefore the
    model's job: per scene, the facts the story asserts should hold, plus a `must_match`
    list naming earlier-established facts this scene *depends on* (an injury established
    earlier must still be present; the script does not re-state it, but it is still promised).

  * `contract_violations` — the comparison against what was actually extracted from the
    footage, which is arithmetic on strings and therefore stays out of the model's hands. It
    is pure and deterministic: given the contract and the observed assertions, a scene is
    flagged only where an observed value contradicts a value the contract promised.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Fact:
    """One thing the script says should be true: an entity, an attribute, and the value it
    should hold. `slot` is carried for the same reason the store carries it — `wearing` is a
    set, not a value, and a coat and a hat are different promises about the same person."""
    entity: str
    attribute: str
    value: str
    slot: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SceneContract:
    """What the story promises for one scene.

    `facts` are established or restated *in* this scene. `must_match` are facts established in
    an earlier scene that this scene silently relies on remaining true — the class of error a
    footage-only search cannot reach, because the script never repeats the claim for the
    footage to contradict.
    """
    scene: int
    story_order: int
    facts: tuple[Fact, ...]
    must_match: tuple[Fact, ...]

    def to_dict(self) -> dict:
        return {
            "scene": self.scene,
            "story_order": self.story_order,
            "facts": [f.to_dict() for f in self.facts],
            "must_match": [f.to_dict() for f in self.must_match],
        }


@dataclass(frozen=True)
class Violation:
    """A scene where the footage contradicts what the script promised.

    `expected` is the script's value, `observed` is what the extractor read from the frame.
    `kind` says whether the broken promise was made in this scene (`scene`) or inherited from
    an earlier one (`must_match`) — the second is the interesting case, the one no
    footage-internal search produces.
    """
    scene: int
    entity: str
    attribute: str
    slot: str
    expected: str
    observed: str
    kind: str            # 'scene' | 'must_match'
    quote: str           # the observed assertion's quote, for the adjudicator


PROMPT = """\
Below is a film's transcript and its scene list. Read the story and write, for each scene,
the CONTRACT the story asserts should be true on screen — the continuity a faithful shoot
must honour.

For each scene give two lists of facts:

- `facts`: what the story establishes or restates IN this scene. A fact is an entity, an
  attribute, and the value it should hold. Use these attributes only: wearing, holding,
  hair, injury, facial_hair, accessory, position, time_of_day, weather, location,
  vehicle_state, prop_state. For a multi-valued attribute like `wearing`, name the `slot`
  (hat, outer, top, neck); otherwise leave `slot` empty.

- `must_match`: facts established in an EARLIER scene that this scene depends on and that
  must still hold, even though the story does not restate them. An injury, a scar, a changed
  hairstyle, a permanent prop state — anything the audience would expect to persist.

Only assert what the story commits to. Do not invent detail the script does not fix.

Transcript:
{transcript}

Scenes:
{scenes}

JSON only:
{{"contracts": [{{"scene": int, "facts": [{{"entity": str, "attribute": str, "value": str, "slot": str}}], "must_match": [{{"entity": str, "attribute": str, "value": str, "slot": str}}]}}]}}
"""


def _transcript_text(lines: list[dict]) -> str:
    out = []
    for l in lines:
        who = l.get("speaker", "")
        out.append(f'[{l.get("t", 0):.0f}s] {who}: {l.get("text", "")}')
    return "\n".join(out)


def _scenes_text(scenes: list[dict]) -> str:
    out = []
    for s in scenes:
        out.append(
            f'scene {s.get("n")}: story_order={s.get("story_order")} '
            f'[{s.get("t_from", 0):.0f}s-{s.get("t_to", 0):.0f}s]'
        )
    return "\n".join(out)


def _facts(raw: object) -> tuple[Fact, ...]:
    if not isinstance(raw, list):
        return ()
    out = []
    for f in raw:
        if not isinstance(f, dict):
            continue
        entity = str(f.get("entity", "")).strip()
        attribute = str(f.get("attribute", "")).strip()
        value = str(f.get("value", "")).strip()
        # A fact without all three names nothing checkable; drop it rather than let an empty
        # promise match an empty observation and manufacture a violation.
        if not (entity and attribute and value):
            continue
        out.append(Fact(entity, attribute, value, str(f.get("slot", "")).strip()))
    return tuple(out)


def extract_contract(client, transcript_lines: list[dict], scenes: list[dict],
                     model: str) -> list[SceneContract]:
    """Read the script into a per-scene contract of intended world-state.

    `scenes` is the scene list — dicts carrying at least `n`, `t_from`, `t_to`,
    `story_order`. The model returns the facts; this function only maps each returned scene
    back to its story position and drops malformed facts. A scene number the model invents
    that is not in `scenes` is ignored — the contract is anchored to the scenes we actually
    have, not to the ones the model wishes it had.

    An unparseable response yields an empty contract list: with nothing read from the script
    there is nothing to check, and inventing promises from a broken parse would be worse than
    checking none.
    """
    story_order = {int(s["n"]): int(s.get("story_order", -1)) for s in scenes}

    raw = (client.models.generate_content(
        model=model,
        contents=PROMPT.format(
            transcript=_transcript_text(transcript_lines),
            scenes=_scenes_text(scenes),
        ),
        config={"response_mime_type": "application/json", "temperature": 0.0},
    ).text or "")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    # Accept {"contracts":[...]} or a bare array, the same latitude scenes.py allows: both
    # are valid readings of "list the contracts", and a shape preference should not lose a
    # whole film.
    got = parsed.get("contracts", []) if isinstance(parsed, dict) else parsed
    if not isinstance(got, list):
        return []

    out: list[SceneContract] = []
    for c in got:
        if not isinstance(c, dict) or "scene" not in c:
            continue
        try:
            scene = int(c["scene"])
        except (TypeError, ValueError):
            continue
        if scene not in story_order:
            continue
        out.append(SceneContract(
            scene=scene,
            story_order=story_order[scene],
            facts=_facts(c.get("facts")),
            must_match=_facts(c.get("must_match")),
        ))
    return out


def _norm(s: str) -> str:
    return str(s).strip().lower()


def _matches(fact: Fact, obs: dict) -> bool:
    """Whether an observed assertion is *about the same thing* the fact promises.

    Entity and attribute must agree. Slot agrees when the fact fixes one; a fact that names
    no slot is a promise about the attribute at large and matches any slot, so a script that
    does not bother to say which layer the coat is still matches the coat the frame reports.
    """
    if _norm(fact.entity) != _norm(obs.get("entity", "")):
        return False
    if _norm(fact.attribute) != _norm(obs.get("attribute", "")):
        return False
    if fact.slot and _norm(fact.slot) != _norm(obs.get("slot", "")):
        return False
    return True


def _violations_for(scene: int, facts: tuple[Fact, ...], kind: str,
                    observed: list[dict]) -> list[Violation]:
    out: list[Violation] = []
    for fact in facts:
        for obs in observed:
            if not _matches(fact, obs):
                continue
            # Same entity/attribute/slot, different value: the footage read something other
            # than what the script promised. Equality is agreement, not a finding; only the
            # disagreement is flagged, and the first one per promise is enough to raise it.
            if _norm(obs.get("value", "")) != _norm(fact.value):
                out.append(Violation(
                    scene=scene, entity=fact.entity, attribute=fact.attribute,
                    slot=fact.slot, expected=fact.value,
                    observed=str(obs.get("value", "")), kind=kind,
                    quote=str(obs.get("quote", "")),
                ))
                break  # one broken promise per fact; do not report every later frame of it
    return out


def contract_violations(contracts: list[SceneContract],
                        observed_assertions: list[dict]) -> list[Violation]:
    """Flag scenes where the footage contradicts the script's contract.

    Pure and deterministic. For each scene contract, the observed assertions extracted from
    that scene's footage are compared against both the scene's own `facts` and the
    `must_match` facts it inherits. A violation is a same-(entity, attribute, slot) pair whose
    observed value differs from the promised one. A promise the footage never speaks to is not
    a violation — silence is not contradiction — which keeps this from flagging every fact the
    extractor happened not to mention.
    """
    by_scene: dict[int, list[dict]] = {}
    for a in observed_assertions:
        try:
            s = int(a.get("scene", -1))
        except (TypeError, ValueError):
            continue
        by_scene.setdefault(s, []).append(a)

    out: list[Violation] = []
    for contract in contracts:
        observed = by_scene.get(contract.scene, [])
        if not observed:
            continue
        out.extend(_violations_for(contract.scene, contract.facts, "scene", observed))
        out.extend(_violations_for(contract.scene, contract.must_match, "must_match", observed))
    return out
