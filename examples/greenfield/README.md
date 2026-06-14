# Ordia greenfield example

Minimal walkthrough for bootstrapping a new project with `ordia init`.

## Quick start

```powershell
pip install ordia-core
ordia init --with-cursor --directory .
ordia doctor --json
ordia validate --project --json
ordia prompt emit --intent recover
```

CI in this monorepo runs an E2E smoke in a temp directory (see `.github/workflows/test.yml` job `example-smoke`).
