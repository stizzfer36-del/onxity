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

try {
  python -m pip install -e .
  Write-Host "Installed ONIXTY (standard path)."
} catch {
  Write-Host "Standard install failed; retrying with --no-build-isolation --no-deps"
  python -m pip install -e . --no-build-isolation --no-deps
}

python -c "import importlib.util as u;mods=['click','rich','prompt_toolkit','sqlalchemy','yaml','git','psutil','watchdog'];missing=[m for m in mods if u.find_spec(m) is None];assert not missing, f'Missing deps: {missing}';print('Dependency check: ok')"

python -m onxity.cli first-run --non-interactive

Write-Host ""
Write-Host "Done. Next commands:"
Write-Host "  python -m onxity.cli doctor"
Write-Host "  python -m onxity.cli daemon-start"
Write-Host "  python -m onxity.cli daemon-status"
Write-Host "  python -m onxity.cli daemon-stop"
Write-Host "  'quit' | python -m onxity.cli repl"
Write-Host "  ./scripts/smoke_runtime.sh"
