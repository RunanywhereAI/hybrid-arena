#!/usr/bin/env bash
# v3.3 article refresh — runs both aggregators + splices their output
# into the AUTO-GENERATED-START/END markers in reports/ARTICLE.md.
#
# Usage:
#   ./bin/v3.3-refresh-article.sh             # just rewrite the article
#   ./bin/v3.3-refresh-article.sh --commit    # rewrite + git commit
#
# Idempotent: re-run any time. As new variant raw.jsonl files reach 50
# rows, the markers fill in. _pending_ rows stay until data lands.

set -e
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$HERE"

ARTICLE="reports/ARTICLE.md"

if [ ! -f "$ARTICLE" ]; then
  echo "ERROR: $ARTICLE not found" >&2
  exit 1
fi

# ---------- §3.5: per-strategy R3 ----------

STRAT_TABLE=$(python3 bin/v3.3-aggregate-strategy.py | awk '
  /^\| strategy/ { p=1 }
  p { print }
  /^\| cascade/ { p=0 }
')

# Splice between markers
python3 <<PYEOF
import re
from pathlib import Path

article = Path("${ARTICLE}").read_text()
new_table = """${STRAT_TABLE}
"""
pattern = re.compile(r"<!-- AUTO-GENERATED-START -->.*?<!-- AUTO-GENERATED-END -->", re.S)
replacement = "<!-- AUTO-GENERATED-START -->\n" + new_table.rstrip() + "\n<!-- AUTO-GENERATED-END -->"
out = pattern.sub(replacement, article, count=1)
Path("${ARTICLE}").write_text(out)
print("§3.5 strategy table refreshed.")
PYEOF

# ---------- §4.4 placeholder: per-model deep-dives (when data lands) ----------

# For now this is informational. When new-model run-dirs land, drop the
# cross-model table into a future §4.4 placeholder via a second
# AUTO-GENERATED marker.

if grep -q "AUTO-GENERATED-MODELS-START" "$ARTICLE"; then
  CROSS_TABLE=$(python3 bin/v3.3-aggregate-models.py)
  python3 <<PYEOF
import re
from pathlib import Path
article = Path("${ARTICLE}").read_text()
new = """${CROSS_TABLE}
"""
pattern = re.compile(r"<!-- AUTO-GENERATED-MODELS-START -->.*?<!-- AUTO-GENERATED-MODELS-END -->", re.S)
replacement = "<!-- AUTO-GENERATED-MODELS-START -->\n" + new.rstrip() + "\n<!-- AUTO-GENERATED-MODELS-END -->"
out = pattern.sub(replacement, article, count=1)
Path("${ARTICLE}").write_text(out)
print("§4.4 cross-model table refreshed.")
PYEOF
fi

# ---------- Optionally commit ----------

if [ "$1" = "--commit" ]; then
  if git diff --quiet "$ARTICLE"; then
    echo "No changes to commit."
  else
    git add "$ARTICLE"
    git commit -m "data(v3.3): refresh ARTICLE.md AUTO-GENERATED tables ($(date +%Y-%m-%d_%H:%M))"
    echo "Committed."
  fi
fi
