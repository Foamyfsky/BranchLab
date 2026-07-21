# Round 08 — GPT-5.6 Integration

Before implementation, verify `apps/web/.env.local` exists locally and never print the key.

Use the official OpenAI JavaScript SDK and the Responses API. Use Zod-based Structured Outputs.

## Build

- server-only OpenAI client;
- environment-configurable model;
- natural-language to typed intervention proposal;
- explicit unsupported/ambiguous result shape;
- code validation, bounds checking, and user confirmation;
- grounded divergence explanation using only computed evidence;
- one suggested next experiment;
- mock mode and deterministic fixtures;
- timeout, refusal, malformed-output, and unavailable-credit handling;
- basic request limits and minimal prompt/evidence payloads.

GPT must never calculate metrics, invent simulator events, or mutate the world directly.
