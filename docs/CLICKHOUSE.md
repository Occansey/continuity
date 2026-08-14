# ClickHouse MCP — the steps

The partner track requires: **"use ClickHouse MCP server connecting to a cluster at
runtime."** Three nouns, all mandatory — the *MCP server*, a *cluster*, at *runtime*.
`chdb` (what we use locally) is a real ClickHouse engine but satisfies none of them. This
is the runbook to satisfy all three. Roughly one hour, and only the first step needs you.

The code is already written: `src/continuity/agent.py` (agent → MCP), `cluster.py`
(loader), and the app switches to the cluster automatically when `CLICKHOUSE_HOST` is set.

---

## 1. Create a cluster — *yours to do* (~10 min)

1. Sign in at **clickhouse.cloud** (free trial, no card).
2. Create a service. Any region; the smallest size is fine — the dataset is a few MB.
3. When it is ready, open **Connect** and copy:
   - host (e.g. `abc123.us-east-1.aws.clickhouse.cloud`)
   - the generated password for the `default` user
4. Put them in your shell:

```bash
export CLICKHOUSE_HOST='<your-host>'
export CLICKHOUSE_USER='default'
export CLICKHOUSE_PASSWORD='<your-password>'
export CLICKHOUSE_SECURE='true'
export CLICKHOUSE_PORT='8443'
```

That is the only step that needs your account. Everything below is scripted.

## 2. Load the assertions into it (~2 min)

```bash
./.venv/bin/python scripts/load_cluster.py
```

Idempotent. It creates the schema, inserts the extracted assertions, and prints the row
count and how many transitions the cluster finds — so a good load is visible, not assumed.

## 3. Run the ClickHouse MCP server against it (~5 min)

The server is `mcp-clickhouse`, launched over stdio and configured entirely by the
`CLICKHOUSE_*` environment already exported:

```bash
uvx mcp-clickhouse            # smoke test: it should start and wait on stdio
```

The agent launches this same command as a subprocess — you do not run it by hand in
normal use. This is just to confirm it starts and connects.

## 4. Drive it with the agent (~5 min)

```bash
GOOGLE_GENAI_USE_VERTEXAI=true GOOGLE_CLOUD_PROJECT=<project> GOOGLE_CLOUD_LOCATION=global \
  ./.venv/bin/python scripts/run_agent.py "find a cross-scene continuity error"
```

`scripts/run_agent.py` builds the ADK agent from `continuity.agent`, which mounts the
ClickHouse MCP server as its toolset. Gemini reasons about *which* contradiction to look
for; the MCP server runs the SQL against the cluster; Gemini reads the rows back. Gemini
never touches the database directly and never computes a number — which is both the
project's discipline and, now, the shape the requirement demands.

## 5. Point the deployed app at the cluster (~10 min)

```bash
gcloud run services update continuity --region us-central1 \
  --update-env-vars \
"CLICKHOUSE_HOST=$CLICKHOUSE_HOST,CLICKHOUSE_USER=$CLICKHOUSE_USER,CLICKHOUSE_PASSWORD=$CLICKHOUSE_PASSWORD,CLICKHOUSE_SECURE=true"
```

`/api/health` then reports `backend: clickhouse-cluster`, and `/api/search` runs the query
on the cluster at request time. That is the runtime call the rules ask to see.

Set the secrets through Cloud Run's env, not the repo — the password is a credential and
belongs nowhere in git.

---

## What satisfies each word of the requirement

| Requirement word | Satisfied by |
|---|---|
| ClickHouse **MCP server** | `mcp-clickhouse`, mounted as the agent's toolset in `agent.py` |
| connecting to a **cluster** | ClickHouse Cloud, loaded by `load_cluster.py` |
| at **runtime** | the agent calls MCP tools per request; `/api/search` queries the cluster live |

`docs/PARTNER.md` will point at the exact call sites once the cluster is live, and
`scripts/preflight.sh` fails if any of them stops existing.
