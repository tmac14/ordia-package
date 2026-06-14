# ordia-package

Monorepo for **Ordia** — durable agent orchestration and implementation control.

| Package | Role |
|---------|------|
| [`packages/ordia-core/`](packages/ordia-core/) | PyPI package `ordia-core` — CLI, validator, templates, Cursor bundle |
| [`packages/ordia-cursor/`](packages/ordia-cursor/) | Dev-only npm stub; wheel embed is canonical for hooks/rules |
| [`docs/ordia/`](docs/ordia/) | Live product documentation (portable subset synced to wheel) |
| [`tools/`](tools/) | Bundle sync, release verification, documentation audits |
| [`examples/greenfield/`](examples/greenfield/) | Minimal greenfield walkthrough + CI smoke |

**Current version:** `ordia-core` **0.18.0**

---

## Install (consumers)

```powershell
pip install ordia-core==0.18.0
ordia init --with-cursor
```

---

## Development

```powershell
pip install -e "packages/ordia-core[dev]"
pytest packages/ordia-core/tests -m "not wheel"
python tools/sync_cursor_bundle.py --check --product-only
```

Full contributor guide: [`packages/ordia-core/docs/TESTING.md`](packages/ordia-core/docs/TESTING.md)

---

## Documentation

| Tree | Purpose |
|------|---------|
| [`docs/ordia/`](docs/ordia/) | Product docs (README, DAILY_USAGE, SPECs) |
| [`packages/ordia-core/docs/`](packages/ordia-core/docs/) | Technical manual (CLI, validator, architecture) |
| [`packages/ordia-core/ordia/product_docs/`](packages/ordia-core/ordia/product_docs/) | Wheel copy — kept in sync via `tools/audits/product_docs_sync.py` |

---

## CI and release

- **Test:** `.github/workflows/test.yml` — ruff, mypy, pytest matrix 3.11–3.13, doc audits
- **Publish:** `.github/workflows/publish.yml` — tag `ordia-core-v*` → test gate → wheel → PyPI

```powershell
python tools/verify_release_tag.py --tag ordia-core-v0.10.0
```

---

## Tools

| Script | Purpose |
|--------|---------|
| `tools/sync_cursor_bundle.py` | Sync `ordia-cursor` templates → `ordia/cursor_bundle/` |
| `tools/audits/docs_links.py` | Broken relative link audit |
| `tools/audits/product_docs_sync.py` | `docs/ordia/` ↔ `product_docs/` drift |
| `tools/audits/docs_inventory.py` | Documentation inventory rules |
| `tools/verify_release_tag.py` | Tag ↔ `pyproject.toml` version check |
| `tools/verify_version_parity.py` | ordia-core ↔ ordia-cursor version check |
