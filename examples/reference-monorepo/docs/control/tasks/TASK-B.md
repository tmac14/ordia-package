# TASK-B

## Control

- Track: web-shell
- Owner: agent-frontend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths: apps/web/
- Status: IN_FLIGHT
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Deliver a minimal web shell that identifies the reference-demo profile.

## Scope

- Allowed: apps/web/
- Blocked: apps/api/, docs/control/ (unless orchestration task)

## Parallel Safety and Locks

- Active lock: apps/web/ (TASK-B)
- Must not run in parallel with: TASK-A (non-overlapping — OK)

## Next Safe Action

agent-frontend updates App.tsx; report IMPLEMENTED when done.
