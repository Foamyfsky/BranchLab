# Progress

## Current round

Round 00 - complete.

## Completed

- Product concept and architecture refined.
- Starter planning pack created.
- Visual references collected.
- Starter planning docs and prompts promoted to the repository root.
- Plain pnpm workspace created for `apps/*` and `packages/*`.
- Minimal Next.js TypeScript app shell created at `apps/web`.
- Workspace package boundaries created for schemas, simulation core, metro model, GTFS importer,
  experiment analysis, and reference world.
- TypeScript, ESLint, Prettier, Vitest, root scripts, lockfile, and CI created.
- `apps/web/.env.local.example` created with placeholders only.
- Real environment files and `data/raw/**` are ignored.
- Previously tracked raw TfNSW files, Obsidian local state, and the nested starter archive were
  removed from the Git index while remaining on disk.
- Lightweight data inventory script added at `scripts/data-inventory.mjs`.
- Current TfNSW static feed presence and header-only inventory recorded in `docs/DATA_INVENTORY.md`.
- Round 02 prompt updated to require a shared `GtfsSource` abstraction for extracted directories and
  ZIP files.
- Round 00 validation passed: install, format check, lint, typecheck, tests, build, and data
  inventory.
- Round 00 closeout completed after rerunning the missing production build gate with `CI=1`.

## Current blockers

- No Round 01 blocker is known.
- Round 00 still needs to be reviewed, committed, and left with a clean working tree before Round 01
  begins.
- Final Sydney subset intentionally remains undecided until the GTFS importer produces candidate
  reports.
- Demonstration date remains undecided until calendar coverage is checked.

## Next gate

Commit Round 00, confirm a clean working tree, then run Round 01 deterministic reference world.
