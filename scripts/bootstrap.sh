#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN not found. Install Python 3.10+ and re-run." >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("ERROR: Python 3.10+ required")
print(f"Using Python {sys.version.split()[0]}")
PY

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR" --system-site-packages
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip --disable-pip-version-check install --upgrade pip >/dev/null 2>&1 || true

if python -m pip install -e . ; then
  echo "Installed ONIXTY with standard editable install."
else
  echo "Standard install failed; attempting offline-friendly fallback (--no-build-isolation --no-deps)..."
  python -m pip install -e . --no-build-isolation --no-deps
fi

python - <<'PY'
import importlib, sys
needed = ["click", "rich", "prompt_toolkit", "sqlalchemy", "yaml", "git", "psutil", "watchdog"]
missing = [m for m in needed if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Missing runtime dependencies: " + ", ".join(missing) + "\nInstall manually with: python -m pip install -e .")
print("Dependency check: ok")
PY

python -m onxity.cli first-run --non-interactive

echo
echo "Bootstrap complete. Next commands:"
echo "  source $VENV_DIR/bin/activate"
echo "  python -m onxity.cli doctor"
echo "  python -m onxity.cli daemon-start"
echo "  python -m onxity.cli daemon-status"
echo "  python -m onxity.cli daemon-stop"
echo "  printf 'quit\\n' | python -m onxity.cli repl"
echo "  ./scripts/smoke_runtime.sh"
