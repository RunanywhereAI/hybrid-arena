#!/usr/bin/env bash
# scripts/reproduce.sh — one-command reproducer for hybrid-coding-eval.
#
# Checks prereqs (Python 3.11+, Docker, Ollama, Node, .env), provisions
# the sandbox image + aux models on first run, then runs a sweep through
# ./bench. Designed to be the FIRST thing a stranger runs after `git clone`.
#
# USAGE
#   scripts/reproduce.sh --smoke
#       Run the 1-task smoke sweep (configs/v1.4-smoke.yaml). ~30 seconds,
#       ~$0.01 cloud spend. If this completes cleanly, the harness is wired.
#
#   scripts/reproduce.sh --config configs/v1.4-canonical-gemma4.yaml \
#       --strategies always-cloud,always-local,heuristic,cascade \
#       --seeds 42,7,13
#       Run a full canonical sweep. ~10–15 hours on M4 Max 64 GB,
#       ~$30–50 cloud spend at gpt-5.5 list price.
#
#   scripts/reproduce.sh --config configs/v1.4-canonical-gemma4.yaml \
#       --set models.local=<new-model> \
#       --set out_dir=results/runs/v1.4-<new-model> \
#       --strategies always-cloud,always-local,heuristic,cascade --seeds 42,7,13
#       Benchmark a NEW local model against the canonical matrix.
#
# Anything after `scripts/reproduce.sh` is forwarded verbatim to `./bench sweep`
# (after we inject defaults). `--smoke` is a shortcut for the smoke recipe.

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

#─── helpers ────────────────────────────────────────────────────────────────
log()  { printf '\033[1;36m[reproduce]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[reproduce]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[reproduce]\033[0m %s\n' "$*" >&2; exit 1; }

# Detect platform so we can print the right install command.
case "$(uname -s)" in
    Darwin*) PLATFORM="mac"   ;;
    Linux*)  PLATFORM="linux" ;;
    *)       PLATFORM="other" ;;
esac

install_hint() {
    # $1=command, $2=mac hint, $3=linux hint
    local cmd="$1" mac="$2" linux="$3"
    case "$PLATFORM" in
        mac)   printf "  → install with: %s\n" "$mac" ;;
        linux) printf "  → install with: %s\n" "$linux" ;;
        *)     printf "  → install %s and re-run.\n" "$cmd" ;;
    esac
}

require_cmd() {
    # $1=command, $2=mac install hint, $3=linux install hint
    if ! command -v "$1" >/dev/null 2>&1; then
        warn "missing prerequisite: '$1'"
        install_hint "$1" "$2" "$3"
        exit 1
    fi
}

#─── parse args ─────────────────────────────────────────────────────────────
SMOKE=0
FORWARD=()
for arg in "$@"; do
    case "$arg" in
        --smoke) SMOKE=1 ;;
        -h|--help)
            sed -n '2,32p' "$0"
            exit 0
            ;;
        *) FORWARD+=("$arg") ;;
    esac
done

#─── prereq checks (fail fast) ──────────────────────────────────────────────
log "checking prerequisites…"

# Prefer python3.12 → python3.11 → python3 (in that order). Python 3.13+
# breaks several agent installers (e.g. aider-chat) because they expect
# a setuptools backend that 3.13/3.14 dropped from the stdlib bootstrap.
PYTHON_BIN=""
for candidate in python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done
if [[ -z "$PYTHON_BIN" ]]; then
    warn "missing prerequisite: 'python3.11' or 'python3.12'"
    install_hint "python3.12" \
        "brew install python@3.12" \
        "sudo apt install python3.12 python3.12-venv"
    warn "  (python3 alone is not enough — the agent runners need 3.11/3.12 specifically.)"
    exit 1
fi
log "python: $PYTHON_BIN ($($PYTHON_BIN --version))"

require_cmd docker \
    "open https://docker.com/products/docker-desktop and install Docker Desktop" \
    "sudo apt install docker.io && sudo usermod -aG docker \$USER"
require_cmd node \
    "brew install node" \
    "sudo apt install nodejs npm"
require_cmd ollama \
    "open https://ollama.com/download" \
    "curl -fsSL https://ollama.com/install.sh | sh"
require_cmd jq \
    "brew install jq" \
    "sudo apt install jq"

