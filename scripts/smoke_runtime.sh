#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -c 'import importlib.util as u; assert u.find_spec("onxity") is not None, "onxity package is not importable"; print("import check: ok")'

"$PYTHON_BIN" -m onxity.cli doctor
"$PYTHON_BIN" -m onxity.cli first-run --non-interactive
"$PYTHON_BIN" -m onxity.cli daemon-start
sleep 1
"$PYTHON_BIN" -m onxity.cli daemon-status
"$PYTHON_BIN" -m onxity.cli daemon-stop
printf 'quit\n' | "$PYTHON_BIN" -m onxity.cli repl

"$PYTHON_BIN" -c 'from onxity.api.jsonrpc import JsonRpcServer, PythonClient; s=JsonRpcServer(methods={"ping": lambda: {"ok": True}}); c=PythonClient(s); print("jsonrpc:", c.call("ping"))'

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
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
"$PYTHON_BIN" -m onxity.cli absorb "$tmpdir/plugin"

echo "smoke_runtime.sh: success"
