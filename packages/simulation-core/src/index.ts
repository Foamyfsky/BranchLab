import type {
  DirectedEdge,
  PassengerQueue,
  Service,
  SimulationState,
  Vehicle,
  World,
} from "@branchlab/schemas";

import { schemaVersion } from "@branchlab/schemas";

export type SimulationSnapshot = string;

type MutableMetrics = SimulationState["metrics"];

const maxPoissonIterations = 10_000;

export function deterministicUniform(
  seed: string,
  streamName: string,
  tick: number,
  entityId: string,
  drawIndex = 0,
): number {
  const input = `${seed}\u001f${streamName}\u001f${tick}\u001f${entityId}\u001f${drawIndex}`;
  const hash = fnv1a32(input);

  return (hash + 0.5) / 0x1_0000_0000;
}

export function samplePoisson(
  lambda: number,
  seed: string,
  streamName: string,
  tick: number,
  entityId: string,
): number {
  if (lambda <= 0) {
    return 0;
  }

  const threshold = Math.exp(-lambda);
  let product = 1;

  for (let drawIndex = 0; drawIndex < maxPoissonIterations; drawIndex += 1) {
    product *= deterministicUniform(seed, streamName, tick, entityId, drawIndex);

    if (product <= threshold) {
      return drawIndex;
    }
  }

  throw new Error(`Poisson sampler exceeded ${maxPoissonIterations} draws`);
}

export function sampleDelayTicks(seed: string, tick: number, entityId: string): number {
  return Math.floor(deterministicUniform(seed, "delay", tick, entityId) * 3);
}

export function createInitialState(world: World): SimulationState {
  const queueKeys = new Set<string>();

  for (const service of world.services) {
    for (const stationId of service.stationIds) {
      queueKeys.add(`${stationId}:${service.id}`);
    }
  }

  for (const station of world.stations) {
    queueKeys.add(`${station.id}:${station.demand.serviceId}`);
  }

  const queues = [...queueKeys]
    .map((key) => {
      const [stationId, serviceId] = key.split(":");

      return {
        stationId: stationId ?? "",
        serviceId: serviceId ?? "",
        waitingPassengers: 0,
      };
    })
    .sort(compareQueues);

  return withFreshAccounting({
    schemaVersion,
    worldId: world.manifest.worldId,
    worldVersion: world.manifest.worldVersion,
    seed: world.manifest.seed,
    tick: 0,
    queues,
    vehicles: [],
    metrics: {
      initialPassengers: 0,
      generatedPassengers: 0,
      waitingPassengers: 0,
      onboardPassengers: 0,
      completedPassengers: 0,
      abandonedPassengers: 0,
      boardedPassengers: 0,
      conservationHolds: true,
    },
  });
}

export function runSimulation(
  world: World,
  ticks: number,
  initialState = createInitialState(world),
): SimulationState {
  let state = restoreState(serializeState(initialState));

  for (let index = 0; index < ticks; index += 1) {
    state = stepSimulation(world, state);
  }

  return state;
}

export function stepSimulation(world: World, state: SimulationState): SimulationState {
  const queues = cloneQueues(state.queues);
  const metrics: MutableMetrics = { ...state.metrics };
  const tick = state.tick;
  const edgeById = new Map(world.edges.map((edge) => [edge.id, edge]));
  const stationThroughput = new Map(
    world.stations.map((station) => [station.id, station.throughputPassengersPerTick]),
  );
  const activeVehicles = advanceVehicles(world, state.vehicles, metrics);

  for (const station of world.stations) {
    const generatedPassengers = samplePoisson(
      station.demand.arrivalRatePassengersPerTick,
      world.manifest.seed,
      "arrival",
      tick,
      station.id,
    );
    const queue = findQueue(queues, station.id, station.demand.serviceId);

    queue.waitingPassengers += generatedPassengers;
    metrics.generatedPassengers += generatedPassengers;
  }

  activeVehicles.push(...spawnVehicles(world, tick));
  activeVehicles.sort(compareVehicles);

  for (const vehicle of activeVehicles) {
    if (vehicle.ticksToNextStation !== 0 || vehicle.currentStationId === undefined) {
      continue;
    }

    const service = mustFindService(world, vehicle.serviceId);
    const isTerminal = vehicle.nextStationIndex >= service.stationIds.length - 1;

    if (isTerminal) {
      continue;
    }

    const queue = findQueue(queues, vehicle.currentStationId, vehicle.serviceId);
    const throughput = stationThroughput.get(vehicle.currentStationId) ?? 0;
    const freeCapacity = Math.max(0, vehicle.capacityPassengers - vehicle.onboardPassengers);
    const boardedPassengers = Math.min(queue.waitingPassengers, freeCapacity, throughput);

    queue.waitingPassengers -= boardedPassengers;
    vehicle.onboardPassengers += boardedPassengers;
    metrics.boardedPassengers += boardedPassengers;

    departVehicle(service, edgeById, vehicle);
  }

  return withFreshAccounting({
    ...state,
    tick: tick + 1,
    queues: queues.sort(compareQueues),
    vehicles: activeVehicles
      .filter((vehicle) => !isCompletedVehicle(world, vehicle))
      .sort(compareVehicles),
    metrics,
  });
}

