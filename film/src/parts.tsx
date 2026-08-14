import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { C, F, FPS, ease, easeInOut, s } from "./theme";
import { useMeter } from "./meter";

/** Fade a child in and, optionally, back out. The film's only workhorse. */
export const Fade: React.FC<{
  at?: number;
  dur?: number;
  out?: number;
  outDur?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ at = 0, dur = 1.1, out, outDur = 0.9, children, style }) => {
  const f = useCurrentFrame();
  const inO = interpolate(f, [s(at), s(at + dur)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
  const outO =
    out === undefined
      ? 1
      : interpolate(f, [s(out), s(out + outDur)], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: ease,
        });
  return <div style={{ opacity: inO * outO, ...style }}>{children}</div>;
};

/**
 * Arrive by settling inward.
 *
 * Paired with the opening push: the bloom accelerates outward past the frame and the
 * line comes to rest coming the other way, so the two moves read as one camera rather
 * than as a thing leaving followed by a thing appearing.
 */
export const Zoomed: React.FC<{
  at?: number; dur?: number; from?: number; children: React.ReactNode; style?: React.CSSProperties;
}> = ({ at = 0, dur = 1.4, from = 1.08, children, style }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [s(at), s(at + dur)], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease,
  });
  return (
    <div style={{ opacity: p, transform: `scale(${from + (1 - from) * p})`, ...style }}>
      {children}
    </div>
  );
};

/**
 * A masked reveal — the line is uncovered rather than moved.
 * Sliding type draws attention to the motion; a wipe draws attention to the words.
 */
export const Reveal: React.FC<{
  at?: number;
  dur?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ at = 0, dur = 1.5, children, style }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [s(at), s(at + dur)], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeInOut,
  });
  return (
    <div style={{ clipPath: `inset(0 ${100 - p}% 0 0)`, ...style }}>{children}</div>
  );
};

/** A hairline that draws itself. Used to separate a claim from its evidence. */
export const Rule: React.FC<{ at?: number; dur?: number; w?: number; color?: string }> = ({
  at = 0,
  dur = 1.2,
  w = 460,
  color = C.rule,
}) => {
  const f = useCurrentFrame();
  const width = interpolate(f, [s(at), s(at + dur)], [0, w], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeInOut,
  });
  return <div style={{ width, height: 1, background: color }} />;
};

/**
 * The film's ground, and its plate furniture.
 *
 * Every scene sits on ink now rather than alternating cream and near-black. Flipping the
 * ground was doing the work of a cut, which meant the loudest thing at each transition
 * was the background rather than the argument; and it made the console footage a lit
 * window in a bright room instead of evidence in the same world as the frame.
 *
 * The ticks along the top and left edges are fiducials, the registration marks a
 * photographic plate carries so measurements taken off it can be trusted. They are also
 * the film's clock, which is what earns them their place: a progress bar laid over a film
 * is furniture, but a scale that was already in the frame can simply start reading.
 *
 * Two axes, two different facts. The top edge fills left to right across the whole film.
 * The left edge fills bottom to top through the current plate, and resets at every cut,
 * so a viewer can see both how far in they are and how long this one has left. Filling
 * upward on the vertical is deliberate: a column that drains downward reads as time
 * running out, and nothing here is on a countdown.
 */
const TOP = 52;
const SIDE = 30;

const Fiducials: React.FC = () => {
  const f = useCurrentFrame();
  const { start, dur, total } = useMeter();
  const filmP = Math.min(1, (start + f) / total);
  const plateP = Math.min(1, f / dur);

  return (
    <>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 34, display: "flex" }}>
        {Array.from({ length: TOP }, (_, i) => {
          const on = i / TOP < filmP;
          const major = i % 6 === 0;
          return (
            <div key={i} style={{
              flex: 1,
              // Filled ticks are drawn heavier as well as brighter. At 1px the meter was
              // legible in a still and invisible in motion, which is the wrong way round.
              borderLeft: `${on ? 2.5 : 1}px solid ${on ? C.sodium : C.tick}`,
              height: (major ? 15 : 7) + (on ? 5 : 0),
              opacity: on ? (major ? 0.95 : 0.7) : major ? 0.9 : 0.45,
            }} />
          );
        })}
      </div>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: 0, width: 34,
                    display: "flex", flexDirection: "column-reverse" }}>
        {Array.from({ length: SIDE }, (_, i) => {
          const on = i / SIDE < plateP;
          const major = i % 5 === 0;
          return (
            <div key={i} style={{
              flex: 1,
              borderBottom: `${on ? 2.5 : 1}px solid ${on ? C.slate : C.tick}`,
              width: (major ? 15 : 7) + (on ? 5 : 0),
              opacity: on ? (major ? 0.9 : 0.62) : major ? 0.9 : 0.45,
            }} />
          );
        })}
      </div>
    </>
  );
};

export const Field: React.FC<{
  children: React.ReactNode;
  /** The two scenes that need to feel like a different room. */
  dark?: boolean;
  pad?: number;
  /** Plate number, bottom right. Encodes sequence, which is a real fact about the film. */
  plate?: string;
}> = ({ children, dark = false, pad = 150, plate }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      background: dark ? C.deep : C.ground,
      color: C.ink,
      padding: pad,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      fontFamily: F.text,
    }}
  >
    <Fiducials />
    {children}
    {plate && (
      <div style={{ position: "absolute", right: 46, bottom: 34, fontFamily: F.mono,
                    fontSize: 12, letterSpacing: ".26em", color: C.inkFaint }}>
        {plate}
      </div>
    )}
  </div>
);

export const Statement: React.FC<{
  children: React.ReactNode;
  size?: number;
  style?: React.CSSProperties;
}> = ({ children, size = 78, style }) => (
  <div
    style={{
      fontFamily: F.display,
      fontSize: size,
      lineHeight: 1.16,
      letterSpacing: "-0.018em",
      maxWidth: 1180,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Eyebrow: React.FC<{ children: React.ReactNode; color?: string }> = ({
  children,
  color = C.inkFaint,
}) => (
  <div
    style={{
      fontFamily: F.mono,
      fontSize: 17,
      letterSpacing: "0.32em",
      textTransform: "uppercase",
      color,
      marginBottom: 34,
    }}
  >
    {children}
  </div>
);

/** Evidence is always monospaced. If it is a number, it can be checked. */
export const Datum: React.FC<{
  value: string;
  label: string;
  at?: number;
  accent?: string;
}> = ({ value, label, at = 0, accent = C.ink }) => (
  <Fade at={at} dur={0.9}>
    <div style={{ minWidth: 250 }}>
      <div
        style={{
          fontFamily: F.mono,
          fontSize: 62,
          color: accent,
          letterSpacing: "-0.03em",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontFamily: F.mono,
          fontSize: 15,
          color: C.inkFaint,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          marginTop: 10,
        }}
      >
        {label}
      </div>
    </div>
  </Fade>
);
