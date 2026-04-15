from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class JsonRpcServer:
    methods: dict[str, callable]

    def handle(self, request_json: str) -> str:
        req = json.loads(request_json)
        method = req.get("method")
        params = req.get("params", {})
        rid = req.get("id")
        if method not in self.methods:
            return json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}})
        try:
            result = self.methods[method](**params)
            return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})
        except Exception as exc:
            return json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(exc)}})


class PythonClient:
    def __init__(self, server: JsonRpcServer):
        self.server = server

    def call(self, method: str, **params):
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        resp = json.loads(self.server.handle(req))
        if "error" in resp:
            raise RuntimeError(resp["error"]["message"])
        return resp["result"]
