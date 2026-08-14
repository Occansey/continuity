"""Load the assertions into ClickHouse and find transitions."""
import json, sys
sys.path.insert(0, "src")
import chdb.session as chs
from continuity.store import TRANSITIONS, load, read_jsonl

sess = chs.Session()
rows = read_jsonl("work/assertions.jsonl", "work/assertions_dialogue.jsonl")
n = load(sess, rows, "detour-1945")
print(f"  {n} assertions loaded")

for label, q in [
    ("by source",    "SELECT source, count() FROM assertions GROUP BY source ORDER BY 2 DESC"),
    ("by attribute", "SELECT attribute, count() c, uniq(entity) e FROM assertions GROUP BY attribute ORDER BY c DESC LIMIT 8"),
    ("top entities", "SELECT entity, count() c FROM assertions GROUP BY entity ORDER BY c DESC LIMIT 8"),
]:
    print(f"\n  --- {label} ---")
    print("   " + str(sess.query(q, "PrettyCompact")).replace("\n", "\n   ").strip())

res = sess.query(TRANSITIONS.replace("{work:String}", "'detour-1945'"), "JSON")
data = json.loads(str(res))["data"]
json.dump(data, open("work/transitions.json", "w"), indent=1)
print(f"\n  {len(data)} transitions found")

cross = [d for d in data if d["source_from"] != d["source_to"]]
print(f"  {len(cross)} of them cross between dialogue and image")
