# Prior art

Checked 14 Aug 2026, after choosing the idea and before building it. It should have been
checked before choosing. Recording it in full, including the part that is bad for us.

---

## 1. Pickup & Zisserman, *Automatic retrieval of visual continuity errors in movies*, CIVR 2009

University of Oxford. Andrew Zisserman is one of the most cited people in computer vision.

**Their method.** Shot detection by RGB histogram; shot *matching* into threads using the
ABAB structure of edited dialogue; homography registration between the last frame of one
shot and the first of the next; per-pixel discrepancy on the registered pair; suppress
regions explained by an upper-body detector, because people are supposed to move; rank
what is left.

**Their result, in their own abstract:** they "discover mistakes that have previously been
missed in the listings for these movies on such websites as `moviemistakes.com`."

That sentence is the demo moment I had planned as our headline. It was published in 2009.

**What it cannot do, and says so.** The approach is defined over "pairs of shots *within a
scene* that might have arisen from different takes", and it works by registering frames
from *similar camera angles*. Anything that does not register — a different scene, a later
episode, a wider setup — is outside the method by construction.

## 2. filmcontinuity.com

Pre-launch, "request access". Reviews dailies overnight on GPU infrastructure and returns
a report with side-by-side frames before the next call time.

**Their stated design position:** "a deterministic computer vision pipeline — detection,
segmentation, visual embeddings. **Not an LLM.** That's why it's fast, cheap, and
explainable when a script supervisor asks why something was flagged."

**Their own headline number:** *207 errors from 1,340 total differences.*

Read that as a user rather than as marketing. The pipeline surfaces 1,340 differences and
calls 207 of them errors, and a human still has to work through what comes out. It is the
same shape as every QC tool: **findings, ranked, handed over.**

## 3. What this means

**The detection problem is not novel and we should stop pretending otherwise.** It is a
seventeen-year-old published result currently being commercialised. Reimplementing it with
better primitives is a weekend of nostalgia, not a contribution, and a judge who spends
thirty seconds on Google finds both of these.

**Two gaps survive, and they are the same gap.**

1. **Neither one decides anything.** The paper ranks. The product reports. Both hand a
   list to a person, which is exactly the position this project has argued against twice
   now in two different domains.
2. **Both are bounded by registration.** They compare shots that look alike. The errors
   that survive to release — and the ones a human is worst at — are the ones separated by
   *story time*, not by camera angle: a wound that changes cheek between scenes, a ring
   worn before the wedding, a scar that heals across episodes. Nothing registers there,
   so nothing in either approach applies.

The second gap is not a refinement of their problem. It is a different problem that
happens to share a name, and it is the one where a language model is unavoidable rather
than optional — which makes filmcontinuity.com's "not an LLM" a design position we can
contest with evidence instead of an obstacle.
