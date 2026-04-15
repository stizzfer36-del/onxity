# ONIXTY Architecture

## Kernel
- `onxity/kernel/identity.py`: durable operator identity.
- `onxity/kernel/state.py`: restart-safe session + daemon state.
- `onxity/kernel/events.py`: in-process event bus.
- `onxity/kernel/daemon.py`: persistent heartbeat daemon.
- `onxity/kernel/policy.py`: risk classification and step/time budgets.

## Core orchestration
- `onxity/core/agent.py`: CEO planning/synthesis and plan validation.
- `onxity/core/orchestrator.py`: governed tool execution, timeout and budget enforcement.
- `onxity/core/approval.py`: persistent approval token workflow.

## Embodiment
- Filesystem tools under `onxity/tools/system/`.
- Host/process/git/terminal/browser tools under `onxity/embodiment/`.

## Agency
- `onxity/agency/team.py` adds worker spawn governance, verifier path, recovery plan generation.

## Capability packs
- `onxity/plugins/absorb.py` executes absorption pipeline.
- `onxity/packs/manifest.py` canonical manifest + signatures.
- `onxity/packs/registry.py` staged/enabled pack registry.

## API / SDK
- `onxity/api/jsonrpc.py` local JSON-RPC server and Python client.
