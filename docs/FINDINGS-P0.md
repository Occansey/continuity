# P0 findings — 14 Aug 2026

The pipeline runs end to end on a real film. What it produces is not yet good, and the
specific ways it is not good are the useful part.

## What ran

| | |
|---|---|
| Film | *Detour* (1945), 68 min, 494×360 |
| Shots detected | 329 (threshold 0.12), 234 sampled |
| Visual assertions | 1,075 from 234 frames, 4 of 59 batches returned nothing |
| Dialogue | 540 lines transcribed, 44 spoken assertions |
| In the store | 1,119 rows |
| Transitions found | 713, of which **9 cross between dialogue and image** |

## The thing worth having

The film's own dialogue places the same injury in three places.

| | |
|---|---|
| 1043s | *"those deep scratches on his **right hand**… Three puffy red lines about a quarter of an inch apart"* |
| 1132s | a **saber cut scar on the arm** |
| 2349s | *"Those scratches on his **wrist**."* |
| 3652s | a scar on the **forearm** |

Found automatically, spanning 43 minutes, and no two of those shots have any pixels in
common. This is the class the 2009 method and filmcontinuity.com cannot reach by
construction, and it is now demonstrated rather than argued.

Whether it is an *error* is a separate question — people say "hand" and "wrist" loosely.
That question is the product, and it is the next thing to build.

## What is bad, precisely

**Precision is poor and that was expected.** 713 transitions on one film, most of them not
errors. This is exactly the 1,340-differences problem restated in a different vocabulary,
and it confirms rather than undermines the thesis: finding differences is cheap, and
deciding which ones matter is the whole job. It does mean the adjudication layer is not a
refinement to add later. It is the product, and P1 is now that, not the spec compiler.

**The attribute vocabulary is overloaded.** `position` is being used for where someone is
sitting *and* for where they were picked up two states ago. So the query compares "front
passenger seat" with "picked up outside Shreveport" and calls it a change. That is a
schema failure, not a model failure, and it is mine.

**Entity resolution is unbuilt and it shows.** `Al` and `Al Roberts`; `Haskell` and
`Charles Haskell Jr.`; `the woman`, `the female passenger` and probably `Vera`. Every one
of those splits a timeline that should be joined, so real contradictions are being missed
silently — the worst failure mode available, because the output looks the same.

**Screen order is not story order.** *Detour* is told almost entirely in flashback, and the
window function orders by timecode. Some fraction of the 713 are artefacts of narrating
the film backwards. Recorded as an open question before the run; now measured as a real one.

## Consequences for the plan

1. **P1 becomes adjudication**, not the spec compiler. Judgement is the product and the
   sooner it is measured the sooner we know if there is anything here.
2. **Entity resolution moves ahead of everything else**, because it changes recall and
   does so invisibly.
3. **Tighten the attribute list** so an attribute means one thing.
4. **Story time needs its own field** — extracted, not inferred from timecode.

## Cost

The whole run, extraction and transcription, was a few dollars of Flash. Scale is not the
constraint. Precision is.

---

# P0, second pass — resolution and adjudication

## What changed

Entity resolution and adjudication built and run. 99 extracted names collapse to 87
entities: `Al`→`Al Roberts`, `Haskell` and `Charles Haskell` →`Charles Haskell Jr.`,
`the convertible`→`convertible car`. Sensible merges, no wrong ones spotted.

724 transitions, 187 adjudicated: **169 explained · 12 not comparable · 6 errors**.

## The bug that made the first run look clean

The first adjudication sample returned **zero errors**, which read as a calibration
problem with the model. It was not. The sample was the top 160 transitions *by
confidence*, and confidence ranks what the extractor is surest about, which is clothing.
The batch was 100 `wearing` transitions and nothing else.

**Every documented error in the film was excluded from the sample.** Injury: 4 candidates,
0 judged. Hair: 34 candidates, 0 judged. Cigarette: 10 candidates, 1 judged.

A global ranking over a skewed population is a filter, and it filtered out the entire
point. Fixed by stratifying per attribute. This is the same failure this project has now
hit in three domains: **the eval measured the wrong thing and produced a clean number.**

