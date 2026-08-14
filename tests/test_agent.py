"""The guardrail on the agent, not the agent's reasoning. Two things must be structurally
true and this file pins both: the agent refuses to build without a cluster to talk to, because
the ClickHouse MCP path is the partner-track requirement and a silent fallback would fail the
one pass/fail thing; and the tools it is given are read-only, because the agent has no business
writing to the store it audits. We assert the McpToolset object and its tool_filter, never a
printed claim about them, and we never launch the MCP server.
"""
import shutil

import pytest
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

import continuity.agent as agent_mod
from continuity.agent import build_agent

CREDS = ("CLICKHOUSE_HOST", "CLICKHOUSE_USER", "CLICKHOUSE_PASSWORD")

# Any tool that could change the store. If the filter ever lets one of these through, the
# read-only guarantee is gone regardless of what the docstring says.
WRITE_TOOLS = {
    "run_write_query", "run_select_query_write", "insert", "create_table", "drop_table",
    "create_database", "drop_database", "alter_table", "execute", "command",
}


def _filter_of(toolset):
    return getattr(toolset, "_tool_filter", getattr(toolset, "tool_filter", None))


def test_build_agent_refuses_without_a_cluster(monkeypatch):
    """No host, user or password means no cluster, and the agent must raise rather than fall
    back to something that would not satisfy the requirement."""
    for k in CREDS:
        monkeypatch.delenv(k, raising=False)

    with pytest.raises(RuntimeError) as exc:
        build_agent()
    assert "cluster" in str(exc.value).lower()


def test_the_error_names_the_missing_credentials(monkeypatch):
    """A fail-safe that does not say what it wants is indistinguishable from a bug. The refusal
    must name the variable that was absent."""
    monkeypatch.setenv("CLICKHOUSE_HOST", "h")
    monkeypatch.setenv("CLICKHOUSE_USER", "u")
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)

    with pytest.raises(RuntimeError) as exc:
        build_agent()
    assert "CLICKHOUSE_PASSWORD" in str(exc.value)


def test_build_agent_wires_exactly_one_toolset(monkeypatch):
    for k in CREDS:
        monkeypatch.setenv(k, "x")
    # Pin the launcher path so construction does not depend on what is installed, and so the
    # server is never actually spawned by this test.
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcp-clickhouse")

    agent = build_agent()
    assert len(agent.tools) == 1
    assert isinstance(agent.tools[0], McpToolset)


def test_the_toolset_is_read_only(monkeypatch):
    """run_query must be reachable and every write tool must be excluded. The filter is the
    structural guarantee; assert on it, not on the comment above it."""
    for k in CREDS:
        monkeypatch.setenv(k, "x")
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcp-clickhouse")

    toolset = build_agent().tools[0]
    allowed = set(_filter_of(toolset))
    assert "run_query" in allowed
    assert allowed == {"list_databases", "list_tables", "run_query"}
    assert allowed.isdisjoint(WRITE_TOOLS)


def test_clickhouse_env_passes_through_to_the_server(monkeypatch):
    """The MCP server is configured entirely by environment. If the creds did not reach the
    subprocess params, the agent would build but never authenticate — a wiring gap the unit
    test alone would miss."""
    monkeypatch.setenv("CLICKHOUSE_HOST", "cluster.example")
    monkeypatch.setenv("CLICKHOUSE_USER", "reader")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "secret")
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/mcp-clickhouse")

    toolset = agent_mod.clickhouse_toolset()
    server_params = toolset._connection_params.server_params
    assert server_params.env["CLICKHOUSE_HOST"] == "cluster.example"
    assert server_params.env["CLICKHOUSE_PASSWORD"] == "secret"
    assert server_params.command == "/usr/bin/mcp-clickhouse"
