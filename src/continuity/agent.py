"""The agent, assembled the way the two mandates require.

Two hard requirements meet here, and this file is where they are satisfied together:

- *"powered by Gemini and Google Cloud Agent Builder"* — this is an ADK agent
  (`google.adk`), Gemini reasoning over tools.
- *"Must use ClickHouse MCP server connecting to a cluster at runtime"* — the agent's
  only route to the data is the ClickHouse MCP server (`mcp-clickhouse`), pointed at a
  ClickHouse Cloud cluster. The agent does not hold a database client; it calls the MCP
  server's tools, and the MCP server talks to the cluster.

That separation is the point of the requirement, not an accident of it. The model reasons
about *which contradiction to look for*; the MCP server runs the SQL against the cluster;
the model reads the rows back. Gemini never computes a number and never touches the
database directly, which is the same discipline the whole project is built on, now
enforced by the topology rather than by good intentions.

## Running it

The MCP server is launched as a subprocess over stdio, configured entirely by
environment — `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`,
`CLICKHOUSE_SECURE=true`. See `docs/CLICKHOUSE.md` for the cluster setup and
`scripts/load_cluster.py` for getting the assertions into it. Without those variables this
module refuses to build an agent rather than silently falling back to something that would
not satisfy the requirement — a fallback here would be a fallback on the one thing that is
pass/fail.
"""

from __future__ import annotations

import os

INSTRUCTION = """\
You are Continuity, a script supervisor for film. Your job is to find places where the
world of a story contradicts itself across scenes — a wound that changes which hand, an
object described one way and shown another, a garment that changes with no time passing.

You have tools that query a ClickHouse table called `assertions`: one row per claim made
about the world by a shot or a line of dialogue, with columns entity, attribute, slot,
value, source, scene, story_order, t, confidence.

Work like this:
1. Use the schema and sampling tools to understand what is in the table.
2. Find transitions: for an entity and attribute (and slot, where present), consecutive
   values in story order that differ. Prefer transitions that cross a scene boundary —
   those are the ones a pixel-based tool cannot catch and the ones worth a human's time.
3. Never compute a count yourself. Every number comes from a query you ran.
4. Report each candidate with the two timecodes, the two values, and the scene numbers,
   so a human can look at both frames.

You decide which query to run. The database decides what is true.
"""


def clickhouse_toolset():
    """The ClickHouse MCP server as an ADK toolset, over stdio.

    Launches `mcp-clickhouse` as a subprocess, configured by the CLICKHOUSE_* environment.
    The agent gets exactly the tools that server exposes — list databases and tables,
    describe schema, run a read-only SELECT — and nothing else.
    """
    import shutil
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
    from mcp import StdioServerParameters

    required = ("CLICKHOUSE_HOST", "CLICKHOUSE_USER", "CLICKHOUSE_PASSWORD")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            f"ClickHouse MCP needs {', '.join(missing)}. The cluster is not optional here — "
            "it is the partner-track requirement. See docs/CLICKHOUSE.md."
        )

    server_env = {
        "CLICKHOUSE_HOST": os.environ["CLICKHOUSE_HOST"],
        "CLICKHOUSE_USER": os.environ["CLICKHOUSE_USER"],
        "CLICKHOUSE_PASSWORD": os.environ["CLICKHOUSE_PASSWORD"],
        "CLICKHOUSE_PORT": os.environ.get("CLICKHOUSE_PORT", "8443"),
        "CLICKHOUSE_SECURE": os.environ.get("CLICKHOUSE_SECURE", "true"),
    }
    # Prefer a resolvable mcp-clickhouse on PATH (installed in the venv); fall back to the
    # uvx form the docs describe. The tool the server exposes is `run_query`, confirmed
    # against a live cluster — the README's `run_select_query` is from an older version.
    bin_ = shutil.which("mcp-clickhouse")
    server = (StdioServerParameters(command=bin_, args=[], env=server_env) if bin_
              else StdioServerParameters(command="uvx", args=["mcp-clickhouse"], env=server_env))
    return McpToolset(
        connection_params=StdioConnectionParams(server_params=server),
        # Read-only. The agent inspects and queries; it has no business writing to the
        # store it is auditing, and the tool filter makes that structural rather than
        # trusted.
        tool_filter=["list_databases", "list_tables", "run_query"],
    )


def build_agent(model: str = "gemini-3.6-flash"):
    """The Continuity agent: Gemini reasoning over the ClickHouse MCP tools."""
    from google.adk.agents import LlmAgent

    return LlmAgent(
        name="continuity",
        model=model,
        instruction=INSTRUCTION,
        tools=[clickhouse_toolset()],
    )
