"""The continuity bible, derived rather than kept.

A production keeps a bible by hand: the running record of what is true of each character
and place — what they wear, what they carry, the state of the world — so the next day's
shooting matches the last. It is out of date the moment anyone shoots, because it is a
document a person maintains alongside the work instead of from it.

The assertions table already holds every established fact with the shot and timecode it
was established at, in story order. So the bible is a *view* of that table, not a second
copy of it: for each principal entity, walk its assertions in story order and record the
moments its world changed. It is current because it is read, not written, and it is
timecoded because the store never dropped where a fact came from.

This is the same table and the same story-order walk the contradiction search runs
(`store.TRANSITIONS`); the difference is only the question asked of it. The search keeps
the transitions that look wrong; the bible keeps all of them, because to a script
supervisor every change of state is a thing to hold on to, not a thing to flag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Fact:
    """One established value, with where in the story it took hold."""

    attribute: str
    slot: str
    value: str
    scene: int
    t: float
    story_order: int
    source: str
    confidence: float

    @property
    def key(self) -> str:
        # A multi-valued attribute is a set of independent tracks; the slot names the
        # track. `wearing`/`hat` and `wearing`/`outer` are two facts held at once, not one
        # fact overwriting another, so they are keyed apart.
        return f"{self.attribute}/{self.slot}" if self.slot else self.attribute


@dataclass
class EntityBible:
    entity: str
    entity_kind: str
    assertions: int
    # Keyed by Fact.key, each a timeline of establishments in story order. A track with a
    # single entry is a fact that held for the whole film; more than one is a change the
    # production has to match to.
    timelines: dict[str, list[Fact]] = field(default_factory=dict)


@dataclass
class Bible:
    work: str
    entities: list[EntityBible] = field(default_factory=list)


def _esc(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


def build_bible(sess, work: str, top: int = 6) -> Bible:
    """Derive the bible for the top `top` principal entities of `work`.

    Principals are ranked by assertion count: the more the film establishes about an
    entity, the more a production has to keep straight about it, so that is what earns a
    place in the bible. Extras that appear in a single shot carry no continuity burden and
    are left out.
    """
    rows = _fetch(sess, work)

    counts: dict[str, int] = {}
    kinds: dict[str, str] = {}
    for r in rows:
        counts[r["entity"]] = counts.get(r["entity"], 0) + 1
        kinds[r["entity"]] = r["entity_kind"]

    principals = sorted(counts, key=lambda e: (-counts[e], e))[:top]

    bible = Bible(work=work)
    for entity in principals:
        eb = EntityBible(entity=entity, entity_kind=kinds[entity],
                         assertions=counts[entity])
        for r in rows:
            if r["entity"] != entity:
                continue
            fact = Fact(
                attribute=r["attribute"], slot=r["slot"], value=r["value"],
                scene=int(r["scene"]), t=float(r["t"]),
                story_order=int(r["story_order"]), source=r["source"],
                confidence=float(r["confidence"]),
            )
            track = eb.timelines.setdefault(fact.key, [])
            # The rows arrive in story order, so a value equal to the last one on this
            # track is the same fact still holding, not a new establishment. Only a change
            # earns a new entry; that is what turns a stream of observations into a
            # timeline.
            if track and track[-1].value == fact.value:
                continue
            track.append(fact)
        bible.entities.append(eb)
    return bible


def _fetch(sess, work: str) -> list[dict]:
    sql = (
        "SELECT entity, entity_kind, attribute, slot, value, scene, t, "
        "story_order, source, confidence FROM assertions "
        f"WHERE work = '{_esc(work)}' "
        "ORDER BY entity, attribute, slot, story_order, t"
    )
    res = sess.query(sql, "JSON")
    payload = str(res).strip()
    if not payload:
        return []
    return json.loads(payload).get("data", [])


def _timecode(t: float) -> str:
    total = int(t)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def render_markdown(bible: Bible) -> str:
    """Render the bible as a readable document: per entity, a table of its facts and how
    they change across story time.

    Ordered so a reader can scan it the way a script supervisor would — one entity at a
    time, each fact and every value it takes, with the scene and timecode the change was
    established at so it can be found in the cut.
    """
    lines = [f"# Continuity bible — {bible.work}", ""]
    for eb in bible.entities:
        lines.append(f"## {eb.entity}")
        lines.append(f"*{eb.entity_kind} · {eb.assertions} assertions*")
        lines.append("")
        lines.append("| Fact | Value | Scene | Timecode |")
        lines.append("| --- | --- | --- | --- |")
        for key in sorted(eb.timelines):
            for f in eb.timelines[key]:
                lines.append(
                    f"| {key} | {f.value} | {f.scene} | {_timecode(f.t)} |"
                )
        lines.append("")
    return "\n".join(lines)
