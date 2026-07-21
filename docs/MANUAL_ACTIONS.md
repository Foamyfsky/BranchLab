# Manual Actions

Codex must update this file after every round.

## Completed for Round 00

- [x] Create/open the repository from the starter pack.
- [x] Confirm Git is initialised.
- [x] Start the primary Codex session from the repository root.
- [x] Paste `prompts/ROUND_00_REPOSITORY_BOOTSTRAP.md`.
- [x] Keep the same primary Codex session for core implementation.
- [x] Place existing TfNSW data locally under `data/raw/tfnsw/`.

## Required before Round 01

- [ ] Review the Round 00 file structure and confirm it opens correctly.
- [ ] Confirm no real API key or real `.env.local` file is present in Git.
- [ ] Confirm the repository root is opened as the Obsidian vault, not the nested starter pack.
- [ ] Commit the completed Round 00 bootstrap.
- [ ] Confirm the working tree is clean before starting Round 01.

## API configuration

- [ ] Do not create `apps/web/.env.local` until you are ready to configure local runtime secrets.
- [ ] When needed, create `apps/web/.env.local` manually from `apps/web/.env.local.example`.
- [ ] Add the real `OPENAI_API_KEY` only in `apps/web/.env.local`.
- [ ] Keep `BRANCHLAB_AI_MODE=mock` until Round 08 is ready for live GPT integration.
- [ ] Never paste the key into Codex chat, Markdown, screenshots, Git, or client-side variables.
- [ ] Ensure API billing/credits are available before Round 08.

## Data preparation for Round 02

- [ ] Keep `data/raw/tfnsw/**` local and untracked.
- [ ] Decide whether to keep or add an original GTFS ZIP at `data/raw/tfnsw/complete_gtfs.zip`.
- [ ] During Round 02, confirm calendar coverage before choosing a demonstration date.
- [ ] During Round 02, review importer-generated candidate subsets and choose the final Sydney Pulse subset.

## Later submission work

- [ ] Create or connect the GitHub repository.
- [ ] Decide public/private sharing according to event rules.
- [ ] Add licence and data attribution.
- [ ] Create deployment account/project.
- [ ] Rehearse the exact demonstration scenario.
- [ ] Run `/feedback` in the primary Codex session and save the session ID.
- [ ] Record and upload the public demo video.
