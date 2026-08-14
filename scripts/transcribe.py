"""Transcribe dialogue, and pull out the assertions the dialogue makes.

Dialogue matters here for a reason specific to this project. The documented error we are
chasing in Detour is that Al *says* the scratches are "about a quarter of an inch apart"
and the hand *shown* has them three times that. There are no two frames to compare. The
contradiction is between what the film says and what it shows, and it is invisible to
every method that works on pixels.

So the transcript is not context. It is a second source of assertions, in the same shape
as the visual ones, and the interesting contradictions are the ones that cross between.
"""
import concurrent.futures, json, os, sys
from pathlib import Path
sys.path.insert(0, "src")
from google import genai
from continuity.extract import ATTRIBUTES, ENTITY_KINDS

MODEL = os.environ.get("CONTINUITY_MODEL", "gemini-3.6-flash")
PROMPT = f"""\
This is ten minutes of audio from the 1945 film Detour, starting at {{offset}} seconds into
the film. Do two things.

1. Transcribe the dialogue with timestamps, in seconds from the start of THIS clip.

2. Extract assertions that the dialogue makes about the physical world — things a
continuity supervisor would have to keep true. A character stating a fact about an object,
a person, an injury, a place, a time. Include measurements and quantities exactly as
spoken.

Ignore assertions about feelings, intentions, opinions, or the future. Only claims about
how the world is or was.

`attribute` must be one of: {", ".join(ATTRIBUTES)}
`entity_kind` must be one of: {", ".join(ENTITY_KINDS)}

JSON only:
{{{{"lines": [{{{{"t": float, "speaker": str, "text": str}}}}],
   "assertions": [{{{{"t": float, "entity": str, "entity_kind": str, "attribute": str,
                   "value": str, "quote": str, "confidence": float}}}}]}}}}
"""

client = genai.Client(vertexai=True, location="global")

def run(i: int):
    p = Path(f"work/audio/chunk_{i}.mp3")
    offset = i * 600
    raw = client.models.generate_content(
        model=MODEL,
        contents=[PROMPT.format(offset=offset),
                  {"inline_data": {"mime_type": "audio/mpeg", "data": p.read_bytes()}}],
        config={"response_mime_type": "application/json", "temperature": 0.0},
    ).text or ""
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return [], []
    lines = [{**l, "t": float(l.get("t", 0)) + offset} for l in d.get("lines", [])]
    asserts = []
    for a in d.get("assertions", []):
        if a.get("attribute") not in ATTRIBUTES or a.get("entity_kind") not in ENTITY_KINDS:
            continue
        asserts.append({
            "shot": -1, "t": float(a.get("t", 0)) + offset,
            "entity": str(a.get("entity",""))[:80], "entity_kind": a["entity_kind"],
            "attribute": a["attribute"], "value": str(a.get("value",""))[:80],
            "confidence": float(a.get("confidence", 0.5)), "source": "dialogue",
            "quote": str(a.get("quote",""))[:200],
        })
    return lines, asserts

chunks = sorted(int(p.stem.split("_")[1]) for p in Path("work/audio").glob("chunk_*.mp3"))
L, A = [], []
with concurrent.futures.ThreadPoolExecutor(4) as ex:
    for lines, asserts in ex.map(run, chunks):
        L.extend(lines); A.extend(asserts)
L.sort(key=lambda x: x["t"]); A.sort(key=lambda x: x["t"])
json.dump(L, open("work/transcript.json","w"), indent=1)
with open("work/assertions_dialogue.jsonl","w") as f:
    for a in A: f.write(json.dumps(a)+"\n")
print(f"  {len(L)} dialogue lines · {len(A)} spoken assertions")
