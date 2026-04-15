#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "ERROR: Python not found. Install Python 3.10+ and retry." >&2
    exit 1
  fi
fi

VENV_DIR="${VENV_DIR:-.venv}"

"$PYTHON_BIN" -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"; print("Using Python", sys.version.split()[0])'

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR" --system-site-packages
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if python -m pip install -e .; then
  echo "Installed ONIXTY (standard path)."
else
  echo "Standard install failed; retrying with --no-build-isolation --no-deps"
  python -m pip install -e . --no-build-isolation --no-deps
fi

python -c 'import importlib.util as u;mods=["click","rich","prompt_toolkit","sqlalchemy","yaml","git","psutil","watchdog"];missing=[m for m in mods if u.find_spec(m) is None];assert not missing, f"Missing deps: {missing}";print("Dependency check: ok")'

python -m onxity.cli first-run --non-interactive

echo
echo "Done. Next commands:"
echo "  source $VENV_DIR/bin/activate"
echo "  python -m onxity.cli doctor"
echo "  python -m onxity.cli daemon-start"
echo "  python -m onxity.cli daemon-status"
echo "  python -m onxity.cli daemon-stop"
echo "  printf 'quit\\n' | python -m onxity.cli repl"
echo "  ./scripts/smoke_runtime.sh"
