# Hard requirements

From the rules page, 14 Aug 2026. These are pass/fail, not judging criteria — a submission
that misses one is not scored badly, it is not scored.

---

## The technology mandate

> "powered by Gemini and Google Cloud Agent Builder"

Google Cloud packages must be **"imported and actually called (a library/backend entry
point, or loaded agent/flow/MCP config), not just named in README."**

Accepted SDKs: `google-adk`, `google-genai`, `google-generativeai`, `google-cloud-aiplatform`.

**Where we stand:** `google-genai` is imported and called, so the letter is satisfied. The
phrase *Agent Builder* is still in the requirement and we are not using it. `google-adk` is
on the accepted list and is what we used on the previous project. Resolve before P2.

## The ClickHouse track mandate — the one that bites

> **"Must use ClickHouse MCP server connecting to a cluster at runtime"**

Not ClickHouse. Not ClickHouse-compatible. **The MCP server, against a cluster, at
runtime.**

**Where we stand: non-compliant.** P0 used `chdb`, ClickHouse embedded in the process.
That is genuinely ClickHouse and it was the right call for a one-day experiment — no
server, no credentials, no waiting. It is not a cluster and there is no MCP server in
front of it.

**What this changes:** a ClickHouse Cloud cluster, the ClickHouse MCP server between the
agent and it, and the agent reaching the data *through* the MCP tools rather than through
a Python client. That is an architectural requirement, not a deployment detail: the agent
must call the tools.

`chdb` stays for local development and for the benchmark baseline, where being in-process
is an advantage.

## Only Google's AI

> "No other AI models, agent frameworks, or AI APIs are permitted, regardless of vendor."

Gemini for everything: vision, transcription, adjudication, and any embeddings. No
third-party embedding model, no Whisper, no other agent framework.

**Where we stand:** compliant. Transcription is Gemini, extraction is Gemini, adjudication
is Gemini. Worth re-checking before every dependency we add.

## Eligibility and provenance

- **Team:** four people maximum.
- **Newly created during the contest period**, which began 27 July. The repository began
  14 August, so the code is new. The *architecture* is carried over from a previous
  project of ours; that is reuse of ideas and of our own prior work, and the code here is
  written for this. Worth stating plainly in the README rather than leaving to inference.

## The date, which does not agree with itself

| Source | Says |
|---|---|
| Devpost front page | **Sep 9, 2026 @ 2:00pm PDT** |
| Devpost rules page | Contest period **July 27 – September 7, 2026** |
| Trade press | Entries close **Sep 7, 10:00pm GMT+1** |

Two of three say the 7th. The time on the front page (2pm PDT) is the same instant as
10pm GMT+1, so the disagreement is only the date, which makes a transcription error
likelier than two different deadlines.

**We plan to the 7th.** Being early costs two days of polish; being late costs
everything. Confirm with the organisers and record the answer here.
