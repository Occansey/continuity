import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setConcurrency(4);

// Remotion could not download its own headless shell in this environment, so it
// renders through the Chrome already installed on the machine. Anyone reproducing
// this on Linux should point it at their own binary or let Remotion fetch one.
Config.setBrowserExecutable(
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
);