if ! docker info >/dev/null 2>&1; then
    case "$PLATFORM" in
        mac)   die "docker daemon not running. Open Docker Desktop, then re-run." ;;
        linux) die "docker daemon not running. Run: sudo systemctl start docker" ;;
        *)     die "docker daemon not running. Start it, then re-run." ;;
    esac
fi

PY_MINOR="$($PYTHON_BIN -c 'import sys; print(sys.version_info.minor)')"

# Ollama daemon must be reachable. We only warn (sweeps that use
# always-cloud don't need it) but a fresh user almost always wants it.
if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    warn "ollama daemon not reachable at 127.0.0.1:11434"
    case "$PLATFORM" in
        mac)   warn "  → start Ollama.app, or run: ollama serve &" ;;
        linux) warn "  → run: sudo systemctl start ollama  (or just: ollama serve &)" ;;
    esac
    warn "  proceeding anyway — only the always-cloud strategy will work without it."
fi

#─── .env presence ──────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
    warn ".env not found — copying from .env.example."
    cp .env.example .env
    warn "Edit .env and add your OPEN_AI_API_KEY before running again."
    exit 1
fi
set +u; source .env; set -u
if [[ -z "${OPEN_AI_API_KEY:-}${OPENAI_API_KEY:-}" ]]; then
    die "neither OPEN_AI_API_KEY nor OPENAI_API_KEY set in .env"
fi

#─── venv ───────────────────────────────────────────────────────────────────
# If a stale .venv exists pinned to a different Python (e.g. 3.13/3.14 from
# a previous shell), nuke it — agent installs (aider-chat) need 3.11/3.12.
if [[ -x .venv/bin/python ]]; then
    EXISTING_PY_MINOR="$(.venv/bin/python -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "x")"
    if [[ "$EXISTING_PY_MINOR" != "$PY_MINOR" ]]; then
        warn "existing .venv is Python 3.$EXISTING_PY_MINOR — recreating with $PYTHON_BIN…"
        rm -rf .venv
    fi
fi
if [[ ! -x .venv/bin/python ]]; then
    log "creating .venv ($PYTHON_BIN)…"
    "$PYTHON_BIN" -m venv .venv
fi
log "installing package (editable)…"
# Hide the routine "pip dependency resolver" warnings — the harness pins
# a known-good openai SDK; aider-chat declares a stricter range, but the
# fallback works in practice (verified by the test suite). Real errors
# still surface because we keep stderr.
.venv/bin/pip install --quiet --upgrade pip 2>&1 | grep -v "dependency resolver" || true
.venv/bin/pip install --quiet -e ".[dev]" 2>&1 | grep -vE "dependency resolver|but you have|requires openai" || true

#─── first-run setup (idempotent) ───────────────────────────────────────────
log "running ./bench setup (idempotent: Docker image + aux models + agents)…"
./bench setup

#─── pick the recipe ────────────────────────────────────────────────────────
if [[ "$SMOKE" -eq 1 ]]; then
    log "running SMOKE sweep (configs/v1.4-smoke.yaml)…"
    set -x
    ./bench sweep \
        --config configs/v1.4-smoke.yaml \
        --strategies always-cloud \
        --seeds 42 \
        --smoke
    { set +x; } 2>/dev/null
    log "analyzing smoke results…"
    ./bench analyze results/runs/v1.4-smoke
    log "smoke sweep complete. Inspect results/runs/v1.4-smoke/."
    exit 0
fi

if [[ "${#FORWARD[@]}" -eq 0 ]]; then
    die "no sweep config given. Try: scripts/reproduce.sh --smoke (or pass --config <yaml>)."
fi

log "running ./bench sweep ${FORWARD[*]}"
set -x
./bench sweep "${FORWARD[@]}"
{ set +x; } 2>/dev/null

# Best-effort analyse: if the user passed --set out_dir=… or relies on the
# config's out_dir, derive it from `./bench show-config` and call analyze.
OUT_DIR="$(./bench show-config "${FORWARD[@]}" 2>/dev/null | jq -r '.out_dir // empty' || true)"
if [[ -n "$OUT_DIR" && -d "$OUT_DIR" ]]; then
    log "analyzing $OUT_DIR…"
    ./bench analyze "$OUT_DIR"
fi

log "done."
