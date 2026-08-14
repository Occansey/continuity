# Working in this repository

Read `SPECIFICATION.md` first. It is the contract; this file is how we honour it.

If an instruction here conflicts with the specification, the specification wins and this
file is wrong. If reality conflicts with the specification, stop and change the
specification before writing the code that contradicts it.

---

## 1. Specification first

No code lands that the specification does not describe.

This is not ceremony. On the last project four separate modules were written, tested and
merged while being reachable from nothing, because the thing they were supposed to serve
was never written down precisely enough to notice the gap. The specification is the list
of things that must be true; anything not on it is either unnecessary or an amendment,
and an amendment is a decision worth making on purpose.

**Before writing a module:** find the clause it implements. If there isn't one, write the
clause first and say why.

## 2. Verification loops

The rule the last project learned the hard way, three separate times:

> **A module with passing tests is evidence about the module, not about the pipeline.**

Every one of the six bugs that reached production had green unit tests. All six died on
contact with the running system. So:

- **Assert end state, never the label.** `not ledger.decide(op, shape).commits` — ask the
  gate, not the thing that wrote to the gate. Twice an eval scored the route a decision
  claimed rather than what actually happened to the world.
- **Test the wiring separately from the unit.** `test_wiring.py` exists to import the
  server module and assert against the object it really uses, because every unit test
  builds its own dependencies and none of them notice when the server builds different
  ones.
- **Run the deployed thing.** A render, a request, a page opened in a browser. Five of
  the six bugs were found by curl; two needed the page.
- **A fail-safe that does not log is indistinguishable from a module that was never
  wired.** If a path swallows an error and returns a safe default, it says so out loud.

## 3. Guardrails

The system decides whether to modify somebody's master. The guardrails are the product,
not a wrapper around it.

- **Defaults resolve toward refusing.** Uncertain measurement, missing threshold,
  unparseable spec clause: escalate. Never pass.
- **The model never sets a number.** Gemini decides what a finding *means*. Whether 
  `-23.4 LUFS` breaches `-24 ±2` is arithmetic, and arithmetic does not get a language
  model.
- **Nothing widens on its own.** Authority is granted only in exchange for verified clean
  runs. Every other door into the ledger clamps.
- **Ledgers are append-only.** No delete, no amend, no purge. The agent is the thing
  being audited.
- **Attack and failure history may raise scrutiny and may never lower it.** A control that
  learns from what happened to it is a control that can be trained.

## 4. Context management

- **The specification, this file, and `docs/PLAN.md` are the durable state.** Anything a
  future session needs must land in one of them or in a decision record. Conversation is
  not storage.
- **Decisions go in `docs/DECISIONS.md`** with the reasoning, including the option not
  taken. A decision whose alternatives are unrecorded gets relitigated every time someone
  new looks at it.
- **Prefer a file over a long explanation.** If it took a paragraph to explain, it will
  take the same paragraph again next week.
- **Subagents get a brief, not a transcript.** Hand a task, the relevant clause, and the
  exit criteria. Handing context is how a subagent inherits a mistake.

## 5. Trajectory review

At each phase boundary in `docs/PLAN.md`, before starting the next one:

1. What does the specification say is true now that was not true before?
2. What did we build that no clause asks for?
3. What is now wired to nothing?
4. What did we assert without measuring?

Question three has a track record. Ask it out loud, and ask it of the deployed
artefact rather than the repository.

## 6. Sandboxing and isolation

- **Media work happens on copies.** Any operation that writes to a master writes to a new
  file and leaves the original untouched. There is no in-place path, and adding one is an
  amendment to the specification.
- **The extractor runs against fixtures by default.** Pointing it at real footage is an
  explicit opt-in, and writing repairs is a *second*, separate opt-in. Reading the world
  and changing it are different decisions and must not share a switch.
- **Credentials never reach a subagent's context.** They come from the environment at the
  call site.
- **Long or destructive work runs in its own worktree** so a half-finished migration
  cannot be what someone else builds on.

## 7. Exit criteria and gates

`docs/GATES.md` holds the exit criteria for each phase, written before the phase starts.
A phase is not complete because the code exists. It is complete when its gate passes,
and the gate is a command someone else can run.

Any claim in the submission has a gate behind it. If a number appears in the README, the
film, or the Devpost write-up, there is a command that regenerates it.

## 8. Retrieval

- Delivery specs are **structured data with citations**, never prose in a prompt. A
  threshold the model recalled is a threshold nobody can check.
- Telemetry lives in ClickHouse and is queried, not summarised into context. The store is
  the retrieval stack; the model reads results, not rows.
- Nothing an attacker or an upstream vendor can write reaches a decision path. Labels,
  filenames and embedded metadata are input, not instruction.

## 9. Feedback and iteration

- **Calibration is reported both ways.** False-pass and false-fail, with intervals. A
  single accuracy number hides the only distinction this product exists to make.
- **Every fixed defect leaves a test named after what actually went wrong,** not after the
  function it lives in.
- **When a measurement disagrees with a claim, the claim changes.** Including in the
  film, including the day before the deadline.

## 10. Style

Match the surrounding code. Comments explain *why*, and are worth writing when the
reasoning is not recoverable from the code — a threshold's source, a defaulting
direction, a bug this shape once caused. Do not annotate the obvious.
