# Brownfield adoption example

Minimal repo layout for `ordia docs audit` integration tests.

## Layout

- `README.md` — project overview
- `docs/ARCHITECTURE.md` — existing documentation
- `package.json` — sample npm scripts (dev, db, tunnel)

## Try it

```powershell
pip install -e packages/ordia-core
ordia docs audit --write-report --write-inventory --directory examples/brownfield-adoption/sample-repo
```
