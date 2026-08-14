"""Direct ClickHouse Cloud client, for loading the store and for the app's query path.

This is distinct from the MCP path in `agent.py`. The MCP server is how the *agent* reaches
the data — that is the partner-track requirement. This module is how we *load* the cluster
and how the web app runs the fixed contradiction query, neither of which is agent work.
Both talk to the same cluster; only the access path differs.
"""
from __future__ import annotations

import os

from continuity.store import SCHEMA, TRANSITIONS


def client():
    import clickhouse_connect
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        user=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        port=int(os.environ.get("CLICKHOUSE_PORT", "8443")),
        secure=os.environ.get("CLICKHOUSE_SECURE", "true") == "true",
    )


def create_schema(c) -> None:
    c.command(SCHEMA)


def insert(c, rows: list[dict], work: str) -> int:
    cols = ["work", "shot", "t", "entity", "entity_kind", "attribute", "value",
            "confidence", "source", "quote", "slot", "scene", "story_order"]
    data = [[work, int(r.get("shot", -1)), float(r.get("t", 0.0)), r.get("entity", ""),
             r.get("entity_kind", ""), r.get("attribute", ""), r.get("value", ""),
             float(r.get("confidence", 0.5)), r.get("source", "image"), r.get("quote", ""),
             r.get("slot", ""), int(r.get("scene", -1)), int(r.get("story_order", -1))]
            for r in rows]
    c.insert("assertions", data, column_names=cols)
    return len(data)


def query_transitions(rows: list[dict], work: str) -> list[dict]:
    """Used by the web app when a cluster is configured. Idempotent load, then the query."""
    c = client()
    create_schema(c)
    if c.command(f"SELECT count() FROM assertions WHERE work = '{work}'") in (0, "0"):
        insert(c, rows, work)
    res = c.query(TRANSITIONS.replace("{work:String}", f"'{work}'"))
    return [dict(zip(res.column_names, row)) for row in res.result_rows]
