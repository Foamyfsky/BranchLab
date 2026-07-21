# `@branchlab/schemas`

## Ownership

Owns versioned TypeScript/Zod contracts for worlds, stations, routes, services, interventions,
simulation events, branch recipes, exports, and future AI response objects.

## Forbidden dependencies

- No React, Next.js, MapLibre, deck.gl, or UI framework imports.
- No OpenAI SDK or direct API calls.
- No filesystem access to `data/raw/**`.
- No simulation algorithms beyond validation-friendly contract helpers.
