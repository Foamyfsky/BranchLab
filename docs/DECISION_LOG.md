# Decision Log

| Date       | Decision                                                                | Reason                                                                                         | Status   |
| ---------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------- |
| Initial    | Use the repository itself as the Obsidian vault                         | Prevent planning/code divergence                                                               | Accepted |
| Initial    | Build a reference world before real GTFS integration                    | Isolate scientific and branch invariants from messy data                                       | Accepted |
| Initial    | Use MapLibre + deck.gl rather than a custom 3D engine first             | Best balance of real geography, 3D appearance, and execution risk                              | Accepted |
| Initial    | Treat Sydney Pulse as scenario analysis, not prediction                 | Real supply data does not imply real demand or validated forecasting                           | Accepted |
| 2026-07-21 | Promote starter pack contents to repository root                        | The repository itself is the Obsidian vault and source of truth                                | Accepted |
| 2026-07-21 | Use a plain pnpm workspace for Round 00                                 | Matches architecture docs without adding Turborepo before it is needed                         | Accepted |
| 2026-07-21 | Create only `apps/web/.env.local.example` in Round 00                   | Keeps secrets out of Git and preserves mock-AI mode without an OpenAI key                      | Accepted |
| 2026-07-21 | Ignore and untrack `data/raw/**`                                        | Raw TfNSW files are too large for Git and must not enter tooling or bundles                    | Accepted |
| 2026-07-21 | Treat station entry/exit data as calibration material                   | The file is monthly entry/exit data, not realtime demand                                       | Accepted |
| 2026-07-21 | Require Round 02 `GtfsSource` abstraction for directories and ZIP files | The local feed is already extracted, while the importer must also support original ZIP sources | Accepted |
| 2026-07-21 | Require a committed, clean Round 00 tree before Round 01                | Keeps repository bootstrap separate from deterministic engine implementation                   | Accepted |
| 2026-07-22 | Use stateless hash-based named random streams for Round 01              | Arrival and delay randomness must not depend on mutable call order                             | Accepted |
| 2026-07-22 | Keep Round 01 passenger behavior aggregate and terminal-completion only | Proves determinism, capacity, boarding, and conservation without full route choice             | Accepted |
| 2026-07-22 | Model Metro Pulse as a fictional eight-station two-service fixture      | Gives a small transfer network without depending on TfNSW or choosing the Sydney subset        | Accepted |
| 2026-07-22 | Prove no-op fork by snapshot restore and identical continuation         | Exercises the required fork invariant without implementing the full branch system              | Accepted |
