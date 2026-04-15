# Operator Guide

## Initialize
1. `python -m onxity.cli first-run --non-interactive`
2. Review `~/.onxity/config.yaml` and permission scopes.

## Run daemon
- Start: `python -m onxity.cli daemon-start`
- Status: `python -m onxity.cli daemon-status`
- Stop: `python -m onxity.cli daemon-stop`

## Use REPL
- `python -m onxity.cli repl`
- Example: `show /path/to/file`

## Approval flow
- Pending requests return token.
- Approve: `python -m onxity.cli approve <TOKEN> --attest "authorized"`

## Absorb capability repo
- `python -m onxity.cli absorb /path/to/repo`
- Review score/findings before enablement.
