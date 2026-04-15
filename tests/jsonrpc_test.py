from __future__ import annotations

from onxity.api.jsonrpc import JsonRpcServer, PythonClient


def test_jsonrpc_roundtrip():
    server = JsonRpcServer(methods={"sum": lambda a, b: {"value": a + b}})
    client = PythonClient(server)
    out = client.call("sum", a=2, b=3)
    assert out["value"] == 5
