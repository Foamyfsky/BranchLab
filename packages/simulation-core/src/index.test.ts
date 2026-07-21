import { describe, expect, it } from "vitest";

import { createMetroPulseWorld } from "@branchlab/reference-world";
import type { World } from "@branchlab/schemas";
import { WorldSchema } from "@branchlab/schemas";

import {
  assertPassengerConservation,
  createInitialState,
  deterministicUniform,
  restoreState,
  runSimulation,
  sampleDelayTicks,
  serializeState,
  stepSimulation,
} from "./index";

function withSeed(seed: string): World {
  return createMetroPulseWorld({ seed });
}

function withZeroDemand(world: World): World {
  return {
    ...world,
    stations: world.stations.map((station) => ({
      ...station,
      demand: {
        ...station.demand,
        arrivalRatePassengersPerTick: 0,
      },
    })),
  };
}

function withVehicleCapacity(world: World, vehicleCapacityPassengers: number): World {
  return {
    ...world,
    services: world.services.map((service) => ({
      ...service,
      vehicleCapacityPassengers,
    })),
  };
}

describe("deterministic reference simulation", () => {
  it("produces identical serialised results for the same seed and inputs", () => {
    const world = withSeed("same-seed");

    expect(serializeState(runSimulation(world, 24))).toBe(serializeState(runSimulation(world, 24)));
  });

  it("changes arrival outcomes for different seeds", () => {
    const left = runSimulation(withSeed("left-seed"), 18);
    const right = runSimulation(withSeed("right-seed"), 18);

    expect(left.metrics.generatedPassengers).not.toBe(right.metrics.generatedPassengers);
  });

  it("keeps arrival and delay random streams isolated from call order", () => {
    const seed = "stream-seed";
    const arrivalBeforeDelay = deterministicUniform(seed, "arrival", 8, "north-gate");
    const delayNoise = sampleDelayTicks(seed, 8, "north-gate");
    const arrivalAfterDelay = deterministicUniform(seed, "arrival", 8, "north-gate");

    expect(arrivalAfterDelay).toBe(arrivalBeforeDelay);
    expect(deterministicUniform(seed, "delay", 8, "north-gate")).not.toBe(arrivalBeforeDelay);
    expect(delayNoise).toBeGreaterThanOrEqual(0);
  });

  it("does not depend on wall-clock time", () => {
    const world = withSeed("wall-clock-seed");
    const originalNow = Date.now;

    Date.now = () => 10;
    const first = serializeState(runSimulation(world, 12));

    Date.now = () => 999_999;
    const second = serializeState(runSimulation(world, 12));

    Date.now = originalNow;

    expect(second).toBe(first);
  });

  it("preserves passenger conservation at every tick", () => {
    const world = withSeed("conservation-seed");
    let state = createInitialState(world);

    for (let tick = 0; tick < 40; tick += 1) {
      state = stepSimulation(world, state);
      assertPassengerConservation(state);
    }
  });

  it("generates no passengers when demand is zero", () => {
    const state = runSimulation(withZeroDemand(withSeed("zero-demand-seed")), 20);

    expect(state.metrics.generatedPassengers).toBe(0);
    expect(state.metrics.waitingPassengers).toBe(0);
    expect(state.metrics.onboardPassengers).toBe(0);
    expect(state.metrics.completedPassengers).toBe(0);
  });

  it("boards no passengers when vehicle capacity is zero", () => {
    const state = runSimulation(withVehicleCapacity(withSeed("zero-capacity-seed"), 0), 20);

    expect(state.metrics.generatedPassengers).toBeGreaterThan(0);
    expect(state.metrics.boardedPassengers).toBe(0);
    expect(state.metrics.completedPassengers).toBe(0);
    expect(state.metrics.waitingPassengers).toBe(state.metrics.generatedPassengers);
  });

  it("restores a snapshot and reproduces uninterrupted execution", () => {
    const world = withSeed("snapshot-seed");
    const uninterrupted = runSimulation(world, 30);
    const midpoint = runSimulation(world, 12);
    const restored = restoreState(serializeState(midpoint));
    const continued = runSimulation(world, 18, restored);

    expect(serializeState(continued)).toBe(serializeState(uninterrupted));
  });

  it("matches a parent future for a no-op child restored at the fork tick", () => {
    const world = withSeed("noop-fork-seed");
    const forkState = runSimulation(world, 10);
    const parentFuture = runSimulation(world, 16, forkState);
    const childFuture = runSimulation(world, 16, restoreState(serializeState(forkState)));

    expect(serializeState(childFuture)).toBe(serializeState(parentFuture));
  });

  it("keeps the Metro Pulse reference world schema-valid", () => {
    expect(WorldSchema.parse(createMetroPulseWorld()).stations).toHaveLength(8);
  });
});
