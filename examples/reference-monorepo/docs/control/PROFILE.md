# Control plane navigation — see [NAVIGATION.md](./NAVIGATION.md) for the full linked map.

Profile: reference-demo

## Agent topology

Six generic parallel roles (see [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)):

| Agent | Role | Typical scopes |
|-------|------|----------------|
| `agent-backend` | API / services | `apps/api/` |
| `agent-frontend` | UI components | `apps/web/` |
| `agent-data` | DB / migrations | `db/`, `migrations/` |
| `agent-infra` | Docker / CI / tunnel | `docker/`, `.github/` |
| `agent-qa` | QA read-only | `temp/qa/` |
| `agent-docs` | Docs / control | `docs/`, `docs/control/` |

**Mutual exclusion:** `agent-data` and `agent-infra` share group `infra-data` — do not run in-flight on overlapping paths.

## Domain guardrails

- Product code lives under `apps/` only (`enforcement.productRoots`).
- Control-plane edits require ORCHESTRATION protocol unless task owner is `agent-docs`.
- Parallel tasks must declare non-overlapping `planned_write_paths` and `active_locks`.

## Active tracks

| Track | Task | Owner | Scope |
|-------|------|-------|-------|
| api-hardening | TASK-A | agent-backend | `apps/api/` |
| web-shell | TASK-B | agent-frontend | `apps/web/` |

Next safe parallel spawn: `ordia prompt emit --intent orchestrate_parallel --task TASK-B`.
