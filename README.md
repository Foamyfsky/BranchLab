# BranchLab

BranchLab is an educational scenario-analysis environment for deterministic counterfactual
experiments on a curated transit network.

Round 00 provides the repository shell only: workspace packages, tooling, documentation, CI, and a
minimal Next.js placeholder app. It does not implement GTFS parsing, simulation, branch logic, map
rendering, OpenAI calls, authentication, or persistence.

## Local checks

```bash
pnpm install
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

## Data and secrets

- Raw source data belongs under `data/raw/` and is ignored by Git.
- Real environment files such as `apps/web/.env.local` are ignored by Git.
- Use `apps/web/.env.local.example` as the placeholder template.
