# Continuity — specification

> **Continuity** is the department whose job is that the world of the story stays the same
> world. Not that the shots match — that the *facts* match. The wound is on the left
> cheek. The ring goes on after the wedding. The dog is still alive.

**Status:** draft 4, 14 Aug 2026. Three drafts were discarded: delivery QC, a streaming
incident agent, and visual continuity. The last of those died on prior art that should
have been checked before it was chosen. See `docs/PRIOR-ART.md`, `docs/DECISIONS.md` D6.

No code lands that this document does not describe.

---

## 1. The problem, stated precisely

There are two continuity problems and the industry uses one word for both.

**Shot continuity.** Two shots cut together, from different takes, minutes apart. The
glass is full then empty. The frames look alike, so you can register one onto the other
and diff the pixels.

*This one is solved.* Pickup and Zisserman published the method in 2009 and reported
finding errors that published listings had missed; a startup is commercialising it now.
We are not doing this.

**Story continuity.** A character is cut on the left cheek in scene 12, shot in April. In
scene 30, shot in June on another location, the cut is on the right. Or gone. Or she is
wearing the ring three days before the wedding, or the dog that died in episode 4 is in
the background of episode 9.

*This one is open*, and it is open for a structural reason: **the shots look nothing
alike.** Different location, different angle, different lighting, sometimes a different
year. Nothing registers, so every pixel-based method has nothing to say. The 2009 paper is
explicit that it operates on "pairs of shots within a scene" from similar camera angles.

Story continuity is also the harder human job. A script supervisor can hold a scene in
their head. Nobody holds seventy hours of a series.

## 2. The move

Stop comparing images. **Compare claims about the world.**

For every shot, extract what is *true* in it — who is present, what they are wearing and
carrying, what is injured and where, what time of day it is, what the weather is doing.
Store the claims. Then look for pairs of claims that cannot both be true, given the order
of the story and whether anything happened in between to explain the change.

Two shots that share no pixels can still contradict each other, and contradiction is a
query, not a distance.

## 3. What it does

1. **Watches** each shot and extracts world-state assertions with provenance: title,
   scene, shot, timecode, confidence.
2. **Resolves** entities across the work — that this is the same character, the same
   jacket, the same car, twenty episodes apart.
3. **Contradicts.** For each entity and attribute, order the assertions by story time and
   find transitions that should not have happened.
4. **Excuses.** Most transitions are fine, and this is where the work is. People change
   clothes. Wounds heal. Time passes. The question is never *did it change* but *did
   anything happen that explains it*.
5. **Maintains the bible.** Productions keep a continuity document by hand. This one is
   derived, timecoded, and always current.
6. **Interrupts — only once it has earned the right.**

## 4. What it deliberately does not do

- **It does not diff pixels.** That problem is taken; see `docs/PRIOR-ART.md`.
- **It does not flag change.** Change is the normal condition of a story. It flags
  *unexplained* change, and the difference is the entire product.
- **It does not decide what is canon.** Where the work itself is ambiguous, it escalates.
  A tool that resolves a deliberate ambiguity has damaged the film.

## 5. The inversion

Geminga defaulted toward refusing, because a false pass cost more than a false fail.

**Here a false alarm is the expensive failure.** Interrupt a shoot over a moving leaf and
you have spent the crew's time; do it twice and the tool is switched off, costing
everything it would ever have caught. filmcontinuity.com's own published figure — *207
errors from 1,340 differences* — is what this failure looks like in a product: a list
long enough that reading it is the new job.

So Continuity earns **the right to interrupt**, attribute class by attribute class. Silent
first, recording what it would have said. Then flagging in dailies review. Then the floor.
One bad interruption drops that class back.

**Precision is the metric.** Recall is reported and never traded against it.

## 6. Non-negotiables

| | |
|---|---|
| **Extraction and judgement are separate steps** | Assertions are made once, stored, and never re-derived by a model at query time. A claim you cannot look up is a claim you cannot audit. |
| **Every assertion carries provenance** | Title, scene, shot, timecode, and the frame it came from. |
| **Every contradiction cites two assertions** | With both frames. A continuity claim nobody can look at is an opinion. |
| **The database never judges** | It finds transitions. Whether a transition is an error needs a model, because "he could have changed his shirt" is world knowledge. |
| **The model never searches** | Gemini adjudicates candidates. It does not scan a corpus it cannot afford to read and then guess about the rest. |
| **Ground truth is third-party** | Published listings. We did not write the exam. |
| **Interruption is earned per class** | Silent, then review, then floor. One bad call demotes. |

## 7. Why both partners are load-bearing

**Gemini is unavoidable, and this is the draft where that is finally true.** Deciding
whether *left cheek → right cheek* is an error requires knowing that cuts do not move
across faces, that four days passed, that nothing in between explains it. That is world
knowledge and narrative reasoning. There is no threshold for it, which is precisely why
the competing product's "not an LLM" is a position rather than an optimisation — and one
we can test rather than assert.

**ClickHouse is unavoidable because contradiction search is quadratic in story length.**
A feature is a few thousand shots; a series is tens of thousands; each shot yields tens of
assertions. Checking an attribute's history means ordering and self-joining an assertions
table and asking, for every pair, whether an explaining event lies between them. That grows
with the square of the work's length, which is why nobody does this for a whole series by
hand and why a row store falls over on the one workload that matters.

Entity resolution across a franchise is the second half: vector similarity on appearance
embeddings *with* structured predicates — same production, different episode — in one
query. `evals/partner_benchmark.py` runs it against pgvector and publishes both.

Neither half can do the other's job. The database cannot know that wounds heal; the model
cannot read seventy hours.

## 8. Evidence

- **Real footage.** Films verified public domain, recorded per title with the basis.
- **Real labels, written by strangers.** Published continuity listings, used as facts — a
  timecode and a claim — never reproduced as text.
- **The claim is falsifiable by anyone with the film:** of the documented *cross-scene*
  errors, how many are found, at what precision, and how many are surfaced that no listing
  contains.
- **The comparison that matters:** how many of those cross-scene errors a registration-based
  method could reach even in principle. We expect close to none, and if we are wrong about
  that, the whole premise of draft 4 is wrong and it goes in the README.

## 9. What "done" means

1. A public-domain feature ingested end to end, on a hosted URL.
2. ClickHouse called at runtime on ingest and on contradiction search.
3. Precision and recall against published listings, separately, with intervals and N.
4. At least one cross-scene contradiction found that no listing contains, both frames shown.
5. One attribute class through the ratchet from silent to interrupting, ledger visible.
6. The benchmark against pgvector, published.
7. A three-minute film that shows it staying quiet about a change that has an explanation.

## 10. Open questions

- **What is the assertion schema?** Too loose and nothing joins; too tight and the world
  does not fit. Blocks everything downstream.
- **What is story time?** Scene order is not story order — flashbacks, intercuts. Blocks
  the ordering the contradiction search depends on.
- **What counts as an explaining event, and who decides?** This is where false alarms come
  from.
- **Agent Builder as host, or Gemini called directly?** The rules require Agent Builder.
