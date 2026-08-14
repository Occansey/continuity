"""Measure how many of our findings the prior art could reach.

Runs the registration test over the flagged findings AND over a control set of same-scene
consecutive shots, which SHOULD be reachable. The contrast is the point: if same-scene
pairs register and our findings do not, the differentiation is demonstrated rather than
asserted.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, "src")
from continuity.reachability import registrable

FRAMES = Path("work/frames")

def frame(shot):
    return FRAMES / f"s{int(shot):04d}.jpg"

# findings: everything the last run flagged as error, plus every cross-scene candidate
transitions = json.load(open("work/transitions.json"))
verdicts = [json.loads(l) for l in open("work/verdicts.jsonl")]
errs = {(v["entity"], v["attribute"], round(v["t_from"],1)) for v in verdicts if v["verdict"]=="error"}

findings = [t for t in transitions
            if (t["entity"], t["attribute"], round(t["t_from"],1)) in errs
            or t["scene_from"] != t["scene"]]

# Control: two frames half a second apart INSIDE one shot — same camera, same setup, the
# textbook case registration is built for. Consecutive *shots* are the wrong control: film
# cuts between angles, so a shot-to-shot pair often does not register either, and using it
# made the finding and the control both ~93% and the metric meaningless. That was a real
# bug in the first version of this eval, caught because the control did not behave the way
# a working control must.
import subprocess
CTRL = Path("work/ctrl"); CTRL.mkdir(exist_ok=True)
control = []
for s in [x for x in json.load(open("work/shots.json")) if x["end"]-x["start"] > 2.0][:60]:
    mid = (s["start"] + s["end"]) / 2
    fa, fb = CTRL / f"c{s['n']}_a.jpg", CTRL / f"c{s['n']}_b.jpg"
    for out, t in ((fa, mid-0.25), (fb, mid+0.25)):
        if not out.exists():
            subprocess.run(["./scripts/ffmpeg.sh","-hide_banner","-loglevel","error","-ss",f"{t:.3f}",
                            "-i","corpus/detour-1945.mp4","-frames:v","1","-q:v","3",str(out)],check=False)
    if fa.exists() and fb.exists():
        control.append((str(fa), str(fb)))

def measure(pairs, label):
    reach = 0; total = 0
    for sf, st in pairs:
        fa = frame(sf) if isinstance(sf, int) else Path(sf)
        fb = frame(st) if isinstance(st, int) else Path(st)
        if not (fa.exists() and fb.exists()):
            continue
        r = registrable(fa, fb)
        reach += r.reachable; total += 1
    print(f"  {label:<38} {total-reach:>3}/{total:<3} unreachable by registration "
          f"({100*(total-reach)/max(1,total):.0f}%)")
    return total - reach, total

print("=== can the prior art reach these pairs? ===")
fu, ft = measure([(t["shot_from"], t["shot_to"]) for t in findings], "our findings (cross-scene + errors)")
cu, ct = measure(control, "control: same shot, 0.5s apart")

print(f"\n  Our findings: {fu}/{ft} lie outside every registration method's reach.")
print(f"  Control:      {ct-cu}/{ct} same-setup pairs register fine, as expected.")
json.dump({"findings_unreachable": fu, "findings_total": ft,
           "control_unreachable": cu, "control_total": ct},
          open("work/reachability.json","w"), indent=1)
