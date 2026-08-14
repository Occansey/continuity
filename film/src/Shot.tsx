import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { FPS } from "./theme";
import type { Shot } from "./footage";

/**
 * Play a captured shot.
 *
 * The captures are stills on an irregular clock — a screenshot loop, because CDP's
 * screencast came back cropped under this Chrome. So instead of assuming a frame rate,
 * each shot ships a manifest of real timestamps and this resolves the film's own time to
 * the nearest one. A still hold therefore holds, rather than stuttering or dropping out,
 * and a burst of activity plays at whatever rate it was actually captured.
 */
export const Playback: React.FC<{
  shot: Shot;
  /** Seconds into the shot at the sequence's first frame. */
  from?: number;
  /** Playback rate. Below 1 stretches a short capture over a longer scene. */
  rate?: number;
  style?: React.CSSProperties;
}> = ({ shot, from = 0, rate = 1, style }) => {
  const frame = useCurrentFrame();
  const t = from + (frame / FPS) * rate;

  // Binary search would be tidier; at ~700 entries a scan is far below a frame budget
  // and keeps the failure mode obvious.
  let best = shot.frames[0];
  for (const f of shot.frames) {
    if (Math.abs(f.t - t) < Math.abs(best.t - t)) best = f;
  }

  return (
    <Img
      src={staticFile(`${shot.dir}/f${String(best.n).padStart(4, "0")}.jpg`)}
      style={{ display: "block", ...style }}
    />
  );
};

/**
 * A shot set into the film's bone field rather than filling the frame.
 *
 * The captures are dark; the film is light. Insetting them is what makes the footage
 * read as an object being shown rather than a recording being played, and it leaves
 * room for a caption that says what is happening without covering it.
 */
export const Plate: React.FC<{
  shot: Shot;
  from?: number;
  rate?: number;
  /** Fractional crop: how much of the capture's width and height to keep, from the top left. */
  crop?: { w: number; h: number; x?: number; y?: number };
  scale?: number;
  at?: number;
}> = ({ shot, from, rate, crop, scale = 1, at = 0 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at * FPS, (at + 0.8) * FPS], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const w = crop?.w ?? 1;
  const h = crop?.h ?? 1;

  return (
    <div
      style={{
        position: "relative",
        width: `${w * 100 * scale}%`,
        aspectRatio: `${1440 * w} / ${940 * h}`,
        overflow: "hidden",
        opacity: o,
        borderRadius: 3,
        // A hairline, not a drop shadow. The frame should stop the eye at the edge of
        // the evidence and then get out of the way.
        outline: "1px solid rgba(20,22,26,0.14)",
        outlineOffset: -1,
      }}
    >
      <Playback
        shot={shot}
        from={from}
        rate={rate}
        style={{
          position: "absolute",
          width: `${100 / w}%`,
          left: `${-(crop?.x ?? 0) * 100}%`,
          top: `${-(crop?.y ?? 0) * 100}%`,
        }}
      />
    </div>
  );
};
