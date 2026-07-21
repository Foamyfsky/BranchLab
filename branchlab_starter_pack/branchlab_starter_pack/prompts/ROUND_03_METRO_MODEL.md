# Round 03 — Scientific Metro Kernel

Implement the mathematical model in `docs/04_MATHEMATICAL_MODEL.md` on the reference world.

## Build

- units and parameter metadata;
- latent Markov demand regime;
- deterministic Poisson sampling through named streams;
- Gamma-Poisson demand parameter representation and analytic update;
- Dirichlet destination priors;
- route-set generation and multinomial-logit selection;
- aggregate passenger cohorts;
- queues, boarding, alighting, completion, and abandonment accounting;
- capacity-constrained vehicles and station throughput;
- dwell and downstream delay propagation;
- crowd-pressure index;
- typed simulator events for Math Lens and Causal Lens;
- metrics and conservation diagnostics.

## Required tests

Implement every test listed in the scientific-model document, including analytic posterior and
passenger conservation checks.

Do not add branches, map rendering, or OpenAI integration.