export function serializeState(state: SimulationState): SimulationSnapshot {
  return JSON.stringify(state);
}

export function restoreState(snapshot: SimulationSnapshot): SimulationState {
  return JSON.parse(snapshot) as SimulationState;
}

export function assertPassengerConservation(state: SimulationState): void {
  if (!state.metrics.conservationHolds) {
    throw new Error(`Passenger conservation failed at tick ${state.tick}`);
  }
}

function advanceVehicles(world: World, vehicles: Vehicle[], metrics: MutableMetrics): Vehicle[] {
  const advancedVehicles: Vehicle[] = [];

  for (const vehicle of vehicles) {
    const nextVehicle: Vehicle = { ...vehicle };

    if (nextVehicle.ticksToNextStation > 0) {
      nextVehicle.ticksToNextStation -= 1;

      if (nextVehicle.ticksToNextStation === 0) {
        const service = mustFindService(world, nextVehicle.serviceId);
        const stationId = service.stationIds[nextVehicle.nextStationIndex];

        nextVehicle.currentStationId = stationId;
        nextVehicle.currentEdgeId = undefined;

        if (nextVehicle.nextStationIndex >= service.stationIds.length - 1) {
          metrics.completedPassengers += nextVehicle.onboardPassengers;
          nextVehicle.onboardPassengers = 0;
        }
      }
    }

    advancedVehicles.push(nextVehicle);
  }

  return advancedVehicles;
}

function spawnVehicles(world: World, tick: number): Vehicle[] {
  const vehicles: Vehicle[] = [];

  for (const service of world.services) {
    if (tick < service.startTick || tick > service.endTick) {
      continue;
    }

    if ((tick - service.startTick) % service.headwayTicks !== 0) {
      continue;
    }

    vehicles.push({
      id: `${service.id}-${tick}`,
      serviceId: service.id,
      capacityPassengers: service.vehicleCapacityPassengers,
      onboardPassengers: 0,
      currentStationId: service.stationIds[0],
      nextStationIndex: 0,
      ticksToNextStation: 0,
    });
  }

  return vehicles;
}

function departVehicle(
  service: Service,
  edgeById: Map<string, DirectedEdge>,
  vehicle: Vehicle,
): void {
  const edgeId = service.edgeIds[vehicle.nextStationIndex];

  if (edgeId === undefined) {
    throw new Error(`Missing edge at index ${vehicle.nextStationIndex} for service ${service.id}`);
  }

  const edge = edgeById.get(edgeId);

  if (!edge) {
    throw new Error(`Missing edge ${edgeId} for service ${service.id}`);
  }

  vehicle.currentStationId = undefined;
  vehicle.currentEdgeId = edge.id;
  vehicle.nextStationIndex += 1;
  vehicle.ticksToNextStation = edge.travelTicks;
}

function isCompletedVehicle(world: World, vehicle: Vehicle): boolean {
  const service = mustFindService(world, vehicle.serviceId);

  return (
    vehicle.ticksToNextStation === 0 && vehicle.nextStationIndex >= service.stationIds.length - 1
  );
}

function withFreshAccounting(state: SimulationState): SimulationState {
  const waitingPassengers = state.queues.reduce(
    (total, queue) => total + queue.waitingPassengers,
    0,
  );
  const onboardPassengers = state.vehicles.reduce(
    (total, vehicle) => total + vehicle.onboardPassengers,
    0,
  );
  const leftSide = state.metrics.initialPassengers + state.metrics.generatedPassengers;
  const rightSide =
    waitingPassengers +
    onboardPassengers +
    state.metrics.completedPassengers +
    state.metrics.abandonedPassengers;

  return {
    ...state,
    metrics: {
      ...state.metrics,
      waitingPassengers,
      onboardPassengers,
      conservationHolds: leftSide === rightSide,
    },
  };
}

function findQueue(queues: PassengerQueue[], stationId: string, serviceId: string): PassengerQueue {
  const queue = queues.find(
    (candidate) => candidate.stationId === stationId && candidate.serviceId === serviceId,
  );

  if (!queue) {
    throw new Error(`Missing queue for ${stationId}/${serviceId}`);
  }

  return queue;
}

function mustFindService(world: World, serviceId: string): Service {
  const service = world.services.find((candidate) => candidate.id === serviceId);

  if (!service) {
    throw new Error(`Unknown service ${serviceId}`);
  }

  return service;
}

function cloneQueues(queues: PassengerQueue[]): PassengerQueue[] {
  return queues.map((queue) => ({ ...queue }));
}

function compareQueues(left: PassengerQueue, right: PassengerQueue): number {
  return `${left.stationId}:${left.serviceId}`.localeCompare(
    `${right.stationId}:${right.serviceId}`,
  );
}

function compareVehicles(left: Vehicle, right: Vehicle): number {
  return left.id.localeCompare(right.id);
}

function fnv1a32(input: string): number {
  let hash = 0x811c9dc5;

  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }

  return hash >>> 0;
}
