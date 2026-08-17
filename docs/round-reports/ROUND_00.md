# Round 00 Report

## Status

PASS

## Completed

- Promoted starter docs and prompts to the repository root.
- Created a pnpm workspace with `apps/web` and the six intended package boundaries.
- Added a minimal Next.js TypeScript app shell and placeholder env example.
- Configured TypeScript, ESLint, Prettier, Vitest, root scripts, lockfile, and CI.
- Added package README ownership and forbidden-dependency notes.
- Added lightweight data inventory that reads names, sizes, and headers only.
- Ignored and untracked raw TfNSW data, Obsidian local state, and the nested starter archive.
- Updated Round 02 planning for a shared extracted-directory/ZIP `GtfsSource` abstraction.

## Files changed

- Root workspace/tooling files.
- `apps/web/**`.
- `packages/**`.
- `scripts/data-inventory.mjs`.
- `docs/**`.
- `prompts/ROUND_02_GTFS_IMPORTER.md`.

## Validation

- `pnpm install` passed.
- `pnpm format` passed.
- `pnpm format:check` passed.
- `pnpm lint` passed.
- `pnpm typecheck` passed.
- `pnpm test` passed.
- `CI=1 pnpm build` passed.
- `pnpm data:inventory data/raw/tfnsw` passed.

## Manual actions for Skylar

- Review and commit Round 00.
- Confirm the working tree is clean before Round 01.
- Do not add `apps/web/.env.local` to Git.
- Keep local raw TfNSW data under `data/raw/tfnsw/**`.

## Known limitations

- The web app is a placeholder only.
- No simulation, GTFS parsing, branch logic, map rendering, OpenAI calls, database, or authentication
  exists yet.
- Next.js build emits a non-blocking ESLint-plugin detection warning despite the explicit root lint
  gate passing.

## Next-round prerequisites

Round 01 may begin after Round 00 is committed and `git status --short` is clean.
