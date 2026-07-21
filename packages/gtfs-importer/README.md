# `@branchlab/gtfs-importer`

## Ownership

Owns future GTFS source loading, validation, service-date filtering, platform grouping, directed
graph creation, shape/schedule extraction, candidate-subset reports, provenance, and world-pack
export.

## Forbidden dependencies

- No React, Next.js, MapLibre, deck.gl, or browser UI code.
- No OpenAI SDK or generated intervention logic.
- No passenger simulation or demand modelling.
- Do not load large GTFS files fully into memory when streaming or indexed reads are required.
