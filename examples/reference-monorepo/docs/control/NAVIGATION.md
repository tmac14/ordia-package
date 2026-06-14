# Control plane navigation

Profile: **reference-demo** · Ordia **0.18.0** reference monorepo.

This map links every coordination artifact. Resolve `{controlRoot}` from `ordia.yaml` → `control.root` (default: `docs/control/`).

---

## Quick start

| Step | Action |
|------|--------|
| 1 | Read [AGENTS.md](../../AGENTS.md) — declare Runtime + Protocol |
| 2 | Read [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md) §0 — live session |
| 3 | Read [PROFILE.md](./PROFILE.md) — agents and guardrails |
| 4 | Run `ordia validate --project` before change-capable work |

**Brownfield:** see [adoption.checklist.yaml](./adoption.checklist.yaml) after `ordia adopt`.

---

## Core artifacts

| Document | Purpose |
|----------|---------|
| [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md) | Live runtime, protocol, active task, recovery |
| [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml) | Tasks, queues, locks, in-flight |
| [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml) | Parallel agent topology and scopes |
| [PROFILE.md](./PROFILE.md) | Domain profile, tracks, guardrails |
| [COMMANDS.md](./COMMANDS.md) | L2/L3 project commands overlay |
| [commands.catalog.json](./commands.catalog.json) | Machine-readable command catalog |

---

## Governance and evidence

| Document | Purpose |
|----------|---------|
| [DECISION_LOG.md](./DECISION_LOG.md) | Material decisions |
| [EVIDENCE_INDEX.md](./EVIDENCE_INDEX.md) | QA and validation evidence |
| [DOCUMENTATION_INVENTORY.yaml](./DOCUMENTATION_INVENTORY.yaml) | Machine-readable inventory |
| [adoption.checklist.yaml](./adoption.checklist.yaml) | Brownfield adoption progress |

---

## Task packets

- Active packets: `tasks/TASK-A.md`, `tasks/TASK-B.md`

---

## CLI cheat sheet

```powershell
ordia task summary
ordia task lock list
ordia prompt emit --intent recover
ordia prompt emit --intent orchestrate_parallel --task TASK-B
ordia validate --project
ordia doctor
npm run dev:web
npm run ordia:validate
```
