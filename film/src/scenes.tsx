import React from "react";
import { Img, staticFile } from "remotion";
import { C, F } from "./theme";
import { Datum, Eyebrow, Fade, Field, Reveal, Rule, Statement } from "./parts";
import { Plate as Screen } from "./Shot";
import { Schematic } from "./Schematic";
import { Mark } from "./Mark";
import { TAKE } from "./footage";

type Plate = { plate?: string };

/* ── 1. Cold open ─────────────────────────────────────────────────────────── */
export const ColdOpen: React.FC<Plate> = ({ plate }) => (
  <Field dark plate={plate}>
    <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center" }}>
      <Fade at={0.5} dur={1.5}>
        <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
          <Mark size={92} color={C.sodium} />
          <div style={{ fontFamily: F.display, fontSize: 76, letterSpacing: ".14em", color: C.ink }}>CONTINUITY</div>
        </div>
      </Fade>
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 150, textAlign: "center" }}>
      <Fade at={2.6} dur={1.4}>
        <div style={{ fontFamily: F.mono, fontSize: 21, color: C.inkFaint, letterSpacing: ".05em" }}>
          The glass was full in the last shot. It is empty in this one.
        </div>
      </Fade>
    </div>
  </Field>
);

/* ── 2. The problem ───────────────────────────────────────────────────────── */
export const Problem: React.FC<Plate> = ({ plate }) => (
  <Field plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow>The problem</Eyebrow></Fade>
    <Reveal at={0.8} dur={1.6}><Statement>Film is shot out of order, over weeks.</Statement></Reveal>
    <Fade at={3.2} dur={1.3} style={{ marginTop: 40 }}>
      <div style={{ fontSize: 28, lineHeight: 1.5, color: C.inkSoft, maxWidth: 1000 }}>
        Somebody has to remember exactly how the world looked last time. The wound on the left
        cheek. The ring worn only after the wedding. They are good at it. They still miss things.
      </div>
    </Fade>
  </Field>
);

/* ── 3. Two problems, one word ────────────────────────────────────────────── */
export const TwoProblems: React.FC<Plate> = ({ plate }) => (
  <Field dark plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow color={C.slate}>Two problems, one word</Eyebrow></Fade>
    <div style={{ display: "flex", gap: 80, marginTop: 40 }}>
      <div style={{ flex: 1 }}>
        <Fade at={0.8} dur={1}><div style={{ fontFamily: F.mono, fontSize: 15, letterSpacing: ".2em", textTransform: "uppercase", color: C.slate, marginBottom: 18 }}>Shot continuity</div></Fade>
        <Fade at={1.2} dur={1}><div style={{ fontSize: 26, color: C.bone, lineHeight: 1.5, maxWidth: 460 }}>Two shots cut together look alike. Line them up, diff the pixels. <b style={{ color: C.verdigris }}>Solved in 2009.</b></div></Fade>
      </div>
      <div style={{ flex: 1 }}>
        <Fade at={2.4} dur={1}><div style={{ fontFamily: F.mono, fontSize: 15, letterSpacing: ".2em", textTransform: "uppercase", color: C.sodium, marginBottom: 18 }}>Story continuity</div></Fade>
        <Fade at={2.8} dur={1}><div style={{ fontSize: 26, color: C.bone, lineHeight: 1.5, maxWidth: 480 }}>A cut on the left cheek in April. The right cheek in June, another location. The shots look nothing alike. <b style={{ color: C.sodium }}>Open.</b></div></Fade>
      </div>
    </div>
    <Fade at={4.6} dur={1.2} style={{ marginTop: 56 }}>
      <div style={{ fontSize: 25, color: C.inkFaint, maxWidth: 1040, lineHeight: 1.5 }}>
        Every existing tool works on pixels, so it only sees the first problem. The errors that reach
        the cinema are the second.
      </div>
    </Fade>
  </Field>
);

