"""Second-pass rigour on the extractor and the finding.

Search plus adjudication finds contradictions; this file is about not trusting a single
model call to have seen the world correctly in the first place. Three checks, each a
different way a confident answer can be wrong.

## Why any of this

An extraction pass is one draw from a distribution. Most of what it reports is stable
across draws — the coat is there every time — but a fraction is confabulated: a 0.95
earring that is not in the frame, asserted once and never again. A single pass cannot
tell the two apart, because both arrive with high confidence. Three passes can: the coat
survives a vote and the earring does not. That is `consensus`.

An open description is not a checkable claim. "Wearing a fedora" and "wearing a homburg"
are two answers to a question nobody asked closed; asked *fedora or homburg, pick one*
against the actual frame, the model has to commit, and a commitment can be scored.
That is `reverify`.

A finding produced by a system looking for findings is not yet evidence. The honest test
is to hand it to a model told to destroy it — invent the innocent explanation, the passed
time, the changed scene — and see whether it can. A flag that survives an adversary built
to kill it is worth more than one that was never attacked. That is `skeptic`, and its
default direction is set by the guardrail: when the skeptic's own answer is unreadable,
the finding stands. Caution keeps the flag.
"""

from __future__ import annotations

import json
from collections import Counter


def consensus(extract_fn, k: int = 3) -> list[dict]:
    """Run the extractor `k` times and keep only assertions a majority of runs agree on.

    `extract_fn` is a zero-argument callable returning a list of assertion dicts — a fresh
    draw each call, so passing a nonzero temperature is the point. Identity is
    (entity, attribute, value); a run votes at most once for a key even if it repeats it,
    because ten mentions in one pass are still one pass's opinion. The surviving dict is a
    representative from the first run that carried the key, so downstream columns
    (confidence, quote, shot) are preserved rather than synthesised.
    """
    seen: Counter = Counter()
    rep: dict = {}
    for _ in range(k):
        this_run: dict = {}
        for a in extract_fn():
            key = (a.get("entity"), a.get("attribute"), a.get("value"))
            if key not in this_run:
                this_run[key] = a
        for key, a in this_run.items():
            seen[key] += 1
            rep.setdefault(key, a)

    # Strict majority: more than half the runs. For k=3 that is >=2, so a lone
    # confabulation (1 of 3) is dropped and a two-thirds agreement is kept.
    threshold = k // 2 + 1
    return [rep[key] for key, n in seen.items() if n >= threshold]


REVERIFY_PROMPT = """\
Look only at THIS frame. Do not reason about the rest of the film.

For {attribute}, is it "{value_a}" or "{value_b}"?

Answer with exactly one of those two, copied verbatim, and nothing else.
"""


def reverify(client, frame_part, attribute: str, value_a: str, value_b: str,
             model: str) -> str | None:
    """Force a closed choice between two values against a single frame.

    Returns whichever of `value_a` / `value_b` the model names, or None when its answer
    matches neither — an unreadable answer to a two-way question is not a licence to guess
    one of them. `frame_part` is an opaque image part passed straight through to the call;
    this function does not construct or inspect it.
    """
    prompt = REVERIFY_PROMPT.format(attribute=attribute, value_a=value_a, value_b=value_b)
    raw = (client.models.generate_content(
        model=model, contents=[prompt, frame_part],
        config={"temperature": 0.0},
    ).text or "").strip().lower()

    hits = [v for v in (value_a, value_b) if v.strip().lower() in raw]
    # Exactly one of the two must be present. If the model echoed both, or neither, the
    # answer did not settle the question and there is nothing to return.
    return hits[0] if len(hits) == 1 else None


SKEPTIC_PROMPT = """\
A continuity flag has been raised on a film. Your job is to try to knock it down.

  {finding}

Argue for the innocent explanation. Did time pass, did the scene change, did the
character move or change clothes, is this two sides of the same cut with left and right
swapped, is the detail too small for this print to resolve? If any ordinary account
explains the change, the flag is refuted.

JSON only:
{{"refuted": true if you found an innocent explanation else false, "reason": str (one sentence)}}
"""


def skeptic(client, finding: str, model: str) -> dict:
    """Adversarially test a finding by asking the model to explain it away.

    Returns {"refuted": bool, "reason": str}. An unparseable or malformed answer is treated
    as *not refuted*: the skeptic exists to kill flags, so when its output cannot be read we
    keep the flag rather than let a broken response discard it. That defaulting direction is
    the guardrail (SPECIFICATION: defaults resolve toward refusing to pass), not an accident
    of parsing.
    """
    raw = client.models.generate_content(
        model=model, contents=[SKEPTIC_PROMPT.format(finding=finding)],
        config={"response_mime_type": "application/json", "temperature": 0.0},
    ).text or ""

    try:
        d = json.loads(raw)
        refuted = d["refuted"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"refuted": False, "reason": "skeptic response unparseable; flag kept"}
    if not isinstance(refuted, bool):
        return {"refuted": False, "reason": "skeptic verdict not boolean; flag kept"}
    return {"refuted": refuted, "reason": str(d.get("reason", ""))[:300]}
