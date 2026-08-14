"""Collapse near-synonym values so a comparison compares meanings, not phrasings.

The extractor is asked to describe a frame, and asked twice it will say "dark combed hair"
and "dark slicked-back hair" about the same head. Those are not a change in the world; they
are a change in the model's wording. Left alone they manufacture transitions and reverts —
on Detour, most of the 62 world-state "reverts" were exactly this — and the search cannot
tell a rephrasing from a real change because at the string level they look identical to one.

Canonicalization is the fix, and it is the same shape as slotting: over the *distinct*
values for an attribute, once, cluster the synonyms and map each to one canonical form.
A few hundred strings, one call, re-runnable when the vocabulary grows — never a re-run of
the footage.

## Why per attribute, and why the model

Synonymy is attribute-local: "light" means one thing for a shirt and another for the time
of day, so the clustering is done within an attribute, not globally. And whether two phrases
mean the same thing is world knowledge — "fedora" and "dark hat" may be the same object,
"fedora" and "cap" are not — which is a judgement, not a string distance. So it is a model
call, kept deterministic (temperature 0) and injected so tests need no API.

## What it must not do

It must not merge values that are genuinely different, because a wrong merge *hides* a real
continuity error — the failure that costs more here. So the prompt is told to keep values
apart when unsure, and the mapping only ever collapses; a value the model does not mention
keeps itself.
"""

from __future__ import annotations

import json

from continuity.retry import with_retry

PROMPT = """\
Below are the distinct values recorded for the attribute "{attribute}" across a film, each
a short description a vision model produced from a single frame. Different phrasings often
describe the same real thing, because the model worded the same observation two ways.

Group values that describe the SAME real-world state and give each group one canonical
value — the clearest, most specific phrasing in the group.

Rules that matter:
- Merge only phrasings of the same thing. "dark combed hair" and "dark slicked-back hair"
  are the same hair worded twice; "dark hair" and "blonde hair" are not; "fedora" and
  "dark hat" may be; "fedora" and "cap" are not.
- When unsure, keep values apart. A wrong merge hides a real continuity error, which is the
  expensive mistake. A missed merge only leaves a little noise.
- Do not normalise away a real difference in degree that a supervisor would care about
  (a full glass vs a half glass; a short vs a long cigarette).

Values:
{values}

JSON only: {{"canonical": {{"<original value>": "<canonical value>"}}}}
"""


def canonical_map(client, attribute: str, values: list[str], model: str) -> dict[str, str]:
    """Map each value for one attribute to its canonical form. Unmentioned values map to
    themselves — silence is not a merge."""
    if not values:
        return {}
    raw = with_retry(lambda: client.models.generate_content(
        model=model,
        contents=PROMPT.format(attribute=attribute, values="\n".join(f"- {v}" for v in sorted(values))),
        config={"response_mime_type": "application/json", "temperature": 0.0},
    )).text or ""
    try:
        got = json.loads(raw).get("canonical", {})
    except json.JSONDecodeError:
        return {v: v for v in values}
    # Only values we actually asked about; anything else is a hallucinated key. Everything
    # unmentioned keeps itself.
    out = {v: v for v in values}
    for v in values:
        if isinstance(got.get(v), str) and got[v].strip():
            out[v] = got[v].strip()
    return out


def canonicalize_rows(client, rows: list[dict], model: str) -> int:
    """Rewrite each row's value to its canonical form, in place. Returns how many rows
    changed, so the effect is visible rather than assumed."""
    by_attr: dict[str, set] = {}
    for r in rows:
        by_attr.setdefault(r["attribute"], set()).add(r["value"])
    mapping: dict[tuple[str, str], str] = {}
    for attr, vals in by_attr.items():
        for v, cv in canonical_map(client, attr, sorted(vals), model).items():
            mapping[(attr, v)] = cv
    changed = 0
    for r in rows:
        cv = mapping.get((r["attribute"], r["value"]), r["value"])
        if cv != r["value"]:
            r["value"] = cv
            changed += 1
    return changed
