# Tech Stack Lock

Round 00 intentionally uses a plain pnpm workspace, not Turborepo.

## Runtime and package manager

- Node.js: CI uses Node.js 22.
- Local Round 00 validation ran on Node.js v24.15.0.
- Package manager: pnpm 11.9.0.
- Workspace layout: `apps/*` and `packages/*`.

## Application

- `apps/web`: Next.js TypeScript app shell.
- Rendering libraries such as MapLibre and deck.gl are deferred to later rounds.
- OpenAI integration is deferred to Round 08 and must remain server-side.

## Tooling

- TypeScript for app and package type checking.
- ESLint flat config for repository linting.
- Prettier for formatting.
- Vitest for unit tests.
- GitHub Actions CI for install, format check, lint, typecheck, tests, and build.

## Dependency versions

Exact resolved versions are locked by `pnpm-lock.yaml`.

Root dev dependencies:

| Package                    | Resolved version |
| -------------------------- | ---------------: |
| `@eslint/js`               |           9.39.5 |
| `@next/eslint-plugin-next` |          15.5.20 |
| `@types/node`              |          22.20.1 |
| `eslint`                   |           9.39.5 |
| `eslint-config-prettier`   |           10.1.8 |
| `globals`                  |          15.15.0 |
| `prettier`                 |            3.9.5 |
| `typescript`               |            5.9.3 |
| `typescript-eslint`        |           8.64.0 |
| `vitest`                   |            3.2.7 |

Web app dependencies:

| Package            | Resolved version |
| ------------------ | ---------------: |
| `next`             |          15.5.20 |
| `react`            |           19.2.7 |
| `react-dom`        |           19.2.7 |
| `@types/react`     |          19.2.17 |
| `@types/react-dom` |           19.2.3 |

pnpm build-script approvals are recorded for:

- `esbuild`
- `sharp`
