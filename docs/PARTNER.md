# ClickHouse — where it is actually called

The rule: *"imported and actually called (a library/backend entry point, or loaded
agent/flow/MCP config), not just named in README"*, and for this track specifically
*"ClickHouse MCP server connecting to a cluster at runtime."*

Verified live on 14 Aug 2026 against a ClickHouse Cloud cluster
(`n686…….eu-west-1.aws.clickhouse.cloud`, service id redacted).

## The MCP path — the agent, at runtime (the track requirement)

| Call site | What it does |
|---|---|
| `src/continuity/agent.py:clickhouse_toolset` | Mounts `mcp-clickhouse` as the ADK agent's toolset over stdio, configured by the CLICKHOUSE_* env, filtered to read-only tools |
| `src/continuity/agent.py:build_agent` | The Gemini ADK `LlmAgent` whose only data access is those MCP tools |
| `scripts/run_agent.py` | Drives it; proven live — Gemini wrote SQL, called the MCP `run_query` tool, the cluster answered, Gemini read 1,119 rows and two cross-scene transitions back |

That is the whole requirement in one path: **ClickHouse MCP server → cluster → at runtime**,
with the agent never touching the database directly.

## The direct path — the hosted app

| Call site | What it does |
|---|---|
| `src/continuity/cluster.py:query_transitions` | The deployed app's `/api/search`, runs the contradiction query on the cluster per request |
| `scripts/load_cluster.py` | Loaded 1,119 assertions into the cluster |

Live proof:

```
$ curl https://continuity-468826425509.us-central1.run.app/api/health
{"ok":true,"backend":"clickhouse-cluster","film":"detour-1945"}
$ curl https://continuity-468826425509.us-central1.run.app/api/search
{"backend":"cluster","transitions":346}
```

## The MCP tool name

The server exposes `run_query`, not the README's `run_select_query` (older version). Found
by listing tools against the running server, not by trusting the docs — the tool_filter in
`agent.py` matches what the server actually offers.
