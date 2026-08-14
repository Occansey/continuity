import { createContext, useContext } from "react";

/**
 * Where we are, in two senses at once.
 *
 * Passed by context rather than as a prop because every plate needs it and none of them
 * should have to care: a scene is about its argument, not about its position.
 */
export type Meter = { start: number; dur: number; total: number };

export const MeterContext = createContext<Meter>({ start: 0, dur: 1, total: 1 });
export const useMeter = () => useContext(MeterContext);
