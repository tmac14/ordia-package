# AGENTS

Ordia bootstrap — read the project profile under the control store before change-capable work.

- Manifest: `ordia.yaml` — resolve **`{controlRoot}`** from `control.root`
- **Navigation map:** **`{controlRoot}/NAVIGATION.md`** — linked control-plane index
- Project profile: **`{controlRoot}/PROFILE.md`** (domain agents, guardrails, tracks)
- Control store: `docs/control/`
- Validate: `ordia validate --project` (optional npm wrapper: `npm run ordia:validate`)

Declare before change-capable work:

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
Ordia profile: reference-demo
```

Recovery bootstrap reads paths from the manifest. See `docs/ordia/SPEC_v0.2.md` for session API and lifecycle gates.

## Reference-demo topology

Six parallel implementation agents (see `docs/control/AGENT_REGISTRY.yaml`). Current in-flight work:

- **TASK-A** — `agent-backend` → `apps/api/`
- **TASK-B** — `agent-frontend` → `apps/web/`

Use `ordia task summary` and `ordia prompt emit --intent orchestrate_parallel` before spawning parallel executors.
