# ONIXTY Operator Guide

## Clone-to-first-run

### Linux/macOS
1. `git clone <YOUR_ONIXTY_REPO_URL>`
2. `cd onxity`
3. `./scripts/bootstrap.sh`

### Windows PowerShell
1. `git clone <YOUR_ONIXTY_REPO_URL>`
2. `cd onxity`
3. `./scripts/bootstrap.ps1`

## Manual setup (if not using bootstrap)
1. `python -m venv .venv`
2. `source .venv/bin/activate` (PowerShell: `.\.venv\Scripts\Activate.ps1`)
3. `python -m pip install --upgrade pip`
4. `python -m pip install -e .`
5. If step 4 fails due build isolation/network: `python -m pip install -e . --no-build-isolation --no-deps`
6. `python -m onxity.cli first-run --non-interactive`

## Core runtime lifecycle
- Start daemon: `python -m onxity.cli daemon-start`
- Check daemon: `python -m onxity.cli daemon-status`
- Stop daemon: `python -m onxity.cli daemon-stop`
- Run diagnostics: `python -m onxity.cli doctor`

## REPL
- Interactive: `python -m onxity.cli repl`
- Non-interactive smoke: `printf "quit\n" | python -m onxity.cli repl`

## Smoke validation
- Full smoke script: `./scripts/smoke_runtime.sh`

## Where ONIXTY stores local state
Default paths (from `python -m onxity.cli doctor`):
- Config: `~/.onxity/config.yaml`
- DB: `~/.onxity/onxity.db`
- Audit log: `~/.onxity/audit.jsonl`
- Identity: `~/.onxity/identity.json`
- Runtime state: `~/.onxity/runtime_state.json`
- Daemon PID: `~/.onxity/daemon.pid`
- Packs: `~/.onxity/packs.json`
- Plugin quarantine: `~/.onxity/plugins/quarantine/`

## If something fails
1. `python -m onxity.cli doctor`
2. `python -m onxity.cli daemon-status`
3. `python -m onxity.cli daemon-stop`
4. Re-run `./scripts/smoke_runtime.sh`
