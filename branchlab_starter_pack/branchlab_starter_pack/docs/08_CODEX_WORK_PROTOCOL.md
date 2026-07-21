# Codex Work Protocol

## How to issue work

Use one milestone prompt at a time. Do not say “build the entire app.” Before coding, Codex must read:

1. `AGENTS.md`
2. `docs/00_PROJECT_CHARTER.md`
3. the relevant technical document;
4. `docs/PROGRESS.md`
5. `docs/MANUAL_ACTIONS.md`
6. the current round prompt.

## Required workflow inside each round

1. Inspect repository state and report contradictions.
2. Restate the round goal, non-goals, and acceptance tests.
3. Propose a short implementation plan.
4. Implement only the round.
5. Run formatting, linting, type checking, unit tests, and targeted smoke tests.
6. Fix failures rather than merely reporting them.
7. Update progress, manual actions, and decision log.
8. Stop at the acceptance gate and return the standard report.

## Never allow silent scope expansion

Codex must ask before:

- changing a core mathematical assumption;
- replacing the chosen map/simulation architecture;
- adding a database, auth system, new framework, or cloud service;
- selecting the final Sydney subset;
- weakening a scientific invariant;
- introducing a paid service;
- copying copyrighted visual assets into production.

## Commit discipline

After a round passes:

- review the diff;
- create one descriptive Git commit;
- tag important demo checkpoints if useful;
- do not mix unrelated visual refactors into scientific-kernel commits.

Suggested commit pattern:

- `chore: bootstrap branchlab workspace`
- `feat(sim): add deterministic reference world`
- `feat(import): add validated gtfs world importer`
- `feat(model): add stochastic metro simulation`
- `feat(branch): add immutable counterfactual replay`
- `feat(ui): add living city renderer`
- `feat(ai): add structured gpt intervention parsing`

## End-of-round response template

```markdown
# Round NN Report

## Status
PASS | PARTIAL | BLOCKED

## Completed

## Files changed

## Design and scientific decisions

## Commands and validation
- install:
- format:
- lint:
- typecheck:
- tests:
- smoke test:

## Manual actions for Robert

## Data/credentials needed

## Known limitations

## Next-round prerequisites

## Suggested next prompt
```
