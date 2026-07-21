# Round 02 — Generic GTFS Importer

Read the data plan and confirm whether `data/raw/tfnsw/complete_gtfs.zip` exists.

First implement against small generated GTFS fixtures. If the TfNSW ZIP is absent, complete all code
and tests possible, update `docs/MANUAL_ACTIONS.md`, and report BLOCKED only for the real-feed smoke
test.

## Build

- CLI arguments: input ZIP, service date, time range, optional bounds/routes, output directory;
- parse required and optional GTFS files;
- validate references and times;
- resolve active service;
- group platforms through `parent_station` where available;
- build directed station/service edges;
- attach route shapes;
- derive trip and headway summaries;
- deterministic world-pack export with provenance;
- candidate-subset report ranking transfer-centred compact subgraphs;
- fixture generator and importer tests.

## Real-feed smoke test

When the ZIP is present:

- inspect, do not commit it;
- generate candidate subsets;
- do not choose the final subset without Robert;
- report exact candidates, station counts, routes, bounds, service frequency, and reasons.

Do not implement passenger simulation or map UI.
