"""Resolve identities, re-search, then adjudicate."""
import concurrent.futures, json, os, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, "src")
import chdb.session as chs
from google import genai
from continuity.adjudicate import adjudicate
from continuity.entities import resolve
from continuity.slots import MULTIVALUED, assign
from continuity.store import TRANSITIONS, load, read_jsonl

MODEL = os.environ.get("CONTINUITY_MODEL", "gemini-3.6-flash")
WORK = "detour-1945"
client = genai.Client(vertexai=True, location="global")

rows = read_jsonl("work/assertions.jsonl", "work/assertions_dialogue.jsonl")

# ── 1. identity ──────────────────────────────────────────────────────────────
counts = Counter((r["entity"], r["entity_kind"]) for r in rows)
names = [(n, k, c) for (n, k), c in counts.items()]
mapping = resolve(client, names, WORK, MODEL)
merged = {k: v for k, v in mapping.items() if k != v}
print(f"  {len(names)} names -> {len(set(mapping.values()))} entities ({len(merged)} merged)")
for k, v in sorted(merged.items())[:10]:
    print(f"     {k[:34]:<36} -> {v}")
json.dump(mapping, open("work/entity_map.json", "w"), indent=1)
for r in rows:
    r["entity"] = mapping.get(r["entity"], r["entity"])

# ── 1b. slots ────────────────────────────────────────────────────────────────
# Multi-valued attributes get a slot so the window compares like with like. Assigned over
# the distinct values, once, rather than during extraction: a few hundred strings instead
# of tens of thousands of rows.
by_attr_vals: dict[str, set] = {}
for r in rows:
    if r["attribute"] in MULTIVALUED:
        by_attr_vals.setdefault(r["attribute"], set()).add(r["value"])
slot_map: dict[tuple[str, str], str] = {}
for attr, vals in by_attr_vals.items():
    got = assign(client, attr, sorted(vals), MODEL)
    for v, sl in got.items():
        slot_map[(attr, v)] = sl
    print(f"  {attr}: {len(got)}/{len(vals)} values slotted -> {sorted(set(got.values()))[:7]}")
for r in rows:
    r["slot"] = slot_map.get((r["attribute"], r["value"]), "")

# ── 1c. scenes ───────────────────────────────────────────────────────────────
# Ordered by story, not by screen. Detour is a flashback, so the two disagree, and the
# window has to walk the story or it compares the present with the past.
scenes = json.load(open("work/scenes.json"))
def _scene(t):
    for sc in scenes:
        if sc["t_from"] <= t <= sc["t_to"]:
            return sc
    return None
for r in rows:
    sc = _scene(r.get("t", 0.0))
    r["scene"] = sc["n"] if sc else -1
    r["story_order"] = sc["story_order"] if sc else -1

# ── 2. re-search ─────────────────────────────────────────────────────────────
sess = chs.Session()
load(sess, rows, WORK)
data = json.loads(str(sess.query(TRANSITIONS.replace("{work:String}", f"'{WORK}'"), "JSON")))["data"]
json.dump(data, open("work/transitions.json", "w"), indent=1)
cross = [d for d in data if d["source_from"] != d["source_to"]]
across = [d for d in data if d["scene_from"] != d["scene"]]
print(f"  {len(across)} cross-SCENE candidates — the class the prior art cannot reach")
print(f"  {len(data)} transitions ({len(cross)} cross-modal) after resolution")

# ── 3. adjudicate ────────────────────────────────────────────────────────────
# Stratified by attribute, not ranked globally by confidence.
#
# The first version took the top N by confidence and judged 160 transitions of which 100
# were `wearing` and none were injury, hair or prop state — so every documented error in
# the film was excluded from the sample, and the run returned zero errors and looked fine.
# Confidence ranks what the extractor is surest about, which is clothing, which is exactly
# where change is most normal. A global ranking on a skewed population is a filter, and it
# filtered out the entire point.
PER_ATTRIBUTE = 26
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 200
by_attr: dict[str, list] = {}
for d in data:
    if d["source_from"] != d["source_to"]:
        continue                                  # cross-modal is taken whole, below
    by_attr.setdefault(d["attribute"], []).append(d)
visual = []
for attr, items in sorted(by_attr.items()):
    visual.extend(items[:PER_ATTRIBUTE])
batch = cross + visual[: max(0, LIMIT - len(cross))]
from collections import Counter as _C
print("  sample by attribute:", dict(_C(b["attribute"] for b in batch)))
transcript = json.load(open("work/transcript.json"))
print(f"  adjudicating {len(batch)}…")

def run(tr):
    try:
        return adjudicate(client, tr, transcript, MODEL)
    except Exception as e:
        print(f"    failed: {type(e).__name__}", file=sys.stderr)
        return None

out = []
with concurrent.futures.ThreadPoolExecutor(8) as ex:
    for v in ex.map(run, batch):
        if v: out.append(v)

with open("work/verdicts.jsonl", "w") as f:
    for v in out:
        f.write(json.dumps(v.to_dict()) + "\n")

c = Counter(v.verdict for v in out)
print(f"\n  {len(out)} adjudicated: {dict(c)}")
errs = sorted((v for v in out if v.verdict == "error"), key=lambda v: -v.confidence)
print(f"\n  === {len(errs)} flagged as errors ===")
for v in errs[:14]:
    tag = "X-MODAL " if v.cross_modal else ""
    print(f"  {tag}{v.entity[:20]:<22} {v.attribute:<12} {v.t_from:>6.0f}s {v.value_from[:26]:<28}")
    print(f"  {'':<22} {'':<12} {v.t_to:>6.0f}s {v.value_to[:26]:<28} [{v.confidence:.2f}]")
    print(f"      {v.reason[:110]}")
