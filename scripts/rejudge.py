"""Re-adjudicate the exact same candidates, so the only variable is the prompt."""
import concurrent.futures, json, os, sys
from collections import Counter
sys.path.insert(0, "src")
from google import genai
from continuity.adjudicate import adjudicate

MODEL = os.environ.get("CONTINUITY_MODEL", "gemini-3.6-flash")
prev = [json.loads(l) for l in open("work/verdicts.jsonl")]
T = json.load(open("work/transitions.json"))
key = lambda x: (x["entity"], x["attribute"], round(x["t_from"], 1))
want = {key(v) for v in prev}
batch = [t for t in T if key(t) in want]
print(f"  re-judging {len(batch)} of {len(prev)} previous candidates")

transcript = json.load(open("work/transcript.json"))
client = genai.Client(vertexai=True, location="global")
def run(tr):
    try: return adjudicate(client, tr, transcript, MODEL)
    except Exception: return None

out = [v for v in concurrent.futures.ThreadPoolExecutor(8).map(run, batch) if v]
with open("work/verdicts2.jsonl","w") as f:
    for v in out: f.write(json.dumps(v.to_dict())+"\n")

before = Counter(v["verdict"] for v in prev)
after  = Counter(v.verdict for v in out)
print(f"\n  before: {dict(before)}")
print(f"  after:  {dict(after)}")

pm = {key(v): v["verdict"] for v in prev}
moved = [(v, pm[key(v.to_dict())]) for v in out if key(v.to_dict()) in pm and pm[key(v.to_dict())] != v.verdict]
print(f"\n  {len(moved)} changed verdict")
for v, was in moved[:12]:
    print(f"   {was:>14} -> {v.verdict:<14} {v.entity[:18]:<20} {v.attribute:<11} {v.t_from:>6.0f}s")
    print(f"       {v.reason[:104]}")
