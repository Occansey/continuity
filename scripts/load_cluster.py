"""Load the extracted assertions into a ClickHouse Cloud cluster, then verify the search.

    CLICKHOUSE_HOST=... CLICKHOUSE_USER=... CLICKHOUSE_PASSWORD=... \
      python scripts/load_cluster.py

Idempotent: safe to re-run. Prints a row count and the number of transitions the cluster
finds, so a successful load is visible rather than assumed.
"""
import sys
sys.path.insert(0, "src")
from continuity.cluster import client, create_schema, insert
from continuity.store import TRANSITIONS, read_jsonl

WORK = "detour-1945"
c = client()
create_schema(c)
existing = c.command(f"SELECT count() FROM assertions WHERE work = '{WORK}'")
if existing in (0, "0"):
    rows = read_jsonl("work/assertions.jsonl", "work/assertions_dialogue.jsonl")
    # scene/slot/story_order are added at query time in scripts; for the cluster we load
    # the enriched rows the app already produced.
    import json, os
    enriched = "work/assertions_enriched.jsonl"
    if os.path.exists(enriched):
        rows = read_jsonl(enriched)
    print(f"  inserting {insert(c, rows, WORK)} rows")
else:
    print(f"  {existing} rows already present, skipping insert")

res = c.query(TRANSITIONS.replace("{work:String}", f"'{WORK}'"))
print(f"  cluster finds {len(res.result_rows)} transitions")
print("  ClickHouse Cloud is loaded and queryable. Point the app and the MCP server at it.")
