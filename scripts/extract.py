"""Run the extractor over the frames and write assertions as JSONL."""
import concurrent.futures, json, os, sys
from pathlib import Path
sys.path.insert(0, "src")
from google import genai
from continuity.extract import extract_batch

MODEL = os.environ.get("CONTINUITY_MODEL", "gemini-3.6-flash")
BATCH = 4
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0

jobs = {n: t for n, t in json.load(open("work/jobs.json"))}
frames = sorted((n, jobs[n], Path(f"work/frames/s{n:04d}.jpg"))
                for n in jobs if Path(f"work/frames/s{n:04d}.jpg").exists())
if LIMIT:
    frames = frames[:LIMIT]
batches = [frames[i:i+BATCH] for i in range(0, len(frames), BATCH)]

client = genai.Client(vertexai=True, location="global")
out, failed = [], 0
def run(b):
    try:
        return extract_batch(client, b, MODEL)
    except Exception as e:
        print(f"    batch {b[0][0]} failed: {type(e).__name__}", file=sys.stderr)
        return []

with concurrent.futures.ThreadPoolExecutor(6) as ex:
    for res in ex.map(run, batches):
        if not res: failed += 1
        out.extend(res)

with open("work/assertions.jsonl", "w") as f:
    for a in out:
        f.write(json.dumps(a.to_dict()) + "\n")
print(f"  {len(out)} assertions from {len(frames)} frames ({failed}/{len(batches)} batches empty)")
