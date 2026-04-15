# SDK Guide

## Python SDK (local)

```python
from onxity.api.jsonrpc import JsonRpcServer, PythonClient

server = JsonRpcServer(methods={"ping": lambda: {"ok": True}})
client = PythonClient(server)
print(client.call("ping"))
```

## .NET client sketch

Use `HttpClient` or named pipes to send JSON-RPC payloads:

```json
{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}
```

Response format follows JSON-RPC 2.0.