/* ── 4. The move ──────────────────────────────────────────────────────────── */
export const Move: React.FC<Plate> = ({ plate }) => (
  <Field plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow>The move</Eyebrow></Fade>
    <Reveal at={0.8} dur={1.6}><Statement size={72}>Stop comparing images.<br />Compare claims about the world.</Statement></Reveal>
    <Fade at={3.6} dur={1.3} style={{ marginTop: 44 }}>
      <div style={{ fontSize: 27, lineHeight: 1.55, color: C.inkSoft, maxWidth: 1060 }}>
        For every shot and every line, extract what is <em>true</em> in it — who is present, what they
        wear, what is injured and where. Two shots that share no pixels can still contradict each other,
        and a contradiction is a query, not a distance.
      </div>
    </Fade>
  </Field>
);

/* ── 5. The pipeline ──────────────────────────────────────────────────────── */
export const Pipeline: React.FC<Plate> = ({ plate }) => (
  <Field plate={plate} pad={0}>
    <Schematic seconds={22.0} />
  </Field>
);

/* ── 6. The product, live ─────────────────────────────────────────────────── */
export const Demo: React.FC<Plate> = ({ plate }) => (
  <Field dark plate={plate} pad={0}>
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingBottom: 60 }}>
      <Fade at={0.2} dur={1}><Eyebrow color={C.slate}>Live · Gemini + ClickHouse MCP · a deployed URL</Eyebrow></Fade>
      <Screen shot={TAKE} rate={TAKE.duration / 10.8} scale={0.9} />
    </div>
  </Field>
);

/* ── 7. The measurement ───────────────────────────────────────────────────── */
export const Measurement: React.FC<Plate> = ({ plate }) => (
  <Field plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow>Measured, not claimed</Eyebrow></Fade>
    <Reveal at={0.8} dur={1.5}><Statement size={54}>The old tools are blind to nine in ten of the errors we catch.</Statement></Reveal>
    <div style={{ display: "flex", gap: 70, marginTop: 52, flexWrap: "wrap" }}>
      <Datum at={2.8} value="92%" label="of our findings the prior art cannot see" accent={C.sodium} />
      <Datum at={3.5} value="3%" label="on same-camera pairs — where it works fine" accent={C.verdigris} />
    </div>
    <Fade at={4.6} dur={1.2} style={{ marginTop: 52 }}>
      <div style={{ fontSize: 26, color: C.inkSoft, maxWidth: 1080, lineHeight: 1.55 }}>
        We ran the prior art&rsquo;s own registration method on our findings. It could not line up the two
        frames <b style={{ color: C.sodium }}>92% of the time</b> — because they share no pixels. That is
        the gap we cover, measured with the competitor&rsquo;s own tool.
      </div>
    </Fade>
  </Field>
);

/* ── 8. The finding nobody could reach ────────────────────────────────────── */
export const Finding: React.FC<Plate> = ({ plate }) => (
  <Field dark plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow color={C.slate}>Said, versus shown</Eyebrow></Fade>
    <Reveal at={0.8} dur={1.5}><Statement size={54} style={{ color: C.bone }}>Some contradictions have no second frame to diff.</Statement></Reveal>
    <div style={{ display: "flex", gap: 40, marginTop: 40, alignItems: "flex-start" }}>
      <Fade at={2.4} dur={1}>
        <div style={{ fontFamily: F.mono, fontSize: 21, lineHeight: 1.7, color: C.inkSoft, borderLeft: `2px solid ${C.sodium}`, paddingLeft: 24, maxWidth: 900 }}>
          &ldquo;Three deep scratches on his <span style={{ color: C.sodium }}>right hand</span>&rdquo;
          <span style={{ color: C.inkFaint }}> — at 1043s</span><br /><br />
          &ldquo;Those scratches on his <span style={{ color: C.sodium }}>wrist</span>&rdquo;
          <span style={{ color: C.inkFaint }}> — at 2349s</span>
        </div>
      </Fade>
    </div>
    <Fade at={4.4} dur={1.2} style={{ marginTop: 40 }}>
      <div style={{ fontSize: 24, color: C.inkFaint, maxWidth: 1040, lineHeight: 1.5 }}>
        The same injury, twenty-two minutes apart, described two ways. No pixels to compare, so no
        existing tool can find it. This one did.
      </div>
    </Fade>
  </Field>
);

