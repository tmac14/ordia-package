# Ordia greenfield example

Minimal walkthrough for bootstrapping a new project with `ordia init`.

## Quick start

```powershell
pip install ordia-core==0.15.0
ordia init --with-cursor --directory .
ordia doctor --json
ordia validate --project --json
ordia task summary
ordia prompt emit --intent recover
```

## Snapshot

Generate a post-init fixture for diffing:

```powershell
python tools/scaffold_greenfield_snapshot.py
```

Output: `examples/greenfield/snapshot/` (ordia.yaml + control stubs).

## Brownfield

See [packages/ordia-core/docs/BROWNFIELD.md](../packages/ordia-core/docs/BROWNFIELD.md) for adopting Ordia in existing repos (`init --skip-existing`, `ordia cursor sync`).

CI in this monorepo runs an E2E smoke in a temp directory (see `.github/workflows/test.yml` job `example-smoke`).
