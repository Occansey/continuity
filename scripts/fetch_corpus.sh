#!/usr/bin/env bash
# Footage is not in the repository. This fetches it and records provenance.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p corpus
[ -f corpus/detour-1945.mp4 ] || curl -L --fail -o corpus/detour-1945.mp4 \
  "https://archive.org/download/detour-1945_202502/Detour%201945.ia.mp4"
shasum -a 256 corpus/detour-1945.mp4