/* ── 8b. Survives an adversary ─────────────────────────────────────────────── */
export const Adversary: React.FC<Plate> = ({ plate }) => (
  <Field dark plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow color={C.slate}>We try to kill our own findings</Eyebrow></Fade>
    <Reveal at={0.8} dur={1.5}><Statement size={50} style={{ color: C.bone }}>A finding is only kept if it survives an adversary.</Statement></Reveal>
    <div style={{ display: "flex", gap: 64, marginTop: 50, flexWrap: "wrap" }}>
      <Datum at={2.6} value="505" label="cross-scene candidates" />
      <Datum at={3.2} value="10" label="flagged by the judge" />
      <Datum at={3.8} value="1" label="survives a second model built to refute it" accent={C.sodium} />
    </div>
    <Fade at={5.0} dur={1.2} style={{ marginTop: 50 }}>
      <div style={{ fontSize: 25, color: C.inkSoft, maxWidth: 1080, lineHeight: 1.55 }}>
        The survivor: a bruise that switched sides of a forehead — which a body cannot do off screen.
        A watch that seems to move wrists is refuted; a wound that moves is not. Measured precision,
        no human in the loop.
      </div>
    </Fade>
  </Field>
);

/* ── 9. Three films ───────────────────────────────────────────────────────── */
export const Honest: React.FC<Plate> = ({ plate }) => (
  <Field plate={plate}>
    <Fade at={0.2} dur={1}><Eyebrow>Not one film. Three.</Eyebrow></Fade>
    <Reveal at={0.8} dur={1.5}><Statement size={52}>The clean film comes back clean.</Statement></Reveal>
    <div style={{ display: "flex", gap: 56, marginTop: 48, flexWrap: "wrap" }}>
      <Datum at={2.6} value="1945" label="Detour · poverty-row · lights up" />
      <Datum at={3.2} value="1968" label="Night of the Living Dead · errors found" />
      <Datum at={3.8} value="2015" label="Cosmos Laundromat · CG · 0 false errors" accent={C.verdigris} />
    </div>
    <Fade at={5.0} dur={1.2} style={{ marginTop: 52 }}>
      <div style={{ fontSize: 26, color: C.inkSoft, maxWidth: 1080, lineHeight: 1.55 }}>
        It flags in proportion to how error-prone a film actually is. A careful modern film
        stays quiet. A tool that just found <em>differences</em> could not tell them apart. This one
        does — and no human had to judge it.
      </div>
    </Fade>
  </Field>
);

/* ── 10. Close ────────────────────────────────────────────────────────────── */
export const Close: React.FC<Plate> = ({ plate }) => (
  <Field dark plate={plate}>
    <Fade at={0.4} dur={1.6}>
      <div style={{ display: "flex", alignItems: "center", gap: 34 }}>
        <Mark size={104} color={C.sodium} />
        <div style={{ fontFamily: F.display, fontSize: 84, letterSpacing: ".14em", color: C.ink }}>CONTINUITY</div>
      </div>
    </Fade>
    <Fade at={1.8} dur={1.3} style={{ marginTop: 30 }}>
      <div style={{ fontSize: 27, color: C.inkSoft, maxWidth: 900, lineHeight: 1.5 }}>
        Everyone else compares pictures. We compare claims about the world.
      </div>
    </Fade>
    <div style={{ marginTop: 40 }}><Rule at={3.2} w={420} color={C.sodium} /></div>
    <Fade at={3.8} dur={1.2} style={{ marginTop: 30 }}>
      <div style={{ fontFamily: F.mono, fontSize: 20, color: C.inkFaint, lineHeight: 2 }}>
        Gemini · ClickHouse MCP · ADK · Cloud Run<br />
        continuity-468826425509.us-central1.run.app
      </div>
    </Fade>
  </Field>
);
