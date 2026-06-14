# Ordia reference monorepo (0.18.0)

Self-contained fixture demonstrating **brownfield adoption**, **parallel in-flight tasks**, and an **L1/L2/L3 command catalog** for a small `apps/` monorepo.

Target Ordia release: **0.18.0** · profile: **`reference-demo`**

## What this example shows

| Theme | Where to look |
|-------|----------------|
| **Adoption** | `docs/control/adoption.checklist.yaml` — partial progress after `ordia adopt` |
| **Parallel tasks** | `TASK_REGISTRY.yaml` — `TASK-A` + `TASK-B` in `queues.in_flight` with `active_locks` |
| **L3 catalog** | `package.json` scripts + `docs/control/commands.catalog.json` (`dev`, `db`, `docker`, `tunnel`) |

## Layout

```text
examples/reference-monorepo/
├── ordia.yaml              # monorepo manifest (productRoots: apps/)
├── AGENTS.md               # agent bootstrap
├── package.json            # L3 npm scripts
├── apps/
│   ├── api/main.py         # backend stub
│   └── web/App.tsx         # frontend stub
└── docs/control/           # coordination store
```

## Quick start

```powershell
cd examples/reference-monorepo
pip install "ordia-core>=0.18.0"

ordia validate --project
ordia task summary
ordia prompt emit --intent orchestrate_parallel --task TASK-B
npm run ordia:validate
```

## Adoption walkthrough

1. **Audit** — `ordia docs audit --write-report` (see checklist step `audit`)
2. **Scaffold** — `ordia init --skip-existing --with-cursor --profile reference-demo`
3. **Sync commands** — `ordia init --sync-commands --skip-existing` seeds L3 sections from `package.json`
4. **Validate** — `ordia validate --project` before change-capable work

Checklist state in this fixture: scaffold and command sync are **completed**; final validate/doctor gates remain **pending** (intentional teaching state).

## Parallel orchestration

Two agents work concurrently without path collision:

- **TASK-A** (`agent-backend`) → `apps/api/` lock
- **TASK-B** (`agent-frontend`) → `apps/web/` lock

Emit a parallel safety prompt:

```powershell
ordia prompt emit --intent orchestrate_parallel --task TASK-B
```

## Command catalog layers

| Layer | Examples in this repo |
|-------|------------------------|
| **L1** | `ordia:validate`, `ordia:doctor`, `ordia:task-summary` |
| **L2** | `quality:lint` |
| **L3** | `dev:web`, `dev:api`, `db:migrate`, `docker:up`, `tunnel:start` |

Human-readable overlay: `docs/control/COMMANDS.md` · machine catalog: `docs/control/commands.catalog.json`.

## Related examples

- [greenfield](../greenfield/README.md) — minimal post-init snapshot
- [brownfield-adoption](../brownfield-adoption/README.md) — adopt into an existing repo
- [project-commands](../project-commands/README.md) — `sync-commands` seeding only
