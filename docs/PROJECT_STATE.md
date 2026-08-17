# Project State

## Current milestone

Round 01 - Deterministic reference world is complete and awaiting Skylar's review and commit.

## Completed structure

- Root documentation and prompts live at `AGENTS.md`, `00_START_HERE.md`, `docs/`, and `prompts/`.
- pnpm workspace covers `apps/*` and `packages/*`.
- Next.js TypeScript shell exists at `apps/web`.
- Versioned Zod schemas live in `packages/schemas`.
- Deterministic logical simulation primitives live in `packages/simulation-core`.
- The fictional eight-station Metro Pulse reference world lives in `packages/reference-world`.
- Placeholder package boundaries remain for `metro-model`, `gtfs-importer`, and `experiment-analysis`.
- Tooling exists for TypeScript, ESLint, Prettier, Vitest, root scripts, and CI.
- `data/raw/**`, real env files, `.obsidian/`, and the promoted starter archive are ignored.

## Commands known to pass

- `pnpm install`
- `pnpm format`
- `pnpm format:check`
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `CI=1 pnpm build`
- `pnpm data:inventory data/raw/tfnsw`
- `CI=1 .\node_modules\.bin\vitest.cmd run packages/schemas/src/index.test.ts packages/simulation-core/src/index.test.ts`
- `tsc --noEmit -p packages/schemas/tsconfig.json`
- `tsc --noEmit -p packages/reference-world/tsconfig.json`
- `tsc --noEmit -p packages/simulation-core/tsconfig.json`

## Manual actions required

- Review the Round 01 deterministic reference-world implementation.
- Commit Round 01.
- Confirm the working tree is clean before beginning Round 02.
- Keep `BRANCHLAB_AI_MODE=mock` until live GPT integration is intentionally enabled in Round 08.
- Keep raw TfNSW data local and untracked under `data/raw/tfnsw/**`.

## Unresolved decisions

- Final Sydney Pulse subset.
- Demonstration date, pending static feed calendar coverage.
- Whether to keep or add the original GTFS ZIP at `data/raw/tfnsw/complete_gtfs.zip`.
- Event location and challenge thresholds.
- Later deployment, licence, and data attribution details.

## Exact next milestone

Round 02 - Generic GTFS importer. Begin only after Round 01 is committed and the working tree is
clean.
