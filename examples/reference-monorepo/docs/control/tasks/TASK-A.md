# TASK-A

## Control

- Track: api-hardening
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths: apps/api/
- Status: IN_FLIGHT
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Harden the reference API stub with a stable health endpoint contract.

## Scope

- Allowed: apps/api/
- Blocked: apps/web/, docs/control/ (unless orchestration task)

## Parallel Safety and Locks

- Active lock: apps/api/ (TASK-A)
- Must not run in parallel with: TASK-B (non-overlapping — OK)

## Next Safe Action

agent-backend implements health response; report IMPLEMENTED when done.
