import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

import type {
  CandidateSubsetReport,
  CompactWorldPack,
  GeographicBounds,
} from "@branchlab/schemas";
import { CandidateSubsetReportSchema, CompactWorldPackSchema, schemaVersion } from "@branchlab/schemas";

import { parseCsvRows, type CsvRow } from "./csv";
import type { GtfsSource } from "./source";
import { median, parseGtfsTimeToSeconds, toGtfsDate, weekdayFieldForDate } from "./time";

export const requiredGtfsFiles = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"] as const;
export const optionalGtfsFiles = [
  "calendar.txt",
  "calendar_dates.txt",
  "shapes.txt",
  "frequencies.txt",
  "transfers.txt",
  "pathways.txt",
  "levels.txt",
] as const;

export interface ImportGtfsOptions {
  serviceDate: string;
  from: string;
  to: string;
  bbox?: GeographicBounds;
  routeIds?: string[];
  routeTypes?: number[];
  worldId?: string;
  worldName?: string;
  worldVersion?: string;
}

interface RouteRow {
  routeId: string;
  routeShortName: string;
  routeLongName: string;
  routeType: number;
}

interface TripRow {
  tripId: string;
  routeId: string;
  serviceId: string;
  shapeId?: string;
  directionId?: string;
}

interface StopTimeRow {
  tripId: string;
  arrivalSeconds: number;
  departureSeconds: number;
  stopId: string;
  stopSequence: number;
}

interface StopRow {
  stopId: string;
  name: string;
  lat: number;
  lon: number;
  locationType: string;
  parentStation?: string;
  platformCode?: string;
}

interface StationGroup {
  stationId: string;
  sourceStopId: string;
  name: string;
  lat: number;
  lon: number;
  platformStopIds: Set<string>;
  routeIds: Set<string>;
}

interface ShapePoint {
  lon: number;
  lat: number;
  sequence: number;
}

export async function importGtfs(source: GtfsSource, options: ImportGtfsOptions): Promise<CompactWorldPack> {
  const warnings: string[] = [];
  const fromSeconds = parseGtfsTimeToSeconds(options.from);
  const toSeconds = parseGtfsTimeToSeconds(options.to);

  if (toSeconds <= fromSeconds) {
    throw new Error("--to must be later than --from");
  }

  await validateRequiredFiles(source);

  const optionalFilesPresent = await existingOptionalFiles(source);
  const activeServiceIds = await resolveActiveServiceIds(source, options.serviceDate);
  const routes = await readRoutes(source, options);
  const { allTripIds, selectedTrips } = await readTrips(source, routes, activeServiceIds, warnings);
  const selectedTripIds = new Set(selectedTrips.keys());
  const selectedShapeIds = new Set([...selectedTrips.values()].flatMap((trip) => (trip.shapeId ? [trip.shapeId] : [])));
  const stopTimesByTrip = await readSelectedStopTimes(
    source,
    selectedTripIds,
    allTripIds,
    fromSeconds,
    toSeconds,
    warnings,
  );
  const selectedStopIds = new Set([...stopTimesByTrip.values()].flatMap((rows) => rows.map((row) => row.stopId)));
  const stops = await readSelectedStops(source, selectedStopIds, warnings);
  const stationGroups = groupStations(stops, selectedStopIds, warnings);
  const filteredStopTimesByTrip = filterStopTimesByBbox(stopTimesByTrip, stops, stationGroups, options.bbox);
  const retainedTripIds = new Set([...filteredStopTimesByTrip.keys()]);
  const retainedTrips = new Map([...selectedTrips].filter(([tripId]) => retainedTripIds.has(tripId)));
  const shapes = await readSelectedShapes(source, selectedShapeIds, warnings);
  const pack = buildWorldPack({
    source,
    options,
    fromSeconds,
    toSeconds,
    optionalFilesPresent,
    warnings,
    routes,
    trips: retainedTrips,
    stopTimesByTrip: filteredStopTimesByTrip,
    stops,
    stationGroups,
    shapes,
  });

  return CompactWorldPackSchema.parse(pack);
}

export async function validateRequiredFiles(source: GtfsSource): Promise<void> {
  const missing: string[] = [];

  for (const fileName of requiredGtfsFiles) {
    if (!(await source.hasFile(fileName))) {
      missing.push(fileName);
    }
  }

  if (missing.length > 0) {
    throw new Error(`Missing required GTFS file(s): ${missing.join(", ")}`);
  }
}

