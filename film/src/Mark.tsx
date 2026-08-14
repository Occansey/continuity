import React from "react";
import { C } from "./theme";

/**
 * The Continuity mark.
 *
 * Two frames of the same thing, offset — a match that does not match. The subject is the
 * gap between them: the mark is a *faux raccord*, the continuity error itself, drawn.
 * A registration tick sits in each frame at a slightly different place, because the whole
 * product is about the thing that moved when it should not have.
 */
export const Mark: React.FC<{ size?: number; color?: string; offset?: number }> = ({
  size = 120, color = "currentColor", offset = 1,
}) => (
  <svg width={size} height={size} viewBox="0 0 200 200" style={{ display: "block", overflow: "visible" }}>
    <g fill="none" stroke={color}>
      {/* first frame */}
      <rect x={40} y={52} width={96} height={72} rx={3} strokeWidth={4} opacity={0.55} />
      {/* second frame, offset — the same shot, a different take */}
      <rect x={64} y={76} width={96} height={72} rx={3} strokeWidth={4} />
    </g>
    {/* the element that should match and does not: a dot in each frame, out of register */}
    <circle cx={88} cy={88} r={7} fill={color} opacity={0.55} />
    <circle cx={136} cy={112 + offset * 6} r={7} fill={color} />
  </svg>
);
