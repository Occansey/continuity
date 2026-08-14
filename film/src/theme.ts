/**
 * The film's design system.
 *
 * The first pass was cream ground, Didot display, bronze accent: a luxury-house look
 * borrowed wholesale, and the single most predictable palette anyone reaches for. It
 * said nothing about this subject and every other entry could arrive wearing it.
 *
 * This one is taken from the thing itself. Geminga is a gamma-ray source with no
 * counterpart at any other wavelength, found on a photographic plate by the absence of
 * anything where something should have been. So the film is built like plate work: an
 * ink ground, fiducial ticks in the margins, a plate number on every frame, and type
 * that behaves like an observing log rather than a masthead.
 *
 * The ground is dark for a functional reason as well as a thematic one. The console and
 * the architecture model are both dark, and setting them into cream made every piece of
 * evidence a bright rectangle floating in a bright room. On ink they sit in the same
 * world as the frame around them, which is what lets the film cut between argument and
 * evidence without the cut being the loudest thing in it.
 */

export const FPS = 30;

export const C = {
  /** Ink, with a blue bias. A neutral black would read as switched off. */
  ground: "#06090C",
  /** One step up, for the two scenes that need to feel like a different room. */
  deep: "#020406",
  panel: "#0D1218",

  /** Type. Cold rather than warm: this is instrument output, not stationery. */
  ink: "#E8EEF3",
  bone: "#E8EEF3",
  inkSoft: "#BAC7D2",
  inkFaint: "#8998A6",

  rule: "#2A353F",
  tick: "#3A4A57",

  /**
   * Sodium. The one accent, and it is spent only on the thing currently under
   * discussion, never on decoration. Amber against ink is the observatory's own
   * colour scheme, chosen because it does not spoil dark adaptation.
   */
  sodium: "#E8A33C",
  /** Kept from the product, and only ever means verified. */
  verdigris: "#4FB08A",
  /** Refusals. This system declines things all day; that is not an alarm state. */
  slate: "#6B7B88",
} as const;

export const F = {
  /**
   * A slab serif for display. Nineteenth-century scientific plates, railway timetables,
   * instrument faceplates: it carries authority without the fashion-magazine register a
   * high-contrast didone brings, and it holds up at 70px on a dark ground where a hairline
   * serif would disintegrate.
   */
  display: '"Superclarendon", "Rockwell", "Bookman Old Style", "Georgia", serif',
  /** Running text. */
  text: '"Avenir Next", "Optima", "Helvetica Neue", system-ui, sans-serif',
  /** Anything that is evidence: numbers, code, names of things, every label. */
  mono: '"SF Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
} as const;

/** Seconds → frames, so scene timings read as time rather than arithmetic. */
export const s = (seconds: number) => Math.round(seconds * FPS);

/**
 * Slow, confident easing. No overshoot anywhere in this film: a spring that bounces
 * reads as eager, and nothing here should look eager.
 */
export const ease = (t: number) => 1 - Math.pow(1 - t, 3);
export const easeInOut = (t: number) =>
  t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
