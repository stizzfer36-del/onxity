# Pack Authoring

Create `onxity_plugin.yaml`:

```yaml
id: sample-pack
name: Sample Pack
version: 0.1.0
tools:
  - name: data.fetch
    scopes: [network]
```

Absorption pipeline stages:
1. quarantine clone/copy
2. classify language/runtime/license
3. extract entrypoints
4. scan risky imports/scopes
5. infer wrapped tools
6. score usefulness/overlap/risk/maintainability
7. generate manifest + signature
8. stage in local registry
