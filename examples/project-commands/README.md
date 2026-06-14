# Project commands example

Demonstrates L1/L2/L3 command catalog seeding from `package.json`.

```powershell
cd examples/project-commands
python -m ordia.cli init --sync-commands --directory . --template minimal
ordia commands validate
```

Expected sections after sync: `ordia`, `dev`, `db`, `docker`, `tunnel`, `quality`.

Reference taxonomy: [IMPROVEMENT_PLAN v0.6 §6](../../docs/ordia/archive/IMPROVEMENT_PLAN_v0.6.md).
