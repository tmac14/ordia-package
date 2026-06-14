# Commands

Project command overlay for profile **reference-demo**. Layers:

- **L1** — portable Ordia CLI (`ordia:*`)
- **L2** — quality gates (`quality:*`)
- **L3** — domain/dev scripts (`dev:*`, `db:*`, `docker:*`, `tunnel:*`)

Machine catalog: [commands.catalog.json](./commands.catalog.json) · npm scripts: [package.json](../../package.json).

## L1 — Ordia core

| Script | Command |
|--------|---------|
| `ordia:validate` | `ordia validate --project` |
| `ordia:doctor` | `ordia doctor` |
| `ordia:task-summary` | `ordia task summary` |
| `ordia:prompt-recover` | `ordia prompt emit --intent recover` |

## L2 — Quality

| Script | Command |
|--------|---------|
| `quality:lint` | `eslint .` (stub) |

## L3 — Domain (reference-demo)

| Script | Command |
|--------|---------|
| `dev:web` | Vite dev server (stub) |
| `dev:api` | API reload server (stub) |
| `db:migrate` | Apply migrations (stub) |
| `docker:up` | `docker compose up -d` (stub) |
| `tunnel:start` | Cloudflare tunnel (stub) |

Validate: `ordia validate --project` · sync catalog: `ordia init --sync-commands --skip-existing`.
