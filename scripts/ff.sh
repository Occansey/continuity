#!/usr/bin/env bash
# ffmpeg, from imageio-ffmpeg's bundled build.
#
# Remotion also ships one and it is stripped: no null encoder, no fps filter, and it fails
# in a different way for each thing you ask of it. Not worth discovering the next gap
# mid-pipeline.
exec "/Users/maxwell/hackathon/03-agentic-cinema/.venv/lib/python3.14/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1" "$@"
