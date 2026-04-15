# ONIXTY

ONIXTY is a **local-first agent operating system** with one operator surface, governed tool execution, append-only audit, and capability absorption through signed packs.

## What is implemented

- Kernel runtime with persistent identity, runtime state, daemon heartbeat, event bus, audit writer, policy budgets.
- CLI with first-run onboarding, daemon start/stop/status, REPL operator surface, approval flow, and pack absorption.
- Embodiment tools: filesystem, process listing, host health, sandboxed terminal execution, git status, URL fetch.
- Agency governance: team orchestrator with depth/worker limits, risk budgets, verifier and recovery supervisor hook.
- Capability absorption pipeline: quarantine copy, classification, risk scan, manifest wrapping, scoring, signing, staged registry.
- Local JSON-RPC primitives + Python client for SDK integration.

## Quickstart

```bash
python -m onxity.cli first-run --non-interactive
python -m onxity.cli daemon-start
python -m onxity.cli daemon-status
python -m onxity.cli repl
```

## Tests

```bash
pytest -q
```

## Safety posture

Restricted/offensive capabilities are **not active core functionality**. The absorption system flags risky imports/scopes and stages packs for explicit review.

## Docs

- `docs/architecture.md`
- `docs/operator-guide.md`
- `docs/pack-authoring.md`
- `docs/sdk-guide.md`
- `docs/security-model.md`
- `docs/restricted-domain-policy.md`
