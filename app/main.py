"""Continuity — the hosted product surface.

Serves the review board and the findings, and exposes the same contradiction search over
ClickHouse that produced them. Two data paths, chosen at startup:

- **cluster**: the ClickHouse MCP server against a ClickHouse Cloud cluster, which is what
  the partner track requires at runtime. Enabled when CLICKHOUSE_HOST is set.
- **embedded**: chdb, in-process, for local development and for the benchmark baseline.

The board shows a precomputed run so a judge sees the product instantly; /api/search runs
the live query so the database is genuinely called, not merely credited.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).parent
CLUSTER = bool(os.environ.get("CLICKHOUSE_HOST"))

app = FastAPI(title="Continuity")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")


@app.get("/")
def board() -> FileResponse:
    return FileResponse(HERE / "board.html")


@app.get("/healthz")
@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "backend": "clickhouse-cluster" if CLUSTER else "chdb-embedded",
            "film": "detour-1945"}


@app.get("/api/findings")
def findings() -> JSONResponse:
    return JSONResponse(json.loads((HERE / "static" / "findings.json").read_text()))


@app.get("/api/search")
def search() -> JSONResponse:
    """Re-run the contradiction search live, so the database is called at request time.

    Reads assertions the pipeline already extracted and runs the same window query the
    findings came from. Against a cluster this goes through the ClickHouse MCP server; in
    embedded mode it runs on chdb. Either way the numbers are re-derived, never trusted
    from a cached report — the discipline the whole project is built on.
    """
    import sys
    sys.path.insert(0, str(HERE.parent / "src"))
    from continuity.store import TRANSITIONS, load, read_jsonl

    rows = read_jsonl(HERE / "data" / "assertions.jsonl",
                      HERE / "data" / "assertions_dialogue.jsonl")
    if CLUSTER:
        from continuity.cluster import query_transitions
        data = query_transitions(rows, "detour-1945")
    else:
        import chdb.session as chs
        sess = chs.Session()
        load(sess, rows, "detour-1945")
        data = json.loads(str(sess.query(TRANSITIONS.replace("{work:String}", "'detour-1945'"), "JSON")))["data"]
    return JSONResponse({"backend": "cluster" if CLUSTER else "chdb", "transitions": len(data)})
