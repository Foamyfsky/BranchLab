# `@branchlab/web`

## Ownership

The web app owns the Next.js application shell, React UI, future MapLibre/deck.gl rendering, server
routes for validated AI proposals, mock AI mode, and import/export user workflows.

## Forbidden dependencies

- Do not import raw files from `data/raw/**`.
- Do not put API keys in client code or any `NEXT_PUBLIC_` variable.
- Do not make GPT or any AI route mutate simulation state directly.
- Do not place deterministic simulation mechanics in React components.
- Do not add databases, authentication, or paid services without an explicit later-round decision.
