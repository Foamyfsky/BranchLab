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

export const GeographicPointSchema = z.object({
  lon: z.number().gte(-180).lte(180),
  lat: z.number().gte(-90).lte(90),
});

export const GeographicBoundsSchema = z.object({
  minLon: z.number().gte(-180).lte(180),
  minLat: z.number().gte(-90).lte(90),
  maxLon: z.number().gte(-180).lte(180),
  maxLat: z.number().gte(-90).lte(90),
});

export const CompactWorldManifestSchema = z.object({
  schemaVersion: z.literal(schemaVersion),
  worldId: idSchema,
  worldVersion: z.string().min(1),
  name: z.string().min(1),
  serviceDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  timeRange: z.object({
    fromSeconds: nonNegativeIntegerSchema,
    toSeconds: positiveIntegerSchema,
  }),
  generatedBy: z.literal("@branchlab/gtfs-importer"),
});

export const CompactPlatformSchema = z.object({
  stopId: z.string().min(1),
  stationId: idSchema,
  name: z.string().min(1),
  platformCode: z.string().optional(),
  lat: z.number().gte(-90).lte(90),
  lon: z.number().gte(-180).lte(180),
});

export const CompactStationSchema = z.object({
  id: idSchema,
  sourceStopId: z.string().min(1),
  name: z.string().min(1),
  lat: z.number().gte(-90).lte(90),
  lon: z.number().gte(-180).lte(180),
  platformStopIds: z.array(z.string().min(1)),
  routeIds: z.array(z.string().min(1)),
  fidelity: z.literal("real-gtfs"),
});

export const CompactTransitEdgeSchema = z.object({
  id: idSchema,
  fromStationId: idSchema,
  toStationId: idSchema,
  routeId: z.string().min(1),
  directionId: z.string().optional(),
  tripIds: z.array(z.string().min(1)),
  scheduledTravelSeconds: positiveIntegerSchema,
});

export const CompactShapeSchema = z.object({
  shapeId: z.string().min(1),
  points: z.array(GeographicPointSchema).min(2),
});

export const CompactRouteSummarySchema = z.object({
  routeId: z.string().min(1),
  routeShortName: z.string(),
  routeLongName: z.string(),
  routeType: nonNegativeIntegerSchema,
  activeTripCount: nonNegativeIntegerSchema,
});

export const CompactTripSummarySchema = z.object({
  tripId: z.string().min(1),
  routeId: z.string().min(1),
  serviceId: z.string().min(1),
  directionId: z.string().optional(),
  shapeId: z.string().optional(),
  stationIds: z.array(idSchema).min(2),
  startSeconds: nonNegativeIntegerSchema,
  endSeconds: positiveIntegerSchema,
});

export const HeadwaySummarySchema = z.object({
  routeId: z.string().min(1),
  medianHeadwaySeconds: nonNegativeIntegerSchema.nullable(),
  tripStartSeconds: z.array(nonNegativeIntegerSchema),
});

export const CompactWorldPackSchema = z.object({
  manifest: CompactWorldManifestSchema,
  network: z.object({
    stations: z.array(CompactStationSchema),
    platforms: z.array(CompactPlatformSchema),
    edges: z.array(CompactTransitEdgeSchema),
    shapes: z.array(CompactShapeSchema),
    warnings: z.array(z.string()),
  }),
  services: z.object({
    routes: z.array(CompactRouteSummarySchema),
    trips: z.array(CompactTripSummarySchema),
    headways: z.array(HeadwaySummarySchema),
  }),
  provenance: z.object({
    sourceKind: z.enum(["directory", "zip"]),
    requiredFiles: z.array(z.string()),
    optionalFilesPresent: z.array(z.string()),
    filters: z.object({
      serviceDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      fromSeconds: nonNegativeIntegerSchema,
      toSeconds: positiveIntegerSchema,
      bbox: GeographicBoundsSchema.optional(),
      routeIds: z.array(z.string()).optional(),
      routeTypes: z.array(nonNegativeIntegerSchema).optional(),
    }),
    fidelity: z.object({
      supply: z.literal("real-gtfs-or-fixture"),
      demand: z.literal("disabled"),
      realtime: z.literal("disabled"),
    }),
  }),
});

export const CandidateSubsetSchema = z.object({
  candidateId: idSchema,
  stationCount: nonNegativeIntegerSchema,
  routeIds: z.array(z.string().min(1)),
  routeNames: z.array(z.string()),
  routeTypes: z.array(nonNegativeIntegerSchema),
  transferStations: z.array(
    z.object({
      stationId: idSchema,
      name: z.string(),
      routeIds: z.array(z.string().min(1)),
    }),
  ),
  activeTripCount: nonNegativeIntegerSchema,
  medianScheduledHeadwaySeconds: nonNegativeIntegerSchema.nullable(),
  geographicBounds: GeographicBoundsSchema.nullable(),
  approximateGraphDensity: nonNegativeNumberSchema,
  suitabilityReasons: z.array(z.string()),
  warnings: z.array(z.string()),
  missingDataNotes: z.array(z.string()),
});

export const CandidateSubsetReportSchema = z.object({
  schemaVersion: z.literal(schemaVersion),
  sourceWorldId: idSchema,
  candidates: z.array(CandidateSubsetSchema),
});

export const EntryExitTripValueSchema = z.discriminatedUnion("kind", [
  z.object({
    kind: z.literal("exact"),
    value: nonNegativeIntegerSchema,
  }),
  z.object({
    kind: z.literal("censored-less-than"),
    upperBoundExclusive: positiveIntegerSchema,
    raw: z.string().min(1),
  }),
]);

export const EntryExitRecordSchema = z.object({
  monthYear: z.string().min(1),
  stationName: z.string().min(1),
  normalizedStationName: z.string().min(1),
  stationType: z.string().min(1),
  entryExit: z.enum(["Entry", "Exit"]),
  trip: EntryExitTripValueSchema,
});

export const EntryExitStationMatchSchema = z.object({
  sourceStationName: z.string().min(1),
  normalizedStationName: z.string().min(1),
  candidates: z.array(
    z.object({
      stationId: idSchema,
      name: z.string().min(1),
      confidence: z.number().gte(0).lte(1),
      matchType: z.enum(["exact", "fuzzy"]),
    }),
  ),
  requiresManualReview: z.boolean(),
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
export type GeographicBounds = z.infer<typeof GeographicBoundsSchema>;
export type CompactWorldPack = z.infer<typeof CompactWorldPackSchema>;
export type CandidateSubset = z.infer<typeof CandidateSubsetSchema>;
export type CandidateSubsetReport = z.infer<typeof CandidateSubsetReportSchema>;
export type EntryExitRecord = z.infer<typeof EntryExitRecordSchema>;
export type EntryExitStationMatch = z.infer<typeof EntryExitStationMatchSchema>;
