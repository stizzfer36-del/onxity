# ONIXTY

Local-first agent runtime with CLI, daemon lifecycle, audit/memory state, and capability absorb pipeline.

## Quickstart (Linux/macOS)
```bash
git clone <YOUR_REPO_URL>
cd onxity
./scripts/bootstrap.sh

source .venv/bin/activate
python -m onxity.cli doctor
python -m onxity.cli daemon-start
sleep 1
python -m onxity.cli daemon-status
python -m onxity.cli daemon-stop
printf "quit\n" | python -m onxity.cli repl
./scripts/smoke_runtime.sh
```

## Quickstart (Windows PowerShell)
```powershell
git clone <YOUR_REPO_URL>
cd onxity
./scripts/bootstrap.ps1
python -m onxity.cli doctor
```

## If install fails
```bash
python -m pip install -e . --no-build-isolation --no-deps
python -m onxity.cli doctor
```

## Useful commands
- `python -m onxity.cli first-run --non-interactive`
- `python -m onxity.cli daemon-start|daemon-status|daemon-stop`
- `python -m onxity.cli repl`
- `python -m onxity.cli absorb <path-to-pack-repo>`

## Docs
- `docs/operator-guide.md`
- `docs/architecture.md`
- `docs/security-model.md`
