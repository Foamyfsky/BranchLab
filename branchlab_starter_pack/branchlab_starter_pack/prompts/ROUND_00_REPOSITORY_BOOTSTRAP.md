# Round 00 — Repository Bootstrap

Read `AGENTS.md`, all documents under `docs/`, and `00_START_HERE.md`.

We currently have planning files but no implemented application. Bootstrap the BranchLab repository
without implementing simulation features.

## Build

- Initialise a pnpm workspace.
- Create the package directories defined in `docs/02_SYSTEM_ARCHITECTURE.md`.
- Create a Next.js TypeScript app at `apps/web`.
- Configure TypeScript project references or a simple workspace arrangement that keeps package
  boundaries clear.
- Configure formatting, ESLint, Vitest, and root scripts for format, lint, typecheck, test, and build.
- Add minimal package READMEs that state ownership and forbidden dependencies.
- Ensure `.env.example` is usable and secrets remain ignored.
- Add a minimal CI workflow that runs install, lint, typecheck, tests, and build.
- Preserve the supplied visual references and planning documents.
- Add a basic landing page that says BranchLab is under construction, but do not build the lab UI.
- Create `docs/TECH_STACK_LOCK.md` recording exact package choices and versions.

## Do not build

- simulation rules;
- GTFS parsing;
- map rendering;
- branch UI;
- OpenAI calls;
- a database or authentication.

## Acceptance

- clean install succeeds;
- root scripts work;
- one trivial unit test proves the test runner works;
- web app builds;
- no secret or raw data is tracked;
- package boundaries match the architecture.

Follow the end-of-round reporting protocol and stop after the gate passes.
