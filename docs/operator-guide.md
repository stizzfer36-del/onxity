# ONIXTY Operator Guide

## 1) Bootstrap
- Linux/macOS: `./scripts/bootstrap.sh`
- Windows PowerShell: `./scripts/bootstrap.ps1`

## 2) Verify runtime
```bash
python -m onxity.cli doctor
python -m onxity.cli daemon-start
sleep 1
python -m onxity.cli daemon-status
python -m onxity.cli daemon-stop
```

## 3) REPL
- Interactive: `python -m onxity.cli repl`
- Scripted: `printf "quit\n" | python -m onxity.cli repl`

## 4) Full smoke
- `./scripts/smoke_runtime.sh`

## 5) Paths (from doctor)
Defaults under `~/.onxity/`:
- `config.yaml`, `onxity.db`, `audit.jsonl`, `identity.json`
- `runtime_state.json`, `daemon.pid`, `packs.json`, `plugins/`

## Troubleshooting
1. `python -m onxity.cli doctor`
2. Retry install fallback: `python -m pip install -e . --no-build-isolation --no-deps`
3. Stop stale daemon: `python -m onxity.cli daemon-stop`
4. Run smoke: `./scripts/smoke_runtime.sh`