export async function buildCandidateSubsetReport(pack: CompactWorldPack): Promise<CandidateSubsetReport> {
  const routeIds = pack.services.routes.map((route) => route.routeId).sort();
  const routeNames = pack.services.routes
    .map((route) => route.routeShortName || route.routeLongName || route.routeId)
    .sort();
  const routeTypes = [...new Set(pack.services.routes.map((route) => route.routeType))].sort(
    (left, right) => left - right,
  );
  const transferStations = pack.network.stations
    .filter((station) => station.routeIds.length > 1)
    .map((station) => ({
      stationId: station.id,
      name: station.name,
      routeIds: [...station.routeIds].sort(),
    }))
    .sort((left, right) => left.stationId.localeCompare(right.stationId));
  const bounds = calculateBounds(pack.network.stations);
  const possibleDirectedEdges = pack.network.stations.length * Math.max(pack.network.stations.length - 1, 1);
  const graphDensity =
    possibleDirectedEdges === 0 ? 0 : Number((pack.network.edges.length / possibleDirectedEdges).toFixed(4));
  const medianHeadway = median(
    pack.services.headways.flatMap((headway) =>
      headway.medianHeadwaySeconds === null ? [] : [headway.medianHeadwaySeconds],
    ),
  );
  const suitabilityReasons = [
    transferStations.length > 0 ? "contains transfer stations" : "no transfer station in fixture subset",
    routeIds.length >= 2 ? "contains multiple active routes" : "single-route subset",
    pack.network.stations.length <= 25 ? "small enough for an inspectable Sydney Pulse candidate" : "large subset",
  ];
  const missingDataNotes = [
    pack.network.shapes.length === 0 ? "no route shape geometry attached" : "",
    pack.services.trips.length === 0 ? "no active trips retained" : "",
  ].filter(Boolean);

  return CandidateSubsetReportSchema.parse({
    schemaVersion,
    sourceWorldId: pack.manifest.worldId,
    candidates: [
      {
        candidateId: stableId(["candidate", ...routeIds]),
        stationCount: pack.network.stations.length,
        routeIds,
        routeNames,
        routeTypes,
        transferStations,
        activeTripCount: pack.services.trips.length,
        medianScheduledHeadwaySeconds: medianHeadway,
        geographicBounds: bounds,
        approximateGraphDensity: graphDensity,
        suitabilityReasons,
        warnings: pack.network.warnings,
        missingDataNotes,
      },
    ],
  });
}

export async function exportWorldPack(pack: CompactWorldPack, outputDirectory: string): Promise<void> {
  await mkdir(outputDirectory, { recursive: true });
  await Promise.all([
    writeJson(path.join(outputDirectory, "manifest.json"), pack.manifest),
    writeJson(path.join(outputDirectory, "network.json"), pack.network),
    writeJson(path.join(outputDirectory, "services.json"), pack.services),
    writeJson(path.join(outputDirectory, "provenance.json"), pack.provenance),
  ]);
}

export async function exportCandidateReport(report: CandidateSubsetReport, outputPath: string): Promise<void> {
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeJson(outputPath, report);
}

async function existingOptionalFiles(source: GtfsSource): Promise<string[]> {
  const present: string[] = [];

  for (const fileName of optionalGtfsFiles) {
    if (await source.hasFile(fileName)) {
      present.push(fileName);
    }
  }

  return present.sort();
}

async function resolveActiveServiceIds(source: GtfsSource, serviceDate: string): Promise<Set<string>> {
  const activeServiceIds = new Set<string>();
  const gtfsDate = toGtfsDate(serviceDate);
  const weekdayField = weekdayFieldForDate(serviceDate);

  if (await source.hasFile("calendar.txt")) {
    for await (const row of parseCsvRows(await source.openTextStream("calendar.txt"))) {
      if (cell(row, weekdayField) === "1" && gtfsDate >= cell(row, "start_date") && gtfsDate <= cell(row, "end_date")) {
        activeServiceIds.add(cell(row, "service_id"));
      }
    }
  }

  if (await source.hasFile("calendar_dates.txt")) {
    for await (const row of parseCsvRows(await source.openTextStream("calendar_dates.txt"))) {
      if (cell(row, "date") !== gtfsDate) {
        continue;
      }

      if (cell(row, "exception_type") === "1") {
        activeServiceIds.add(cell(row, "service_id"));
      }

      if (cell(row, "exception_type") === "2") {
        activeServiceIds.delete(cell(row, "service_id"));
      }
    }
  }

  return activeServiceIds;
}

