$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
$VenvDir = if ($env:VENV_DIR) { $env:VENV_DIR } else { ".venv" }

& $Python -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ required'; print('Using Python', sys.version.split()[0])"

if (-not (Test-Path $VenvDir)) {
  & $Python -m venv $VenvDir --system-site-packages
}

$Activate = Join-Path $VenvDir "Scripts/Activate.ps1"
. $Activate
python -m pip --disable-pip-version-check install --upgrade pip *> $null

try {
  python -m pip install -e .
  Write-Host "Installed ONIXTY with standard editable install."
} catch {
  Write-Host "Standard install failed; attempting offline-friendly fallback (--no-build-isolation --no-deps)..."
  python -m pip install -e . --no-build-isolation --no-deps
}

python - <<'PY'
import importlib
needed = ["click", "rich", "prompt_toolkit", "sqlalchemy", "yaml", "git", "psutil", "watchdog"]
missing = [m for m in needed if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Missing runtime dependencies: " + ", ".join(missing) + "\nInstall manually with: python -m pip install -e .")
print("Dependency check: ok")
PY

python -m onxity.cli first-run --non-interactive

Write-Host "`nBootstrap complete. Next commands:"
Write-Host "  python -m onxity.cli doctor"
Write-Host "  python -m onxity.cli daemon-start"
Write-Host "  python -m onxity.cli daemon-status"
Write-Host "  python -m onxity.cli daemon-stop"
Write-Host "  'quit' | python -m onxity.cli repl"
Write-Host "  ./scripts/smoke_runtime.sh"
