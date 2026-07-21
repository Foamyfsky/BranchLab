import { describe, expect, it } from "vitest";

import { WorldSchema, schemaVersion, type World } from "./index";

const validWorld: World = {
  manifest: {
    schemaVersion,
    worldId: "schema-test-world",
    worldVersion: "0.1.0",
    name: "Schema Test World",
    seed: "schema-seed",
    tickSeconds: 10,
  },
  stations: [
    {
      id: "alpha",
      name: "Alpha",
      nominalCapacityPassengers: 100,
      throughputPassengersPerTick: 10,
      demand: {
        serviceId: "test-line",
        arrivalRatePassengersPerTick: 2,
        provenance: "synthetic",
      },
    },
    {
      id: "beta",
      name: "Beta",
      nominalCapacityPassengers: 100,
      throughputPassengersPerTick: 10,
      demand: {
        serviceId: "test-line",
        arrivalRatePassengersPerTick: 0,
        provenance: "synthetic",
      },
    },
  ],
  edges: [
    {
      id: "alpha-beta",
      fromStationId: "alpha",
      toStationId: "beta",
      distanceMeters: 800,
      travelTicks: 1,
    },
  ],
  services: [
    {
      id: "test-line",
      name: "Test Line",
      stationIds: ["alpha", "beta"],
      edgeIds: ["alpha-beta"],
      headwayTicks: 2,
      startTick: 0,
      endTick: 20,
      vehicleCapacityPassengers: 10,
    },
  ],
};

describe("WorldSchema", () => {
  it("accepts a valid reference-style world", () => {
    expect(WorldSchema.parse(validWorld).manifest.worldId).toBe("schema-test-world");
  });

  it("rejects invalid edge station references", () => {
    const result = WorldSchema.safeParse({
      ...validWorld,
      edges: [{ ...validWorld.edges[0], toStationId: "missing" }],
    });

    expect(result.success).toBe(false);
  });

  it("rejects invalid service edge references", () => {
    const result = WorldSchema.safeParse({
      ...validWorld,
      services: [{ ...validWorld.services[0], edgeIds: ["missing-edge"] }],
    });

    expect(result.success).toBe(false);
  });
});
