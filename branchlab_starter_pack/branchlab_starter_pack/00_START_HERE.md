# BranchLab — Start Here

BranchLab is a real-world network importer, scientifically transparent stochastic simulator,
causal timeline-forking interface, and futuristic 3D visual laboratory.

## The source-of-truth rule

Use this repository itself as the Obsidian vault. Keep product and scientific notes under`docs/`, and let Codex read those same tracked files. Add `.obsidian/` to `.gitignore`.
Do not maintain a separate copy of the specification in another vault because the two versions will diverge.

## First manual steps

1. Create a new Git repository from the contents of this starter pack.
2. Open the repository root as an Obsidian vault.
3. Put the OpenAI key in `apps/web/.env.local`, never in a Markdown file.
4. Start one primary Codex session from the repository root. Use that same session for the
   majority of the implementation and eventually run `/feedback` in it.
5. Give Codex `prompts/ROUND_00_REPOSITORY_BOOTSTRAP.md`.
6. Do not download the large TfNSW feed until Round 02 asks for it, unless you want to do it now.

## Intended build order

1. Freeze contracts and repository structure.
2. Build a tiny deterministic reference world.
3. Build and validate the generic GTFS importer.
4. Import and curate Sydney Pulse.
5. Implement the scientific demand and transport model.
6. Implement immutable timeline forks and paired comparisons.
7. Build the web shell and geographic 2.5D renderer.
8. Build the futuristic HUD and signature fork interaction.
9. Add GPT-5.6 through server-side structured outputs.
10. Validate, deploy, document, and record the demonstration.

The reference world is intentional. It lets the team test conservation, determinism, branching,
and mathematics before introducing a large and messy real-world dataset.
