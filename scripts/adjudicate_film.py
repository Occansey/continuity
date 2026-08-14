"""Adjudicate a film's transitions, stratified by attribute so no class is starved.

Ranking globally by confidence once hid every documented error behind 100 wearing
transitions. Stratifying per attribute is the fix, kept here rather than rediscovered.
"""
import sys, json, os, concurrent.futures
from collections import Counter
from pathlib import Path
sys.path.insert(0, "src")
import chdb.session as chs
from google import genai
from continuity.store import TRANSITIONS, load, read_jsonl
from continuity.adjudicate import adjudicate

WORK = sys.argv[1]
PER = int(sys.argv[2]) if len(sys.argv) > 2 else 24
out = Path(f"work/{WORK}")

sess = chs.Session()
load(sess, read_jsonl(out / "assertions_enriched.jsonl"), WORK)
data = json.loads(str(sess.query(TRANSITIONS.replace("{work:String}", f"'{WORK}'"), "JSON")))["data"]
cross = [d for d in data if d["scene_from"] != d["scene"]]

by_attr = {}
for d in cross:
    by_attr.setdefault(d["attribute"], []).append(d)
batch = []
for attr, items in sorted(by_attr.items()):
    batch.extend(items[:PER])
print(f"  {WORK}: {len(data)} transitions, {len(cross)} cross-scene, adjudicating {len(batch)}")
print(f"  by attribute: {dict(Counter(b['attribute'] for b in batch))}")

client = genai.Client(vertexai=True, location="global")
transcript = json.load(open(out / "transcript.json"))
def judge(tr):
    try: return adjudicate(client, tr, transcript, "gemini-3.6-flash", frames_dir=out / "frames")
    except Exception: return None
res = [v for v in concurrent.futures.ThreadPoolExecutor(6).map(judge, batch) if v]
with open(out / "verdicts.jsonl", "w") as f:
    for v in res: f.write(json.dumps(v.to_dict()) + "\n")
print(f"\n  adjudicated {len(res)}: {dict(Counter(v.verdict for v in res))}")
errs = sorted((v for v in res if v.verdict == "error"), key=lambda v: -v.confidence)
print(f"\n  === {len(errs)} flagged as errors ===")
for v in errs:
    print(f"   {v.entity[:18]:<20} {v.attribute:<11} {v.value_from[:24]:<26} -> {v.value_to[:24]}")
    print(f"      {v.reason[:104]}")
