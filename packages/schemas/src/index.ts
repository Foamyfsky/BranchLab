import { z } from "zod";

export const schemaVersion = "1.0.0";

const idSchema = z
  .string()
  .min(1)
  .regex(/^[a-z0-9][a-z0-9-]*$/);
const nonNegativeIntegerSchema = z.number().int().nonnegative();
const positiveIntegerSchema = z.number().int().positive();
const nonNegativeNumberSchema = z.number().nonnegative();

export const WorldManifestSchema = z.object({
  schemaVersion: z.literal(schemaVersion),
  worldId: idSchema,
  worldVersion: z.string().min(1),
  name: z.string().min(1),
  seed: z.string().min(1),
  tickSeconds: positiveIntegerSchema,
});

export const StationSchema = z.object({
  id: idSchema,
  name: z.string().min(1),
  nominalCapacityPassengers: positiveIntegerSchema,
  throughputPassengersPerTick: nonNegativeIntegerSchema,
  demand: z.object({
    serviceId: idSchema,
    arrivalRatePassengersPerTick: nonNegativeNumberSchema,
    provenance: z.literal("synthetic"),
  }),
});

export const DirectedEdgeSchema = z.object({
  id: idSchema,
  fromStationId: idSchema,
  toStationId: idSchema,
  distanceMeters: positiveIntegerSchema,
  travelTicks: positiveIntegerSchema,
});

export const ServiceSchema = z.object({
  id: idSchema,
  name: z.string().min(1),
  stationIds: z.array(idSchema).min(2),
  edgeIds: z.array(idSchema).min(1),
  headwayTicks: positiveIntegerSchema,
  startTick: nonNegativeIntegerSchema,
  endTick: positiveIntegerSchema,
  vehicleCapacityPassengers: nonNegativeIntegerSchema,
});

export const VehicleSchema = z.object({
  id: idSchema,
  serviceId: idSchema,
  capacityPassengers: nonNegativeIntegerSchema,
  onboardPassengers: nonNegativeIntegerSchema,
  currentStationId: idSchema.optional(),
  currentEdgeId: idSchema.optional(),
  nextStationIndex: nonNegativeIntegerSchema,
  ticksToNextStation: nonNegativeIntegerSchema,
});

export const PassengerQueueSchema = z.object({
  stationId: idSchema,
  serviceId: idSchema,
  waitingPassengers: nonNegativeIntegerSchema,
});

export const SimulationMetricsSchema = z.object({
  initialPassengers: nonNegativeIntegerSchema,
  generatedPassengers: nonNegativeIntegerSchema,
  waitingPassengers: nonNegativeIntegerSchema,
  onboardPassengers: nonNegativeIntegerSchema,
  completedPassengers: nonNegativeIntegerSchema,
  abandonedPassengers: nonNegativeIntegerSchema,
  boardedPassengers: nonNegativeIntegerSchema,
  conservationHolds: z.boolean(),
});

export const SimulationStateSchema = z.object({
  schemaVersion: z.literal(schemaVersion),
  worldId: idSchema,
  worldVersion: z.string().min(1),
  seed: z.string().min(1),
  tick: nonNegativeIntegerSchema,
  queues: z.array(PassengerQueueSchema),
  vehicles: z.array(VehicleSchema),
  metrics: SimulationMetricsSchema,
});

export const WorldSchema = z
  .object({
    manifest: WorldManifestSchema,
    stations: z.array(StationSchema).min(1),
    edges: z.array(DirectedEdgeSchema),
    services: z.array(ServiceSchema).min(1),
  })
  .superRefine((world, context) => {
    const stationIds = new Set(world.stations.map((station) => station.id));
    const edgeById = new Map(world.edges.map((edge) => [edge.id, edge]));
    const serviceIds = new Set(world.services.map((service) => service.id));

    for (const edge of world.edges) {
      if (!stationIds.has(edge.fromStationId)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["edges", edge.id, "fromStationId"],
          message: `Unknown fromStationId: ${edge.fromStationId}`,
        });
      }

      if (!stationIds.has(edge.toStationId)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["edges", edge.id, "toStationId"],
          message: `Unknown toStationId: ${edge.toStationId}`,
        });
      }
    }

    for (const station of world.stations) {
      if (!serviceIds.has(station.demand.serviceId)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["stations", station.id, "demand", "serviceId"],
          message: `Unknown demand serviceId: ${station.demand.serviceId}`,
        });
      }
    }

    for (const service of world.services) {
      for (const [index, stationId] of service.stationIds.entries()) {
        if (!stationIds.has(stationId)) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["services", service.id, "stationIds", index],
            message: `Unknown service stationId: ${stationId}`,
          });
        }
      }

      if (service.edgeIds.length !== service.stationIds.length - 1) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["services", service.id, "edgeIds"],
          message: "Service edgeIds must connect each consecutive station pair",
        });
      }

      for (const [index, edgeId] of service.edgeIds.entries()) {
        const edge = edgeById.get(edgeId);
        const fromStationId = service.stationIds[index];
        const toStationId = service.stationIds[index + 1];

        if (!edge) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["services", service.id, "edgeIds", index],
            message: `Unknown service edgeId: ${edgeId}`,
          });
          continue;
        }

        if (edge.fromStationId !== fromStationId || edge.toStationId !== toStationId) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["services", service.id, "edgeIds", index],
            message: `Edge ${edgeId} does not connect ${fromStationId} to ${toStationId}`,
          });
        }
      }
    }
  });

export type WorldManifest = z.infer<typeof WorldManifestSchema>;
export type Station = z.infer<typeof StationSchema>;
export type DirectedEdge = z.infer<typeof DirectedEdgeSchema>;
export type Service = z.infer<typeof ServiceSchema>;
export type Vehicle = z.infer<typeof VehicleSchema>;
export type PassengerQueue = z.infer<typeof PassengerQueueSchema>;
export type SimulationMetrics = z.infer<typeof SimulationMetricsSchema>;
export type SimulationState = z.infer<typeof SimulationStateSchema>;
export type World = z.infer<typeof WorldSchema>;
