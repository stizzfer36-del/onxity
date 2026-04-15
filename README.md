# ONIXTY

ONIXTY is a **local-first agent runtime** with one operator CLI, governed execution, append-only audit, and a local capability absorption pipeline.

This repository is currently focused on **clone-and-run reliability** for the implemented runtime.

## First 5 minutes (copy/paste)

```bash
git clone <YOUR_ONIXTY_REPO_URL>
cd onxity

# Linux/macOS bootstrap (creates venv, installs, runs first-run)
./scripts/bootstrap.sh

# Verify runtime
source .venv/bin/activate
python -m onxity.cli doctor
python -m onxity.cli daemon-start
sleep 1
python -m onxity.cli daemon-status
python -m onxity.cli daemon-stop
printf "quit\n" | python -m onxity.cli repl
./scripts/smoke_runtime.sh
```

Windows PowerShell bootstrap:

```powershell
./scripts/bootstrap.ps1
python -m onxity.cli doctor
```

## Common install paths

### Path A (standard editable install)
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

### Path B (fallback if build isolation/network causes issues)
```bash
python -m pip install -e . --no-build-isolation --no-deps
```

## Verify ONIXTY is running

1. Run onboarding:
   - `python -m onxity.cli first-run --non-interactive`
2. Start daemon:
   - `python -m onxity.cli daemon-start`
3. Confirm status shows `running: true` and a PID:
   - `python -m onxity.cli daemon-status`
4. Stop daemon cleanly:
   - `python -m onxity.cli daemon-stop`
5. Confirm environment and paths:
   - `python -m onxity.cli doctor`

## Troubleshooting

### Install fails
- Run fallback install: `python -m pip install -e . --no-build-isolation --no-deps`
- Check environment details: `python -m onxity.cli doctor`
- Ensure Python is 3.10+.

### Daemon looks stuck or PID is stale
- `python -m onxity.cli daemon-status`
- `python -m onxity.cli daemon-stop`
- Retry: `python -m onxity.cli daemon-start`

### REPL in non-interactive scripts
- Use piped input: `printf "quit\n" | python -m onxity.cli repl`

## Implemented surfaces

- Kernel runtime: persistent identity/runtime state, heartbeat daemon, event bus, policy budgets.
- CLI: first-run, doctor, daemon lifecycle, REPL, approvals, absorb.
- Embodiment tools: filesystem, process/host info, terminal execute, git status, URL fetch.
- Agency governance: worker spawn policy, verify/recovery hooks.
- Capability absorption: quarantine/classify/scan/score/sign/stage.
- JSON-RPC primitive + Python client.

## Docs

- `docs/operator-guide.md`
- `docs/architecture.md`
- `docs/pack-authoring.md`
- `docs/sdk-guide.md`
- `docs/security-model.md`
- `docs/restricted-domain-policy.md`
