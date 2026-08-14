# Intel

Gathered 14 Aug 2026, before the idea was fixed. Sources at the bottom; every claim here
traces to one.

---

## 1. What ClickHouse people reward — with a caveat I got wrong once

**Correction.** An earlier version of this file said "the ClickHouse *track* weights use
of ClickHouse at 25%". That is not true and I should not have written it. Agentic Cinema
publishes four criteria for every track — Technological Implementation, Design, Potential
Impact, Quality of the Idea — and no per-track weighting.

The weights below are from **ClickHouse's own separate hackathon** with Trigger.dev. They
are evidence about what ClickHouse people value when they judge, which is worth having,
and they are not the rubric here.

| Weight | Criterion |
|---|---|
| **25%** | use of ClickHouse & partner |
| 20% | problem fit |
| 20% | technical implementation |
| 20% | innovation |
| 10% | scalability & impact |
| 5% | presentation |

Their in-person Click-a-thon write-up says what stood out: **"use cases impossible on
other databases"**, shown with **"benchmarking and before/after demonstrations"**.

Read together, the track's bar is not *did you store something in ClickHouse*. It is
**did you do something that only works because of it, and did you show the comparison**.
Alexey Milovidov, who wrote the database, judges these.

**Consequence, stated correctly:** we are judged on four criteria with no published
weighting, by judges who include partner people. A benchmark is not scored directly. It
is evidence for *Technological Implementation* and insurance against a partner judge
concluding the database was decorative.

## 2. What wins agent hackathons generally

From the 2026 crop that has actually been judged, the winners are unglamorous and
operational rather than generative:

- **Gitdefender** (Google Cloud grand prize) — sits inside code review, finds security
  issues, *writes the fix and opens the review*. It acts.
- **GraphDev** (Anthropic grand prize) — maps how a system changes over time.
- **LORE** — eight agents behind a router, and the write-up leads with **43 tests**.

Two patterns worth stealing: the winners **act inside an existing workflow** rather than
producing an artefact beside it, and at least one led with its test count, which suggests
judges reward visible rigour rather than being bored by it.

## 3. The real ClickHouse workload in media

Not frame-level QC. **Live streaming playback telemetry**, and it is not a hypothetical:

- **Sony LIV** ingests tens of millions of video streaming events into ClickHouse Cloud,
  and their operations team uses it to "monitor, alert and troubleshoot QoS and QoE of
  their customers in real time".
- **Mux** uses ClickHouse as a real-time stream processing engine behind Mux Data, which
  "monitors some of the world's largest livestream events in real time".
- **Vimeo** powers video analytics on it at scale.

This is the canonical media & entertainment ClickHouse deployment. Building on it means
the workload is real before we touch it.

## 4. Where the pain actually is

Live streaming operations, during the event:

- Rebuffering spikes trace to a **misconfigured CDN edge, a saturated origin link, or a
  surge overwhelming one PoP** — plus an over-aggressive bitrate ladder, poor cache hit
  ratio, oversized segments, or device-specific decode limits.
- Diagnosis means finding the cluster: **"if rebuffering clusters by CDN, region or
  device model, it's yours to fix rather than the viewer's."**
- And the industry admits it is bad at this: **27% report ongoing difficulty with
  root-cause identification**, with teams "reacting to visible symptoms instead of
  resolving underlying causes, extending incident timelines".

**The gap in one line:** dashboards tell you *that* quality dropped. Working out *what
explains it* is a combinatorial search across CDN × region × ISP × device × player
version × ladder rung, done by a human, by intuition, under time pressure, during a live
event that will not pause.

## 5. What this rules out

- **Anything generative.** The crowd is there, and a judge will have seen forty trailer
  cutters. Also nothing in §2 suggests generation wins.
- **A read-only dashboard or a chat-with-your-data agent.** §2 says winners act.
- **Anything where ClickHouse could be swapped for Postgres without noticing.** §1 says
  that is 25% of the score, gone.

---

## Sources

- ClickHouse × Trigger.dev AI Hackathon 2026 — https://triggerdev.clickhouse.com/
- Click-a-thon 2026 write-up — https://clickhouse.com/blog/click-a-thon-2026
- ClickHouse at the NYC AI Agents Hackathon — https://clickhouse.com/blog/nyc-ai-agents-hackathon
- Vimeo video analytics on ClickHouse — https://clickhouse.com/blog/behind-the-scenes-how-clickhouse-helps-vimeo-power-video-analytics-at-scale
- Mux as a real-time stream processing engine — https://www.mux.com/blog/how-we-use-clickhouse-as-a-real-time-stream-processing-engine
- GitLab AI Hackathon 2026 winners — https://about.gitlab.com/blog/gitlab-ai-hackathon-2026-meet-the-winners/
- Bitmovin, live streaming observability — https://bitmovin.com/blog/live-streaming-observability/
- Fastly, challenges of online live streaming — https://www.fastly.com/blog/navigating-challenges-online-live-streaming
- FastPix, debugging with CDN logs — https://fastpix.com/blog/using-cdn-logs-to-debug-video-streaming-issues-a-simple-guide
- Agentic Cinema rules — https://agentic-cinema.devpost.com/