async function readRoutes(source: GtfsSource, options: ImportGtfsOptions): Promise<Map<string, RouteRow>> {
  const routes = new Map<string, RouteRow>();
  const routeIdFilter = options.routeIds ? new Set(options.routeIds) : undefined;
  const routeTypeFilter = options.routeTypes ? new Set(options.routeTypes) : undefined;

  for await (const row of parseCsvRows(await source.openTextStream("routes.txt"))) {
    const routeId = cell(row, "route_id");
    const routeType = Number(cell(row, "route_type"));

    if (routeIdFilter && !routeIdFilter.has(routeId)) {
      continue;
    }

    if (routeTypeFilter && !routeTypeFilter.has(routeType)) {
      continue;
    }

    routes.set(routeId, {
      routeId,
      routeShortName: cell(row, "route_short_name"),
      routeLongName: cell(row, "route_long_name"),
      routeType,
    });
  }

  return routes;
}

async function readTrips(
  source: GtfsSource,
  routes: Map<string, RouteRow>,
  activeServiceIds: Set<string>,
  warnings: string[],
): Promise<{ allTripIds: Set<string>; selectedTrips: Map<string, TripRow> }> {
  const allTripIds = new Set<string>();
  const selectedTrips = new Map<string, TripRow>();

  for await (const row of parseCsvRows(await source.openTextStream("trips.txt"))) {
    const tripId = cell(row, "trip_id");
    const routeId = cell(row, "route_id");
    const serviceId = cell(row, "service_id");
    const shapeId = cell(row, "shape_id");
    const directionId = cell(row, "direction_id");
    allTripIds.add(tripId);

    if (!routes.has(routeId)) {
      warnings.push(`Trip ${tripId} references filtered or missing route ${routeId}`);
      continue;
    }

    if (!activeServiceIds.has(serviceId)) {
      continue;
    }

    const trip: TripRow = { tripId, routeId, serviceId };

    if (shapeId) {
      trip.shapeId = shapeId;
    }

    if (directionId) {
      trip.directionId = directionId;
    }

    selectedTrips.set(tripId, trip);
  }

  return { allTripIds, selectedTrips };
}

async function readSelectedStopTimes(
  source: GtfsSource,
  selectedTripIds: Set<string>,
  allTripIds: Set<string>,
  fromSeconds: number,
  toSeconds: number,
  warnings: string[],
): Promise<Map<string, StopTimeRow[]>> {
  const stopTimesByTrip = new Map<string, StopTimeRow[]>();
  const invalidTripWarnings = new Set<string>();

  for await (const row of parseCsvRows(await source.openTextStream("stop_times.txt"))) {
    const tripId = cell(row, "trip_id");

    if (!allTripIds.has(tripId) && !invalidTripWarnings.has(tripId)) {
      warnings.push(`stop_times.txt references unknown trip ${tripId}`);
      invalidTripWarnings.add(tripId);
    }

    if (!selectedTripIds.has(tripId)) {
      continue;
    }

    const arrivalSeconds = parseGtfsTimeToSeconds(cell(row, "arrival_time"));
    const departureSeconds = parseGtfsTimeToSeconds(cell(row, "departure_time"));

    if (departureSeconds < fromSeconds || arrivalSeconds > toSeconds) {
      continue;
    }

    const stopTimes = stopTimesByTrip.get(tripId) ?? [];
    stopTimes.push({
      tripId,
      arrivalSeconds,
      departureSeconds,
      stopId: cell(row, "stop_id"),
      stopSequence: Number(cell(row, "stop_sequence")),
    });
    stopTimesByTrip.set(tripId, stopTimes);
  }

  for (const [tripId, rows] of [...stopTimesByTrip]) {
    rows.sort((left, right) => left.stopSequence - right.stopSequence);

    if (rows.length < 2) {
      warnings.push(`Trip ${tripId} has fewer than two retained stops in the requested time window`);
      stopTimesByTrip.delete(tripId);
    }
  }

  return new Map([...stopTimesByTrip].sort(([left], [right]) => left.localeCompare(right)));
}

