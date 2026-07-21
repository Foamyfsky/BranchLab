# Round 01 Report

## Status

PASS

## Goal completed

Round 01 created a deterministic, inspectable reference-world vertical slice for BranchLab.

## Files created or changed

- `packages/schemas/package.json`
- `packages/schemas/src/index.ts`
- `packages/schemas/src/index.test.ts`
- `packages/reference-world/package.json`
- `packages/reference-world/src/index.ts`
- `packages/simulation-core/package.json`
- `packages/simulation-core/src/index.ts`
- `packages/simulation-core/src/index.test.ts`
- `vitest.config.ts`
- `pnpm-lock.yaml`
- `docs/PROJECT_STATE.md`
- `docs/PROGRESS.md`
- `docs/MANUAL_ACTIONS.md`
- `docs/DECISION_LOG.md`
- `docs/round-reports/ROUND_01.md`

## Important decisions

- Added `zod` for the shared versioned schema package.
- Used stateless FNV-1a hash-derived random values keyed by seed, stream, tick, entity, and draw
  index.
- Kept passenger behavior aggregate and minimal: generated demand, station queues, scheduled
  vehicles, finite capacity, boarding, terminal completion, and conservation accounting.
- Proved no-op fork behavior with snapshot restore and identical future states, without implementing
  branch ancestry or interventions.

## Commands run

- `CI=1 pnpm install --no-frozen-lockfile`
- `CI=1 .\node_modules\.bin\vitest.cmd run packages/schemas/src/index.test.ts packages/simulation-core/src/index.test.ts`
- `tsc --noEmit -p packages/schemas/tsconfig.json`
- `tsc --noEmit -p packages/reference-world/tsconfig.json`
- `tsc --noEmit -p packages/simulation-core/tsconfig.json`
- `CI=1 pnpm lint`
- `CI=1 pnpm typecheck`
- `CI=1 pnpm test`

## Lint/typecheck/test results

- Targeted tests: 13 passed.
- Affected package typechecks: passed.
- Root lint: passed.
- Root typecheck: passed.
- Root test: passed.

## Manual actions required from Robert

- Review and commit Round 01.
- Confirm the working tree is clean before Round 02.
- Decide whether Round 02 should smoke test only the extracted TfNSW directory first or also require
  `data/raw/tfnsw/complete_gtfs.zip`.

## Data or credentials still required

- No OpenAI key is required.
- Raw TfNSW data remains local and untracked.
- A GTFS ZIP is optional for Round 02 ZIP-source smoke testing.

## Known limitations and risks

- Metro Pulse is deliberately fictional and synthetic.
- Passenger behavior is minimal and terminal-completion only.
- There is no route choice, Bayesian calibration, GTFS import, map rendering, intervention system,
  or OpenAI integration.

## Exact prerequisites for the next round

Commit Round 01 and confirm `git status --short` is clean.

## Suggested next prompt

Begin Round 02. Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `docs/03_DATA_PLAN.md`,
`docs/06_MILESTONES_AND_GATES.md`, and `prompts/ROUND_02_GTFS_IMPORTER.md`. Implement the generic
GTFS importer with a shared `GtfsSource` abstraction for extracted directories and ZIP files, using
small generated fixtures before any real TfNSW smoke test.