## The six, checked by looking at the frames

Not one of these is reported as a finding without both frames having been looked at.

| | Verdict on inspection |
|---|---|
| **car: closed sedan → convertible, 4s apart** (2224→2228s) | **Strong candidate.** A wide exterior of a closed sedan with a hard roof cuts straight into a convertible interior with the top down. Consistent with the film's documented habit of reusing stock footage. Needs a human to confirm it is meant to be the same car. |
| **Haskell: passenger seat → driver seat** (983→1017s) | **False positive.** The first shot is from behind the car and the second is through the windscreen. Facing a car mirrors left and right, so both frames show the same person driving. The model does not reason about camera direction. |
| **Vera: earrings/brooch changing** (3054→3111s, 3456→3488s, 3613→3661s) | **Right place, overconfident.** This is the convertible scene where the published listing says Vera's appearance changes continually — so the search found the correct location. But at 494×360 the print cannot settle whether an earring changed, and the model returned 0.95. |
| **Vera: pose jump** (3883→3894s) | Plausible, unverified. |

## What this says

**The search works.** It found the scene the published listing points at, and it found a
sedan-to-convertible cut, without being told what to look for.

**The judgement does not, yet, in two specific ways.**

1. **No camera geometry.** Left and right reverse when the camera crosses to the other
   side, and the adjudicator does not know that. One of six errors is this bug. It is
   fixable in the prompt and must be, because it will recur on every reverse angle in
   cinema.
2. **Confidence is not calibrated.** 0.95 on a detail this print cannot resolve. The
   `unresolvable` verdict exists precisely for that case and was returned zero times in
   187 judgements, which means the model would rather decide than abstain. That is the
   wrong disposition for a tool whose metric is precision.

## Next, in order

1. Teach the adjudicator about reverse angles, and add shot framing to the assertion.
2. Make `unresolvable` reachable: state the print's resolution in the prompt and require
   abstention when the detail is below it.
3. Move to a ClickHouse Cloud cluster behind the MCP server — `chdb` does not satisfy the
   track requirement (`docs/REQUIREMENTS.md`).
4. Only then measure precision properly, on a held-out sample, with a human pass.

---

# P0, third pass — slots, and what precision actually costs

## The structural bug, found and fixed

`wearing` is not a value, it is a set. A person wears a hat and a jacket and a tie at
once, the extractor emits one assertion per garment, and the window compared each with the
next — asking whether a beret became a coat.

Measured: **485 of 724 transitions were `wearing`, and 78% of those compared different
garments.** Roughly half of everything the search produced was malformed, and no amount of
model quality could have fixed it, because the query was asking a question with no answer.

Fixed with a `slot` column — hat, outer, top, neck, legs, feet — and partitioning by
(entity, attribute, slot). Slots are assigned once over the ~200 distinct values rather
than during extraction, so it costs one call instead of a re-run.

| | before slots | after slots |
|---|---|---|
| transitions | 724 | **406** |
| `not_comparable` | 6.4% | **3.7%** |
| `unresolvable` | 0 | 3 |
| errors flagged | 6 | 2 |

## The camera fix worked

The reverse-angle false positive is now `explained`, and the model's reason cites the
geometry: *"in the driver's seat in both shots; the reverse camera angle from behind to
inside…"*. One paragraph in the prompt, and a whole class of false alarm that would recur
on every shot-reverse-shot in cinema.

## The two remaining errors, looked at

**Vera, wearing, 2228s → 2236s. Strong candidate.** Eight seconds apart in a continuous
drive: a plain light blouse under a dark jacket becomes a light patterned jacket with a
bow at the collar, and the hair changes with it. Consistent with the published complaint
that Vera's appearance changes continually in the convertible. Needs confirmation that no
scene boundary sits between the two shots.

**Vera, position, 3883s → 3894s. False positive.** This is the strangling. She moves
because she is being killed. The model read a dramatic action as a discontinuity.

## The next structural problem, from that false positive

**`position` for a person is almost always action.** People move; that is what people in
films do. The attribute is meaningful for props and vehicles — a car that changes lanes
between cuts, a glass that moves across a table — and close to meaningless for a body
inside a scene.

