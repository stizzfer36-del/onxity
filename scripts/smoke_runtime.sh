#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import importlib.util
assert importlib.util.find_spec("onxity") is not None, "onxity package is not importable"
print("import check: ok")
PY

python -m onxity.cli doctor
python -m onxity.cli first-run --non-interactive
python -m onxity.cli daemon-start
sleep 1
python -m onxity.cli daemon-status
python -m onxity.cli daemon-stop
printf 'quit\n' | python -m onxity.cli repl

python - <<'PY'
from onxity.api.jsonrpc import JsonRpcServer, PythonClient
srv = JsonRpcServer(methods={"ping": lambda: {"ok": True}})
cli = PythonClient(srv)
print("jsonrpc:", cli.call("ping"))
PY

tmpdir="$(mktemp -d)"
mkdir -p "$tmpdir/plugin"
cat > "$tmpdir/plugin/onxity_plugin.yaml" <<'YAML'
id: smoke-pack
name: Smoke Pack
version: 0.1.0
tools:
  - name: smoke.echo
    scopes: [fs:read]
YAML
cat > "$tmpdir/plugin/main.py" <<'PY'
if __name__ == '__main__':
    print('ok')
PY
python -m onxity.cli absorb "$tmpdir/plugin"

echo "smoke_runtime.sh: success"
