import type { World } from "@branchlab/schemas";

import { schemaVersion } from "@branchlab/schemas";

export const metroPulseWorldId = "metro-pulse-reference";

const baseMetroPulseWorld: World = {
  manifest: {
    schemaVersion,
    worldId: metroPulseWorldId,
    worldVersion: "0.1.0",
    name: "Metro Pulse Reference",
    seed: "metro-pulse-seed",
    tickSeconds: 10,
  },
  stations: [
    {
      id: "north-gate",
      name: "North Gate",
      nominalCapacityPassengers: 160,
      throughputPassengersPerTick: 14,
      demand: {
        serviceId: "spine-line",
        arrivalRatePassengersPerTick: 3.8,
        provenance: "synthetic",
      },
    },
    {
      id: "west-market",
      name: "West Market",
      nominalCapacityPassengers: 140,
      throughputPassengersPerTick: 12,
      demand: {
        serviceId: "cross-line",
        arrivalRatePassengersPerTick: 2.7,
        provenance: "synthetic",
      },
    },
    {
      id: "pulse-junction",
      name: "Pulse Junction",
      nominalCapacityPassengers: 220,
      throughputPassengersPerTick: 18,
      demand: {
        serviceId: "spine-line",
        arrivalRatePassengersPerTick: 1.2,
        provenance: "synthetic",
      },
    },
    {
      id: "civic-forum",
      name: "Civic Forum",
      nominalCapacityPassengers: 130,
      throughputPassengersPerTick: 10,
      demand: {
        serviceId: "spine-line",
        arrivalRatePassengersPerTick: 0.8,
        provenance: "synthetic",
      },
    },
    {
      id: "river-park",
      name: "River Park",
      nominalCapacityPassengers: 130,
      throughputPassengersPerTick: 10,
      demand: {
        serviceId: "cross-line",
        arrivalRatePassengersPerTick: 0.9,
        provenance: "synthetic",
      },
    },
    {
      id: "south-works",
      name: "South Works",
      nominalCapacityPassengers: 120,
      throughputPassengersPerTick: 10,
      demand: {
        serviceId: "spine-line",
        arrivalRatePassengersPerTick: 0.4,
        provenance: "synthetic",
      },
    },
    {
      id: "event-bowl",
      name: "Event Bowl",
      nominalCapacityPassengers: 260,
      throughputPassengersPerTick: 16,
      demand: {
        serviceId: "spine-line",
        arrivalRatePassengersPerTick: 0,
        provenance: "synthetic",
      },
    },
    {
      id: "east-pier",
      name: "East Pier",
      nominalCapacityPassengers: 150,
      throughputPassengersPerTick: 12,
      demand: {
        serviceId: "cross-line",
        arrivalRatePassengersPerTick: 0,
        provenance: "synthetic",
      },
    },
  ],
  edges: [
    {
      id: "north-gate-pulse-junction",
      fromStationId: "north-gate",
      toStationId: "pulse-junction",
      distanceMeters: 1200,
      travelTicks: 1,
    },
    {
      id: "pulse-junction-civic-forum",
      fromStationId: "pulse-junction",
      toStationId: "civic-forum",
      distanceMeters: 700,
      travelTicks: 1,
    },
    {
      id: "civic-forum-south-works",
      fromStationId: "civic-forum",
      toStationId: "south-works",
      distanceMeters: 900,
      travelTicks: 1,
    },
    {
      id: "south-works-event-bowl",
      fromStationId: "south-works",
      toStationId: "event-bowl",
      distanceMeters: 800,
      travelTicks: 1,
    },
    {
      id: "west-market-pulse-junction",
      fromStationId: "west-market",
      toStationId: "pulse-junction",
      distanceMeters: 1100,
      travelTicks: 1,
    },
    {
      id: "pulse-junction-river-park",
      fromStationId: "pulse-junction",
      toStationId: "river-park",
      distanceMeters: 650,
      travelTicks: 1,
    },
    {
      id: "river-park-east-pier",
      fromStationId: "river-park",
      toStationId: "east-pier",
      distanceMeters: 950,
      travelTicks: 1,
    },
  ],
  services: [
    {
      id: "spine-line",
      name: "Spine Line",
      stationIds: ["north-gate", "pulse-junction", "civic-forum", "south-works", "event-bowl"],
      edgeIds: [
        "north-gate-pulse-junction",
        "pulse-junction-civic-forum",
        "civic-forum-south-works",
        "south-works-event-bowl",
      ],
      headwayTicks: 3,
      startTick: 0,
      endTick: 120,
      vehicleCapacityPassengers: 18,
    },
    {
      id: "cross-line",
      name: "Cross Line",
      stationIds: ["west-market", "pulse-junction", "river-park", "east-pier"],
      edgeIds: ["west-market-pulse-junction", "pulse-junction-river-park", "river-park-east-pier"],
      headwayTicks: 4,
      startTick: 0,
      endTick: 120,
      vehicleCapacityPassengers: 14,
    },
  ],
};

export function createMetroPulseWorld(overrides: Partial<World["manifest"]> = {}): World {
  return {
    ...structuredClone(baseMetroPulseWorld),
    manifest: {
      ...baseMetroPulseWorld.manifest,
      ...overrides,
    },
  };
}
