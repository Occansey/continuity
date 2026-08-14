"""Decide which names refer to the same thing.

The extractor sees one frame at a time and has no way to know that the man it called
`Al` in shot 12 is the one it called `Al Roberts` in shot 90. It should not know: guessing
identity from a single frame is how you get confident nonsense, and pushing the guess into
extraction makes it invisible.

So identity is resolved once, afterwards, over the whole cast at once — which is also the
only point at which there is enough information to do it.

## Why this runs before anything else

A split identity does not produce a wrong answer. It produces a *missing* one. `Haskell`
and `Charles Haskell Jr.` become two timelines, each internally consistent, and the
contradiction between them is never looked for. Nothing in the output says so. On the
first run of this pipeline the cast of four had at least seven names, so an unknown but
non-trivial fraction of real contradictions were simply not searched for.

Recall failures that leave no trace are the worst kind, and they are the reason this is
not a later refinement.

## Why a model and not string similarity

`Al` and `Al Roberts` merge under any edit distance. `Vera` and `the hitchhiking woman`
do not, and they are the same character. Knowing that requires having followed the film,
which is a job for something that can read.
"""

from __future__ import annotations

import json

from continuity.retry import with_retry

PROMPT = """\
Below are entity names extracted independently from single frames and dialogue of one
film, with how often each appeared. Different names often refer to the same person, prop
or place, because whoever wrote each one could only see a single shot.

Group them. For each group give one canonical name — prefer a proper name when the film
supplies one, otherwise the clearest stable descriptor.

Rules that matter:

- **Merge only what you are confident is the same thing.** A wrong merge fuses two
  timelines and invents contradictions out of nothing. A missed merge only leaves things
  as they are. When unsure, leave it alone.
- **Roles are not identities.** "the driver" may be several people across a film. Keep it
  separate unless the film makes it one person.
- **Do not merge across kinds.** A person and a vehicle stay apart whatever they are called.
- Singletons are fine. Most names will be their own group.

Film: {work}

Names:
{names}

JSON only:
{{"groups": [{{"canonical": str, "members": [str], "confidence": float, "why": str}}]}}
"""


def resolve(client, names: list[tuple[str, str, int]], work: str, model: str) -> dict[str, str]:
    """Return a mapping from every name to its canonical form.

    `names` is (name, kind, count). Count is passed because frequency is evidence: a name
    appearing four hundred times is a principal and worth merging carefully, and one
    appearing once is usually an extra nobody needs to track.
    """
    listing = "\n".join(f"- {n}  [{k}]  x{c}" for n, k, c in sorted(names, key=lambda x: -x[2]))
    raw = with_retry(lambda: client.models.generate_content(
        model=model,
        contents=PROMPT.format(work=work, names=listing),
        config={"response_mime_type": "application/json", "temperature": 0.0},
    )).text or ""

    try:
        groups = json.loads(raw).get("groups", [])
    except json.JSONDecodeError:
        return {}

    known = {n for n, _, _ in names}
    kind_of = {n: k for n, k, _ in names}
    mapping: dict[str, str] = {}
    for g in groups:
        canonical = str(g.get("canonical", "")).strip()
        members = [str(m).strip() for m in g.get("members", []) if str(m).strip() in known]
        if not canonical or not members:
            continue
        # A group spanning kinds is a mistake in the answer, not an interesting merge.
        if len({kind_of[m] for m in members}) > 1:
            continue
        for m in members:
            mapping[m] = canonical
    # Anything unmentioned keeps its own name. Silence is not a merge.
    for n in known:
        mapping.setdefault(n, n)
    return mapping
