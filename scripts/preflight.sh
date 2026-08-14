#!/usr/bin/env bash
# G5. Everything the submission claims, checked from outside the repository.
#
# Run from anywhere; it works from the project root regardless. A previous project's
# deploy script uploaded the wrong directory for a week because it assumed a cwd.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
say() { printf "  %-42s %s\n" "$1" "$2"; }

URL="${CONTINUITY_URL:-}"
if [ -z "$URL" ]; then
  say "hosted URL" "SKIP (set CONTINUITY_URL)"
else
  code=$(curl -s -o /dev/null -w '%{http_code}' "$URL" || echo 000)
  [ "$code" = "200" ] && say "hosted URL" "200" || { say "hosted URL" "$code"; fail=1; }
fi

[ -f LICENSE ] && say "licence" "present" || { say "licence" "MISSING"; fail=1; }

# "Imported and called in code" is a submission requirement, so it is checked rather
# than asserted: every line PARTNER.md points at has to still be there.
if [ -f docs/PARTNER.md ]; then
  bad=0
  while IFS= read -r ref; do
    file="${ref%%:*}"; line="${ref##*:}"
    [ -f "$file" ] && [ "$(wc -l < "$file")" -ge "$line" ] || { echo "      dangling: $ref"; bad=1; }
  done < <(grep -oE '[a-zA-Z0-9_/.-]+\.py:[0-9]+' docs/PARTNER.md || true)
  [ $bad -eq 0 ] && say "partner call sites" "resolve" || { say "partner call sites" "DANGLING"; fail=1; }
else
  say "partner call sites" "docs/PARTNER.md MISSING"; fail=1
fi

exit $fail
