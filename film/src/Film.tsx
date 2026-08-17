import React from "react";
import { AbsoluteFill, Audio, Sequence, Series, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, FPS, s } from "./theme";
import { MeterContext } from "./meter";
import { TURNS } from "./vo";
import {
  ColdOpen, Problem, TwoProblems, Move, Pipeline, Demo, Measurement, Finding, Adversary, Honest, Close,
} from "./scenes";

// A 3-minute trailer, the length this hackathon asks for. Each plate is sized to its
// narration; the meter in the margins reads the film and the plate at once.
const SCENES = [
  { C: ColdOpen, sec: 8.5 },
  { C: Problem, sec: 12.3 },
  { C: TwoProblems, sec: 22.2 },
  { C: Move, sec: 14.0 },
  { C: Pipeline, sec: 16.5 },
  { C: Demo, sec: 10.0 },
  { C: Measurement, sec: 14.8 },
  { C: Finding, sec: 12.6 },
  { C: Adversary, sec: 17.6 },
  { C: Honest, sec: 18.1 },
  { C: Close, sec: 7.0 },
];

export const TOTAL = SCENES.reduce((a, x) => a + s(x.sec), 0);
const STARTS = SCENES.reduce<number[]>((acc, x, i) => [...acc, i === 0 ? 0 : acc[i - 1] + s(SCENES[i - 1].sec)], []);
const TOTAL_S = SCENES.reduce((a, x) => a + x.sec, 0);

const Narration: React.FC = () => (
  <>
    {TURNS.map((t) => (
      <Sequence key={t.file} from={STARTS[t.plate - 1] + Math.round(t.at * FPS)} durationInFrames={Math.ceil(t.dur * FPS) + 2}>
        <Audio src={staticFile(t.file)} volume={0.95} />
      </Sequence>
    ))}
  </>
);

export const Film: React.FC = () => (
  <AbsoluteFill style={{ background: C.ground }}>
    <Narration />
    <Series>
      {SCENES.map(({ C: Scene, sec }, i) => (
        <Series.Sequence key={i} durationInFrames={s(sec)}>
          <MeterContext.Provider value={{ start: STARTS[i], dur: s(sec), total: TOTAL }}>
            <Scene plate={`PLATE ${String(i + 1).padStart(2, "0")} / ${SCENES.length}`} />
          </MeterContext.Provider>
        </Series.Sequence>
      ))}
    </Series>
  </AbsoluteFill>
);
