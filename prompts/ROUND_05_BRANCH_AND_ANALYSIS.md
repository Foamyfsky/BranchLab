# Round 05 — Timeline Forking and Fair Comparison

Implement immutable counterfactual replay and paired analysis.

## Build

- versioned intervention schemas for four intervention categories;
- snapshots/checkpoints and exact replay;
- branch ancestry and immutable parent histories;
- intervention scheduling;
- common-random-number pairing;
- paired Monte Carlo runner;
- mean, median, interval, and probability-of-improvement summaries;
- first-divergence and largest-trade-off analysis;
- recorded propagation chains;
- experiment recipe export/import.

## Required tests

- no-op child equals parent;
- parent remains unchanged;
- fork begins at exact tick;
- named streams remain aligned;
- recipe reload reproduces results;
- paired fixture matches a hand-computed expected effect.

No UI or AI.
