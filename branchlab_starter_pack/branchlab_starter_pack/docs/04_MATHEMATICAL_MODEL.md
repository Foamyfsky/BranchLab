# Scientific Model

## Core formulation

BranchLab is a controlled discrete-time stochastic state-space model on a finite-capacity transit
network.

`X(t + Δ) = Fθ(X(t), U(t), ε(t))`

- `X`: queues, station occupancy, vehicles, onboard cohorts, service state, delays, latent demand
  regime, and network availability.
- `U`: user intervention.
- `ε`: exogenous named random streams.
- `θ`: documented parameters and calibrated distributions.
- `Δ`: logical simulation tick.

## Fork semantics

At fork tick `tf`:

- parent and child begin from the identical state;
- parent remains immutable;
- common exogenous random streams remain aligned;
- only explicit intervention mechanisms differ.

A no-op branch must therefore reproduce its parent exactly after `tf`.

## Demand

Use a Markov-modulated Poisson process (MMPP).

Demand regime:

`Zt ∈ {quiet, normal, buildup, surge, decay}`

`P(Z(t+Δ)=j | Z(t)=i) = Pij`

Conditional arrivals:

`A(i,d,t) | Zt=z ~ Poisson(λ(i,d,z,t) Δ)`

where the intensity can combine base station rate, time profile, regime multiplier, and destination
share.

## Bayesian calibration

Arrival intensity prior and update:

- `λi ~ Gamma(ai, bi)`
- `Ni | λi ~ Poisson(λi T)`
- posterior `λi | Ni ~ Gamma(ai + Ni, bi + T)`

Destination shares:

- `πi ~ Dirichlet(αi)`
- destination cohort `D ~ Categorical(πi)`

When no observations exist, initialise destination prior through a gravity-style cost model and mark
it synthetic.

## Route choice

Generate a small route-choice set and use a multinomial logit model:

`Cr = ride_time + ww*wait_time + wx*transfers + wc*crowding + wd*delay`

`P(r) = exp(-θ Cr) / Σk exp(-θ Ck)`

Guidance interventions alter perceived cost rather than moving passengers directly.

## Queue conservation

For station and destination cohort:

`Q(t+Δ) = Q(t) + arrivals + transfers_in - boarded - abandoned`

Global passenger accounting must satisfy:

`initial + generated = waiting + onboard + completed + abandoned`

## Boarding

`boarded = min(eligible_queue, free_vehicle_capacity, station_throughput * Δ)`

## Dwell and delay propagation

A practical dwell model:

`dwell = base + α*boardings + β*alightings + γ*(occupancy/capacity)^2 + noise`

Downstream delay:

`delay(k+1) = ρ*delay(k) + dwell_overrun(k) + operational_noise(k)`

## Crowd-pressure index

Use a clearly labelled scenario index:

`pressure = (station_occupancy / nominal_capacity)^2`

It is not an engineering safety certification.

## Fair stochastic comparison

Use paired Monte Carlo with common random numbers.

For replication `n`:

`Δn = metric_branch(εn) - metric_baseline(εn)`

Report:

- representative trajectory;
- mean and median paired effect;
- uncertainty interval;
- probability of improvement;
- main adverse trade-off.

## Causal explanation

Do not add a generic Bayesian-network library only for appearance. Record typed simulator events and
render the dependency chain:

event → demand regime → arrivals → queue → dwell → delay → downstream headway → downstream queue.

GPT-5.6 may verbalise this recorded chain but cannot invent causal edges or values.

## Required scientific tests

- deterministic replay;
- no-op fork equivalence;
- branch immutability;
- named random-stream alignment;
- passenger conservation at every tick;
- zero-demand sanity;
- zero-capacity sanity;
- monotonic local capacity sanity under controlled conditions;
- known small-network route-choice cases;
- posterior update against analytic Gamma-Poisson result;
- paired comparison against a hand-computed fixture;
- units and range validation for every parameter.