async function readSelectedStops(
  source: GtfsSource,
  selectedStopIds: Set<string>,
  warnings: string[],
): Promise<Map<string, StopRow>> {
  const stops = new Map<string, StopRow>();
  const parentStopIds = new Set<string>();
  const allRows: StopRow[] = [];

  for await (const row of parseCsvRows(await source.openTextStream("stops.txt"))) {
    const stop = optionalProps({
      stopId: row.stop_id,
      name: row.stop_name,
      lat: Number(row.stop_lat),
      lon: Number(row.stop_lon),
      locationType: row.location_type || "0",
      parentStation: row.parent_station || undefined,
      platformCode: row.platform_code || undefined,
    });

    allRows.push(stop);

    if (selectedStopIds.has(stop.stopId)) {
      stops.set(stop.stopId, stop);

      if (stop.parentStation) {
        parentStopIds.add(stop.parentStation);
      }
    }
  }

  for (const stop of allRows) {
    if (parentStopIds.has(stop.stopId)) {
      stops.set(stop.stopId, stop);
    }
  }

  for (const stopId of selectedStopIds) {
    if (!stops.has(stopId)) {
      warnings.push(`Selected stop_time references missing stop ${stopId}`);
    }
  }

  return stops;
}

function groupStations(
  stops: Map<string, StopRow>,
  selectedStopIds: Set<string>,
  warnings: string[],
): Map<string, StationGroup> {
  const stationGroups = new Map<string, StationGroup>();

  for (const stopId of [...selectedStopIds].sort()) {
    const platform = stops.get(stopId);

    if (!platform) {
      continue;
    }

    const parent = platform.parentStation ? stops.get(platform.parentStation) : undefined;

    if (platform.parentStation && !parent) {
      warnings.push(`Platform stop ${platform.stopId} references missing parent_station ${platform.parentStation}`);
    }

    const sourceStop = parent ?? platform;
    const stationId = stableId(["station", sourceStop.stopId]);
    const group =
      stationGroups.get(stationId) ??
      ({
        stationId,
        sourceStopId: sourceStop.stopId,
        name: sourceStop.name,
        lat: sourceStop.lat,
        lon: sourceStop.lon,
        platformStopIds: new Set<string>(),
        routeIds: new Set<string>(),
      } satisfies StationGroup);

    group.platformStopIds.add(platform.stopId);
    stationGroups.set(stationId, group);
  }

  return stationGroups;
}

function filterStopTimesByBbox(
  stopTimesByTrip: Map<string, StopTimeRow[]>,
  stops: Map<string, StopRow>,
  stationGroups: Map<string, StationGroup>,
  bbox: GeographicBounds | undefined,
): Map<string, StopTimeRow[]> {
  if (!bbox) {
    return stopTimesByTrip;
  }

  const retained = new Map<string, StopTimeRow[]>();

  for (const [tripId, stopTimes] of stopTimesByTrip) {
    const filteredRows = stopTimes.filter((row) => {
      const station = stationGroupForStop(row.stopId, stops, stationGroups);
      return (
        station !== undefined &&
        station.lon >= bbox.minLon &&
        station.lon <= bbox.maxLon &&
        station.lat >= bbox.minLat &&
        station.lat <= bbox.maxLat
      );
    });

    if (filteredRows.length >= 2) {
      retained.set(tripId, filteredRows);
    }
  }

  return retained;
}

async function readSelectedShapes(
  source: GtfsSource,
  selectedShapeIds: Set<string>,
  warnings: string[],
): Promise<Map<string, ShapePoint[]>> {
  const shapes = new Map<string, ShapePoint[]>();

  if (!(await source.hasFile("shapes.txt"))) {
    if (selectedShapeIds.size > 0) {
      warnings.push("Selected trips reference shapes, but shapes.txt is absent");
    }
    return shapes;
  }

  for await (const row of parseCsvRows(await source.openTextStream("shapes.txt"))) {
    if (!selectedShapeIds.has(row.shape_id)) {
      continue;
    }

    const points = shapes.get(row.shape_id) ?? [];
    points.push({
      lat: Number(row.shape_pt_lat),
      lon: Number(row.shape_pt_lon),
      sequence: Number(row.shape_pt_sequence),
    });
    shapes.set(row.shape_id, points);
  }

  for (const shapeId of selectedShapeIds) {
    if (!shapes.has(shapeId)) {
      warnings.push(`Selected trip references missing shape ${shapeId}`);
    }
  }

  return shapes;
}

