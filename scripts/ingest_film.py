"""Ingest one film into the shared Continuity corpus, end to end.

    python scripts/ingest_film.py <work-id> <path-to.mp4>

Runs the full pipeline (continuity.pipeline.run) and loads the result into ClickHouse —
the embedded engine by default, or the cluster when CLICKHOUSE_HOST is set, so the same
command fills the local corpus or the deployed one.
"""
import os, sys
sys.path.insert(0, "src")
from continuity.pipeline import run
from continuity.store import TRANSITIONS, load, read_jsonl

work = sys.argv[1]
film = sys.argv[2]
print(f"  === ingesting {work} ===")
rep = run(work, film)
print(f"  pipeline: {rep}")

rows = read_jsonl(f"work/{work}/assertions_enriched.jsonl")
if os.environ.get("CLICKHOUSE_HOST"):
    from continuity.cluster import client, create_schema, insert
    c = client(); create_schema(c)
    if c.command(f"SELECT count() FROM assertions WHERE work='{work}'") in (0, "0"):
        insert(c, rows, work)
    n = c.command(f"SELECT count() FROM assertions WHERE work='{work}'")
    t = len(c.query(TRANSITIONS.replace("{work:String}", f"'{work}'")).result_rows)
    print(f"  cluster: {n} rows, {t} transitions  (corpus now spans multiple films)")
else:
    import chdb.session as chs, json
    sess = chs.Session()
    load(sess, rows, work)
    t = json.loads(str(sess.query(TRANSITIONS.replace("{work:String}", f"'{work}'"), "JSON")))["data"]
    print(f"  chdb: {len(rows)} rows, {len(t)} transitions")
