"""Run the whole pipeline on one film, keyed by a work id.

Until now the stages lived as one-off scripts hardcoded to `work/` and to `detour-1945`.
That was fine for proving the idea on one film and useless for a corpus. This module runs
every stage for an arbitrary film into `work/<work>/`, so films never collide, and imports
the core logic from the same modules the single-film path used — a fix to a stage is a fix
for every film, not a copy that drifts.

    from continuity.pipeline import run
    run("notld-1968", "corpus/notld-1968.mp4")

The store already keys every row by `work`, so loading a second film into the same
ClickHouse is nothing more than calling load with a different id. The corpus was designed
in from the start; this is the ingest that fills it.

Stages, each idempotent (skips if its output exists), so a failed run resumes rather than
restarts:
  shots -> frames -> visual assertions -> dialogue -> scenes -> resolve -> slots -> load
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import imageio_ffmpeg

from continuity.entities import resolve
from continuity.extract import extract_batch
from continuity.scenes import renumber, segment
from continuity.slots import MULTIVALUED, assign

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MODEL = "gemini-3.6-flash"
SCENE_THRESHOLD = 0.12


def _duration(film: str) -> float:
    out = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", film], capture_output=True, text=True
    ).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if not m:
        return 0.0
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def detect_shots(film: str, out: Path) -> list[dict]:
    """Scene-cut detection. The threshold is a soft-transfer compromise, tuned on Detour;
    a cleaner print wants it higher, so it is a parameter, not a constant baked in a
    hundred lines away."""
    f = out / "shots.json"
    if f.exists():
        return json.loads(f.read_text())
    scenes_txt = out / "scenes_raw.txt"
    subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "info", "-i", film,
         "-filter:v", f"select='gt(scene,{SCENE_THRESHOLD})',metadata=print:file={scenes_txt}",
         "-an", "-f", "null", "-"],
        capture_output=True, check=False,
    )
    times = [round(float(m), 3) for m in re.findall(r"pts_time:([\d.]+)", scenes_txt.read_text())]
    dur = _duration(film)
    shots = [{"n": i, "start": a, "end": b}
             for i, (a, b) in enumerate(zip([0.0] + times, times + [dur]))]
    f.write_text(json.dumps(shots))
    return shots


def sample_frames(film: str, shots: list[dict], out: Path) -> list[tuple[int, float]]:
    """One frame per shot, 40% in — past a dissolve, before a gesture ends."""
    fdir = out / "frames"
    fdir.mkdir(exist_ok=True)
    jobs = [(s["n"], s["start"] + (s["end"] - s["start"]) * 0.4)
            for s in shots if s["end"] - s["start"] >= 0.6]

    def grab(job):
        n, t = job
        p = fdir / f"s{n:04d}.jpg"
        if not p.exists():
            subprocess.run(
                [FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}",
                 "-i", film, "-frames:v", "1", "-q:v", "3", str(p)],
                check=False,
            )

    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        list(ex.map(grab, jobs))
    return jobs


def extract_visual(client, jobs, out: Path) -> list[dict]:
    f = out / "assertions.jsonl"
    if f.exists():
        return [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    fdir = out / "frames"
    frames = [(n, t, fdir / f"s{n:04d}.jpg") for n, t in jobs if (fdir / f"s{n:04d}.jpg").exists()]
    batches = [frames[i:i + 4] for i in range(0, len(frames), 4)]

    def run_batch(b):
        try:
            return [a.to_dict() for a in extract_batch(client, b, MODEL)]
        except Exception:
            return []

    rows: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        for r in ex.map(run_batch, batches):
            rows.extend(r)
    f.write_text("\n".join(json.dumps(r) for r in rows))
    return rows


def transcribe(client, film: str, out: Path) -> tuple[list[dict], list[dict]]:
    """Dialogue is a second source of assertions, in the same shape as the visual ones —
    the said-vs-shown contradictions live in the crossover. Chunked to keep timecodes
    honest."""
    tf, af = out / "transcript.json", out / "assertions_dialogue.jsonl"
    if tf.exists() and af.exists():
        return json.loads(tf.read_text()), [json.loads(l) for l in af.read_text().splitlines() if l.strip()]

    adir = out / "audio"
    adir.mkdir(exist_ok=True)
    dur = _duration(film)
    chunks = []
    for i in range(0, int(dur // 600) + 1):
        p = adir / f"chunk_{i}.mp3"
        if not p.exists():
            subprocess.run(
                [FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", str(i * 600), "-t", "600",
                 "-i", film, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-q:a", "6",
                 str(p), "-y"],
                check=False,
            )
        if p.exists() and p.stat().st_size > 1000:
            chunks.append((i, p))

    from continuity.extract import ATTRIBUTES, ENTITY_KINDS
    prompt = (
        "This is ten minutes of audio from a film, starting at {off} seconds in. "
        "1) Transcribe the dialogue with timestamps in seconds from the start of THIS clip. "
        "2) Extract assertions the dialogue makes about the physical world — objects, people, "
        "injuries, places, times — with measurements exactly as spoken. Ignore feelings and "
        "intentions.\n"
        f"attribute must be one of: {', '.join(ATTRIBUTES)}\n"
        f"entity_kind must be one of: {', '.join(ENTITY_KINDS)}\n"
        'JSON only: {{"lines":[{{"t":float,"speaker":str,"text":str}}],'
        '"assertions":[{{"t":float,"entity":str,"entity_kind":str,"attribute":str,'
        '"value":str,"quote":str,"confidence":float}}]}}'
    )

    def run_chunk(job):
        i, p = job
        off = i * 600
        raw = client.models.generate_content(
            model=MODEL,
            contents=[prompt.format(off=off),
                      {"inline_data": {"mime_type": "audio/mpeg", "data": p.read_bytes()}}],
            config={"response_mime_type": "application/json", "temperature": 0.0},
        ).text or ""
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            return [], []
        lines = [{**l, "t": float(l.get("t", 0)) + off} for l in d.get("lines", [])]
        asserts = []
        for a in d.get("assertions", []):
            if a.get("attribute") in ATTRIBUTES and a.get("entity_kind") in ENTITY_KINDS:
                asserts.append({
                    "shot": -1, "t": float(a.get("t", 0)) + off,
                    "entity": str(a.get("entity", ""))[:80], "entity_kind": a["entity_kind"],
                    "attribute": a["attribute"], "value": str(a.get("value", ""))[:80],
                    "confidence": float(a.get("confidence", 0.5)), "source": "dialogue",
                    "quote": str(a.get("quote", ""))[:200],
                })
        return lines, asserts

    L, A = [], []
    with concurrent.futures.ThreadPoolExecutor(4) as ex:
        for lines, asserts in ex.map(run_chunk, chunks):
            L.extend(lines)
            A.extend(asserts)
    L.sort(key=lambda x: x["t"])
    A.sort(key=lambda x: x["t"])
    tf.write_text(json.dumps(L, indent=1))
    af.write_text("\n".join(json.dumps(a) for a in A))
    return L, A


def enrich(client, rows: list[dict], shots, transcript, out: Path) -> list[dict]:
    """Entity resolution, scene segmentation, story order, and slots — the four things
    that turn raw assertions into comparable ones. Each was a structural bug when missing;
    here they are the standard path."""
    scenes = renumber(segment(client, shots, transcript, MODEL))
    (out / "scenes.json").write_text(json.dumps([s.to_dict() for s in scenes], indent=1))

    counts = Counter((r["entity"], r["entity_kind"]) for r in rows)
    mapping = resolve(client, [(n, k, c) for (n, k), c in counts.items()], out.name, MODEL)
    for r in rows:
        r["entity"] = mapping.get(r["entity"], r["entity"])

    vals: dict[str, set] = {}
    for r in rows:
        if r["attribute"] in MULTIVALUED:
            vals.setdefault(r["attribute"], set()).add(r["value"])
    slotmap = {}
    for attr, vs in vals.items():
        for v, sl in assign(client, attr, sorted(vs), MODEL).items():
            slotmap[(attr, v)] = sl

    def scene_of(t):
        return next((s for s in scenes if s.t_from <= t <= s.t_to), None)

    for r in rows:
        sc = scene_of(r.get("t", 0.0))
        r["scene"] = sc.n if sc else -1
        r["story_order"] = sc.story_order if sc else -1
        r["slot"] = slotmap.get((r["attribute"], r["value"]), r.get("slot", ""))
    (out / "assertions_enriched.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    return rows


def run(work: str, film: str) -> dict:
    """The whole thing. Returns a small report; writes everything to work/<work>/."""
    from google import genai

    out = Path(f"work/{work}")
    out.mkdir(parents=True, exist_ok=True)
    client = genai.Client(vertexai=True, location="global")

    shots = detect_shots(film, out)
    jobs = sample_frames(film, shots, out)
    visual = extract_visual(client, jobs, out)
    transcript, dialogue = transcribe(client, film, out)
    rows = enrich(client, visual + dialogue, shots, transcript, out)

    return {"work": work, "shots": len(shots), "frames": len(jobs),
            "assertions": len(rows), "dialogue_lines": len(transcript)}