function buildWorldPack(input: {
  source: GtfsSource;
  options: ImportGtfsOptions;
  fromSeconds: number;
  toSeconds: number;
  optionalFilesPresent: string[];
  warnings: string[];
  routes: Map<string, RouteRow>;
  trips: Map<string, TripRow>;
  stopTimesByTrip: Map<string, StopTimeRow[]>;
  stops: Map<string, StopRow>;
  stationGroups: Map<string, StationGroup>;
  shapes: Map<string, ShapePoint[]>;
}): CompactWorldPack {
  const edgeAccumulator = new Map<
    string,
    {
      fromStationId: string;
      toStationId: string;
      routeId: string;
      directionId?: string;
      tripIds: Set<string>;
      travelSeconds: number[];
    }
  >();
  const tripSummaries = [];
  const routeTripStartSeconds = new Map<string, number[]>();

  for (const [tripId, stopTimes] of input.stopTimesByTrip) {
    const trip = input.trips.get(tripId);

    if (!trip) {
      continue;
    }

    const stationIds = stopTimes
      .map((stopTime) => stationGroupForStop(stopTime.stopId, input.stops, input.stationGroups)?.stationId)
      .filter((stationId): stationId is string => stationId !== undefined);

    if (stationIds.length < 2) {
      input.warnings.push(`Trip ${tripId} does not have enough retained grouped stations`);
      continue;
    }

    routeTripStartSeconds.set(trip.routeId, [...(routeTripStartSeconds.get(trip.routeId) ?? []), stopTimes[0]!.departureSeconds]);

    for (const stationId of stationIds) {
      input.stationGroups.get(stationId)?.routeIds.add(trip.routeId);
    }

    tripSummaries.push(
      optionalProps({
        tripId,
        routeId: trip.routeId,
        serviceId: trip.serviceId,
        directionId: trip.directionId,
        shapeId: trip.shapeId,
        stationIds,
        startSeconds: stopTimes[0]!.departureSeconds,
        endSeconds: stopTimes[stopTimes.length - 1]!.arrivalSeconds,
      }),
    );

    for (let index = 0; index < stopTimes.length - 1; index += 1) {
      const current = stopTimes[index]!;
      const next = stopTimes[index + 1]!;
      const fromStation = stationGroupForStop(current.stopId, input.stops, input.stationGroups);
      const toStation = stationGroupForStop(next.stopId, input.stops, input.stationGroups);

      if (!fromStation || !toStation || fromStation.stationId === toStation.stationId) {
        continue;
      }

      const edgeKey = [trip.routeId, trip.directionId ?? "none", fromStation.stationId, toStation.stationId].join("|");
      const edge =
        edgeAccumulator.get(edgeKey) ??
        ({
          fromStationId: fromStation.stationId,
          toStationId: toStation.stationId,
          routeId: trip.routeId,
          directionId: trip.directionId,
          tripIds: new Set<string>(),
          travelSeconds: [],
        } satisfies {
          fromStationId: string;
          toStationId: string;
          routeId: string;
          directionId?: string;
          tripIds: Set<string>;
          travelSeconds: number[];
        });

      edge.tripIds.add(tripId);
      edge.travelSeconds.push(Math.max(1, next.arrivalSeconds - current.departureSeconds));
      edgeAccumulator.set(edgeKey, edge);
    }
  }

  const stations = [...input.stationGroups.values()]
    .map((station) => ({
      id: station.stationId,
      sourceStopId: station.sourceStopId,
      name: station.name,
      lat: station.lat,
      lon: station.lon,
      platformStopIds: [...station.platformStopIds].sort(),
      routeIds: [...station.routeIds].sort(),
      fidelity: "real-gtfs" as const,
    }))
    .filter((station) => station.routeIds.length > 0)
    .sort((left, right) => left.id.localeCompare(right.id));
  const retainedStationIds = new Set(stations.map((station) => station.id));
  const platforms = [...input.stops.values()]
    .filter((stop) => {
      const station = stationGroupForStop(stop.stopId, input.stops, input.stationGroups);
      return station !== undefined && retainedStationIds.has(station.stationId) && stop.locationType !== "1";
    })
    .map((stop) => {
      const station = stationGroupForStop(stop.stopId, input.stops, input.stationGroups)!;

      return optionalProps({
        stopId: stop.stopId,
        stationId: station.stationId,
        name: stop.name,
        platformCode: stop.platformCode,
        lat: stop.lat,
        lon: stop.lon,
      });
    })
    .sort((left, right) => left.stopId.localeCompare(right.stopId));
  const edges = [...edgeAccumulator.values()]
    .map((edge) =>
      optionalProps({
        id: stableId(["edge", edge.routeId, edge.directionId ?? "none", edge.fromStationId, edge.toStationId]),
        fromStationId: edge.fromStationId,
        toStationId: edge.toStationId,
        routeId: edge.routeId,
        directionId: edge.directionId,
        tripIds: [...edge.tripIds].sort(),
        scheduledTravelSeconds: median(edge.travelSeconds) ?? 1,
      }),
    )
    .sort((left, right) => left.id.localeCompare(right.id));
  const routes = [...input.routes.values()]
    .map((route) => ({
      ...route,
      activeTripCount: [...input.trips.values()].filter((trip) => trip.routeId === route.routeId).length,
    }))
    .filter((route) => route.activeTripCount > 0)
    .sort((left, right) => left.routeId.localeCompare(right.routeId));
  const tripSummariesSorted = tripSummaries.sort((left, right) => left.tripId.localeCompare(right.tripId));
  const headways = [...routeTripStartSeconds]
    .map(([routeId, starts]) => {
      const sortedStarts = [...starts].sort((left, right) => left - right);
      const deltas = sortedStarts.slice(1).map((start, index) => start - sortedStarts[index]!);

      return {
        routeId,
        medianHeadwaySeconds: median(deltas),
        tripStartSeconds: sortedStarts,
      };
    })
    .sort((left, right) => left.routeId.localeCompare(right.routeId));
  const shapes = [...input.shapes]
    .map(([shapeId, points]) => ({
      shapeId,
      points: points
        .sort((left, right) => left.sequence - right.sequence)
        .map((point) => ({ lon: point.lon, lat: point.lat })),
    }))
    .filter((shape) => shape.points.length >= 2)
    .sort((left, right) => left.shapeId.localeCompare(right.shapeId));

  return {
    manifest: {
      schemaVersion,
      worldId: stableId([input.options.worldId ?? "fixture-world"]),
      worldVersion: input.options.worldVersion ?? "0.1.0",
      name: input.options.worldName ?? "GTFS Fixture World",
      serviceDate: input.options.serviceDate,
      timeRange: {
        fromSeconds: input.fromSeconds,
        toSeconds: input.toSeconds,
      },
      generatedBy: "@branchlab/gtfs-importer",
    },
    network: {
      stations,
      platforms,
      edges,
      shapes,
      warnings: [...new Set(input.warnings)].sort(),
    },
    services: {
      routes,
      trips: tripSummariesSorted,
      headways,
    },
    provenance: {
      sourceKind: input.source.kind,
      requiredFiles: [...requiredGtfsFiles],
      optionalFilesPresent: input.optionalFilesPresent,
      filters: optionalProps({
        serviceDate: input.options.serviceDate,
        fromSeconds: input.fromSeconds,
        toSeconds: input.toSeconds,
        bbox: input.options.bbox,
        routeIds: input.options.routeIds?.slice().sort(),
        routeTypes: input.options.routeTypes?.slice().sort((left, right) => left - right),
      }),
      fidelity: {
        supply: "real-gtfs-or-fixture",
        demand: "disabled",
        realtime: "disabled",
      },
    },
  };
}

function stationGroupForStop(
  stopId: string,
  stops: Map<string, StopRow>,
  stationGroups: Map<string, StationGroup>,
): StationGroup | undefined {
  const stop = stops.get(stopId);

  if (!stop) {
    return undefined;
  }

  const parent = stop.parentStation ? stops.get(stop.parentStation) : undefined;
  const sourceStopId = parent?.stopId ?? stop.stopId;

  return stationGroups.get(stableId(["station", sourceStopId]));
}

function calculateBounds(stations: CompactWorldPack["network"]["stations"]): GeographicBounds | null {
  if (stations.length === 0) {
    return null;
  }

  return {
    minLon: Math.min(...stations.map((station) => station.lon)),
    minLat: Math.min(...stations.map((station) => station.lat)),
    maxLon: Math.max(...stations.map((station) => station.lon)),
    maxLat: Math.max(...stations.map((station) => station.lat)),
  };
}

export function stableId(parts: string[]): string {
  const joined = parts.join("-");
  const slug = joined
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return slug || "id";
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function optionalProps<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(Object.entries(value).filter(([, entry]) => entry !== undefined)) as T;
}