The fix is not a better prompt. It is that attributes need to declare *what kind of change
is expected of them*, and `position` on a `person` should not generate candidates at all
within a scene. That is the fourth structural bug found by running the thing, and like the
other three it was invisible until the output was looked at rather than counted.

## Where precision actually stands

Two flagged, one plausible. That is not a precision figure and must not be quoted as one:
the sample is small, the second judgement is mine, and I chose the film. What can be said
is that the noise floor dropped by nearly half from one schema change, and every remaining
false positive so far has had a nameable structural cause rather than being a model
failing to be clever.

---

# Tests, and the keystone measurement — 14 Aug

## Tests

Zero to 22, and they test the parts that were wrong before rather than the parts that are
easy. `test_store.py` runs the actual contradiction SQL against chdb — the same engine as
the cluster — and pins all four structural fixes found this session: slot separation, the
person-position scene gate, story order beating screen order, and cross-scene ranking.
`test_logic.py` pins the guardrails: cross-kind merges rejected, hallucinated members
dropped, unknown verdicts refused, cross-modal flagged.

Every assertion is on the output of the window or the guardrail, never on a label. That is
the discipline this project's history demands.

## The reachability metric — the differentiation, measured

The claim that separates this from all prior art is "we reach pairs a registration method
cannot". That was rhetoric until now. `evals/reachability.py` makes it arithmetic: for
each pair, run the prior art's own technique — ORB features, RANSAC homography — and count
geometric inliers. Below 15, no homography fits, and no registration-based tool reaches
the pair.

| | unreachable by registration |
|---|---|
| **our findings** (cross-scene + flagged errors) | **146 / 159 — 92%** |
| control: same shot, 0.5s apart (same setup) | 2 / 60 — 3% |

The control is the whole point of the number, and the first version of it was wrong. I
first used *consecutive shots within a scene* as the control, and it came back 93%
unreachable — identical to the findings, making the metric prove nothing. The bug was
mine: cinema cuts between angles, so consecutive shots are different setups and do not
register either. The correct positive control is two frames half a second apart inside one
shot — guaranteed same camera. Those register 97% of the time, median 306 inliers.

Caught because a control that does not separate from the treatment is a broken control,
whatever number it shows. The metric is only worth having because the control behaves.

**This is classical CV, not a model** — deliberately. It keeps us inside the no-non-Google
rule, and it means the number comes from running the competitor's actual method and
showing where it stops, rather than describing it.

---

# Three films — and the cry-wolf test

The corpus is now three films, ingested by one parameterised pipeline into one ClickHouse.

| Film | Year | Kind | Shots | Assertions | Transitions | Cross-scene |
|---|---|---|---|---|---|---|
| Detour | 1945 | live, poverty-row | 329 | 1,119 | 347 | many |
| Night of the Living Dead | 1968 | live, error-strewn | 1,281 | 3,509 | 1,428 | 505 |
| Cosmos Laundromat | 2015 | CG, carefully made | 97 | 220 | 52 | 8 |

## The result that matters

On Cosmos Laundromat — a controlled CG short, not chosen for errors and not error-prone —
the pipeline produced 8 cross-scene candidates, and adjudication called **all 8 explained.
Zero false errors.**

This is the strongest precision evidence in the project, because it needs no human judge.
A system that merely finds *differences* would light up on any film. This one flags in
proportion to how error-prone the film actually is: a sloppy 1945 quota-quickie lights up,
a controlled 2015 CG short comes back clean. The discrimination is the signal, and the
clean film proves it from the outside.

It also answers the two standing weaknesses at once. "One film" is now three, spanning
1945 to 2015 and live-action to CG. "Precision unmeasured" gains a real, judge-free
data point: fed a clean film, the tool stays quiet.

## Honest caveats

Cosmos is short (12 min), so few candidates were expected regardless; 0/8 is a clean
signal, not a precision rate. NOTLD's 505 cross-scene candidates are candidates, not
errors — its 298-entity cast makes entity resolution noisier, and adjudication (not yet
run at scale on it) is what would separate real errors from scene changes and split
timelines. The claim here is discrimination across films, not a measured precision number.
