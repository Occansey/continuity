import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { C, F, FPS, ease } from "./theme";

/**
 * The pipeline, in one drawing.
 *
 * Two sources of claims — what a shot shows, what a line of dialogue says — flow into one
 * store, and the store finds the pairs that cannot both be true. Gemini judges the
 * shortlist. The arrows are the argument: two streams become one table, and a query, not a
 * model, does the finding. Built as inline SVG so every position is a coordinate and
 * nothing clips.
 */
const W = 1920, H = 1080;

const Box: React.FC<{
  x: number; y: number; w: number; h: number; title: string; sub?: string; o: number; tone?: string;
}> = ({ x, y, w, h, title, sub, o, tone = C.inkFaint }) => (
  <g opacity={o}>
    <rect x={x} y={y} width={w} height={h} rx={2} fill="rgba(255,255,255,0.014)" stroke={tone} strokeWidth={1.3} />
    <text x={x + w / 2} y={y + (sub ? h / 2 - 4 : h / 2 + 6)} textAnchor="middle" fontFamily={F.mono} fontSize={20} fill={C.ink}>{title}</text>
    {sub && <text x={x + w / 2} y={y + h / 2 + 20} textAnchor="middle" fontFamily={F.mono} fontSize={13.5} fill={C.inkFaint}>{sub}</text>}
  </g>
);

const Arrow: React.FC<{ d: string; at: number; t: number; tone?: string; dashed?: boolean }> = ({ d, at, t, tone = C.rule, dashed }) => {
  const p = interpolate(t, [at, at + 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  return (
    <path d={d} fill="none" stroke={tone} strokeWidth={1.5} markerEnd="url(#tip)"
      strokeDasharray={dashed ? "6 6" : "1600"} strokeDashoffset={dashed ? 0 : 1600 - 1600 * p} opacity={dashed ? p : 1} />
  );
};

export const Schematic: React.FC<{ seconds: number }> = ({ seconds }) => {
  const t = useCurrentFrame() / FPS;
  const fade = (a: number) => interpolate(t, [a, a + 0.8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
      <defs>
        <marker id="tip" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0.4 L6,3 L0,5.6 Z" fill={C.rule} />
        </marker>
      </defs>

      {/* two sources */}
      <text x={190} y={210} fontFamily={F.mono} fontSize={14} letterSpacing="0.14em" fill={C.slate} opacity={fade(0.2)}>TWO SOURCES OF CLAIMS</text>
      <Box x={190} y={236} w={360} h={92} o={fade(0.4)} title="every shot" sub="what the frame shows" tone={C.sodium} />
      <Box x={190} y={356} w={360} h={92} o={fade(0.9)} title="every line of dialogue" sub="what a character says" tone={C.sodium} />

      {/* the store */}
      <Arrow t={t} at={1.8} d={`M 550 282 L 720 340`} />
      <Arrow t={t} at={2.0} d={`M 550 402 L 720 360`} />
      <Box x={720} y={300} w={420} h={100} o={fade(2.0)} title="assertions" sub="subject · attribute · value · in ClickHouse" />

      {/* the query */}
      <Arrow t={t} at={3.2} d={`M 1140 350 L 1300 350`} />
      <Box x={1300} y={300} w={430} h={100} o={fade(3.2)} title="what cannot both be true" sub="a windowed query, not a model" />

      {/* judge */}
      <Arrow t={t} at={4.4} d={`M 1515 400 L 1515 560`} />
      <Box x={1300} y={560} w={430} h={100} o={fade(4.4)} title="Gemini judges" sub="is this change explained, or an error?" tone={C.verdigris} />

      {/* the two feedback truths */}
      <text x={190} y={640} fontFamily={F.mono} fontSize={20} fill={C.ink} opacity={fade(5.4)}>The database never judges.</text>
      <text x={190} y={676} fontFamily={F.mono} fontSize={20} fill={C.ink} opacity={fade(5.9)}>The model never scans.</text>
      <text x={190} y={730} fontFamily={F.mono} fontSize={16} fill={C.inkFaint} opacity={fade(6.4)}>Neither can do the other&rsquo;s job.</text>
    </svg>
  );
};
