# Decision Log

| ID | State | Date | Decision | Rationale |
|---|---|---|---|---|
| REF-DEMO-D001 | ACCEPTED | 2026-06-10 | Adopt Ordia with profile `reference-demo` | Brownfield monorepo needs durable parallel orchestration |
| REF-DEMO-D002 | ACCEPTED | 2026-06-12 | Split in-flight work across `apps/api/` and `apps/web/` | Non-overlapping scopes enable safe MULTI_CHAT parallelism |
