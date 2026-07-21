# Manual Actions

Codex must update this file after every round.

## Required now

- [ ] Create/open the repository from this starter pack.
- [ ] Open the repository root as the Obsidian vault.
- [ ] Confirm Git is initialised.
- [ ] Start the primary Codex session from the repository root.
- [ ] Paste `prompts/ROUND_00_REPOSITORY_BOOTSTRAP.md`.
- [ ] Keep the same primary Codex session for core implementation.

## API configuration

- [ ] Create `apps/web/.env.local` only after Round 00 creates the web app.
- [ ] Add `OPENAI_API_KEY=...`.
- [ ] Add `OPENAI_MODEL=gpt-5.6`.
- [ ] Never paste the key into Codex chat, Markdown, screenshots, Git, or client-side variables.
- [ ] Ensure API billing/credits are available before Round 08.

## Data acquisition for Round 02

- [ ] Visit the official TfNSW Timetables Complete GTFS dataset page.
- [ ] Sign in if required.
- [ ] Download the current GTFS ZIP.
- [ ] Save it as `data/raw/tfnsw/complete_gtfs.zip`.
- [ ] Do not unzip manually unless the importer instructs it.
- [ ] Do not commit the ZIP.

## Decision required after Round 02

- [ ] Review the importer-generated candidate subsets.
- [ ] Choose one based on transfer structure, visual clarity, active scheduled trips, and event story.
- [ ] Confirm the final world name and event location.

## Visual work

- [ ] Keep the supplied reference images under `docs/references/`.
- [ ] Review Codex's extracted design tokens and moodboard notes.
- [ ] Approve camera pitch, visual density, and branch colours after the first renderer.
- [ ] Test on the machine used to record the demo.

## Submission work

- [ ] Create GitHub repository.
- [ ] Decide public/private sharing according to event rules.
- [ ] Add licence and data attribution.
- [ ] Create deployment account/project.
- [ ] Rehearse the exact demonstration scenario.
- [ ] Run `/feedback` in the primary Codex session and save the session ID.
- [ ] Record and upload the public demo video.
