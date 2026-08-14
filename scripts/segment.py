import json, os, sys
sys.path.insert(0, "src")
from google import genai
from continuity.scenes import renumber, segment

MODEL = os.environ.get("CONTINUITY_MODEL", "gemini-3.6-flash")
shots = json.load(open("work/shots.json"))
transcript = json.load(open("work/transcript.json"))
client = genai.Client(vertexai=True, location="global")
scenes = renumber(segment(client, shots, transcript, MODEL))
json.dump([s.to_dict() for s in scenes], open("work/scenes.json", "w"), indent=1)

print(f"  {len(scenes)} scenes over {len(shots)} shots")
pres = [s for s in scenes if s.frame == "present"]
print(f"  {len(pres)} in the present, {len(scenes)-len(pres)} in flashback")
print("\n  first twelve:")
for s in scenes[:12]:
    print(f"   {s.n:>3} shots {s.shot_from:>3}-{s.shot_to:<3} {s.t_from:>6.0f}s  story {s.story_order:>2} "
          f"{s.frame[:4]:<5} {s.place[:44]}")
# does story order disagree with screen order, as it must for a flashback film
inv = sum(1 for a, b in zip(scenes, scenes[1:]) if b.story_order < a.story_order)
print(f"\n  {inv} places where story order runs backwards against screen order")
