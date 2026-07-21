# Project State

## Current milestone

Round 00 - Repository bootstrap is complete and awaiting Robert's review and commit.

## Completed structure

- Root documentation and prompts live at `AGENTS.md`, `00_START_HERE.md`, `docs/`, and `prompts/`.
- pnpm workspace covers `apps/*` and `packages/*`.
- Next.js TypeScript shell exists at `apps/web`.
- Workspace packages exist at:
  - `packages/schemas`
  - `packages/simulation-core`
  - `packages/metro-model`
  - `packages/gtfs-importer`
  - `packages/experiment-analysis`
  - `packages/reference-world`
- Tooling exists for TypeScript, ESLint, Prettier, Vitest, root scripts, and CI.
- Placeholder env template exists at `apps/web/.env.local.example`.
- `data/raw/**`, real env files, `.obsidian/`, and the promoted starter archive are ignored.
- Lightweight data inventory exists at `scripts/data-inventory.mjs`.

## Commands known to pass

- `pnpm install`
- `pnpm format`
- `pnpm format:check`
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `CI=1 pnpm build`
- `pnpm data:inventory data/raw/tfnsw`

## Manual actions required

- Review the Round 00 structure.
- Confirm no real API key or real `.env.local` is present in Git.
- Open the repository root as the Obsidian vault.
- Commit Round 00.
- Confirm the working tree is clean before beginning Round 01.
- Keep `BRANCHLAB_AI_MODE=mock` until live GPT integration is intentionally enabled in Round 08.

## Unresolved decisions

- Final Sydney Pulse subset.
- Demonstration date, pending static feed calendar coverage.
- Whether to keep or add the original GTFS ZIP at `data/raw/tfnsw/complete_gtfs.zip`.
- Event location and challenge thresholds.
- Later deployment, licence, and data attribution details.

## Exact next milestone

Round 01 - Deterministic reference world. Begin only after Round 00 is committed and the working tree
is clean.
