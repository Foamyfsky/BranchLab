import { mkdir, readFile, rm } from "node:fs/promises";
import path from "node:path";

import { describe, expect, it, beforeEach } from "vitest";

import { matchEntryExitStation, readEntryExitRecords } from "./entry-exit";
import { createFixtureFeed, writeFixtureDirectory, writeFixtureZip } from "./fixtures";
import {
  buildCandidateSubsetReport,
  exportWorldPack,
  importGtfs,
  validateRequiredFiles,
} from "./importer";
import { DirectoryGtfsSource, ZipGtfsSource, bufferToTextStream } from "./source";

const tmpRoot = path.join(process.cwd(), "packages", "gtfs-importer", ".tmp-tests");
const baseOptions = {
  serviceDate: "2026-07-22",
  from: "07:50:00",
  to: "25:00:00",
  worldId: "fixture-world",
  worldName: "Fixture World",
};

describe("fixture-first GTFS importer", () => {
  beforeEach(async () => {
    await rm(tmpRoot, { recursive: true, force: true });
    await mkdir(tmpRoot, { recursive: true });
  });

  it("produces equivalent normalised output from directory and ZIP sources", async () => {
    const directory = path.join(tmpRoot, "feed");
    const zipPath = path.join(tmpRoot, "feed.zip");
    const files = createFixtureFeed();
    await writeFixtureDirectory(directory, files);
    await writeFixtureZip(zipPath, files);

    const directoryPack = await importGtfs(new DirectoryGtfsSource(directory), baseOptions);
    const zipPack = await importGtfs(new ZipGtfsSource(zipPath), baseOptions);

    expect(zipPack.manifest).toEqual(directoryPack.manifest);
    expect(zipPack.network).toEqual(directoryPack.network);
    expect(zipPack.services).toEqual(directoryPack.services);
    expect(zipPack.provenance.sourceKind).toBe("zip");
    expect(directoryPack.provenance.sourceKind).toBe("directory");
  });

  it("validates required files", async () => {
    const directory = path.join(tmpRoot, "missing-required");
    await writeFixtureDirectory(directory, createFixtureFeed({ missingRequiredFile: "stops.txt" }));

    await expect(validateRequiredFiles(new DirectoryGtfsSource(directory))).rejects.toThrow("stops.txt");
  });

  it("parses quoted CSV values containing commas", async () => {
    const pack = await importFixture();
    const route = pack.services.routes.find((candidate) => candidate.routeId === "R1");

    expect(route?.routeLongName).toBe("Blue Line, Inner");
  });

  it("resolves active services and calendar-date exceptions", async () => {
    const pack = await importFixture();
    const tripIds = pack.services.trips.map((trip) => trip.tripId);

    expect(tripIds).toContain("r1-out-1");
    expect(tripIds).toContain("r2-east-1");
    expect(tripIds).not.toContain("inactive-1");
    expect(tripIds).not.toContain("removed-1");
  });

  it("supports GTFS times greater than 24 hours", async () => {
    const pack = await importFixture();
    const lateTrip = pack.services.trips.find((trip) => trip.tripId === "r2-east-1");

    expect(lateTrip?.startSeconds).toBe(87_030);
    expect(lateTrip?.endSeconds).toBe(87_900);
  });

  it("groups platform stops under parent stations while retaining platform metadata", async () => {
    const pack = await importFixture();
    const north = pack.network.stations.find((station) => station.sourceStopId === "north");

    expect(north?.platformStopIds).toEqual(["north-p1", "north-p2"]);
    expect(pack.network.platforms.find((platform) => platform.stopId === "north-p1")?.stationId).toBe(
      north?.id,
    );
  });

  it("constructs directed transit edges, including opposite directions", async () => {
    const pack = await importFixture();
    const edgePairs = pack.network.edges.map((edge) => `${edge.routeId}:${edge.fromStationId}->${edge.toStationId}`);

    expect(edgePairs).toContain("R1:station-north->station-junction");
    expect(edgePairs).toContain("R1:station-south->station-junction");
  });

  it("filters and attaches selected route shapes", async () => {
    const pack = await importFixture();
    const shapeIds = pack.network.shapes.map((shape) => shape.shapeId);

    expect(shapeIds).toEqual(["shape-r1", "shape-r1-rev", "shape-r2"]);
    expect(pack.network.shapes.find((shape) => shape.shapeId === "shape-r2")?.points).toHaveLength(3);
  });

  it("exports deterministic world-pack files", async () => {
    const pack = await importFixture();
    const first = path.join(tmpRoot, "out-a");
    const second = path.join(tmpRoot, "out-b");

    await exportWorldPack(pack, first);
    await exportWorldPack(pack, second);

    await expect(readFile(path.join(second, "manifest.json"), "utf8")).resolves.toBe(
      await readFile(path.join(first, "manifest.json"), "utf8"),
    );
    await expect(readFile(path.join(second, "network.json"), "utf8")).resolves.toBe(
      await readFile(path.join(first, "network.json"), "utf8"),
    );
  });

  it("reports invalid references as warnings", async () => {
    const pack = await importFixture(createFixtureFeed({ malformedReference: true }));

    expect(pack.network.warnings.some((warning) => warning.includes("unknown trip ghost-trip"))).toBe(true);
  });

  it("emits a bounded fixture candidate-subset report", async () => {
    const report = await buildCandidateSubsetReport(await importFixture());
    const candidate = report.candidates[0]!;

    expect(candidate.stationCount).toBeGreaterThanOrEqual(5);
    expect(candidate.routeIds).toEqual(["R1", "R2"]);
    expect(candidate.transferStations.map((station) => station.name)).toContain("Harbour Junction");
    expect(candidate.medianScheduledHeadwaySeconds).toBeGreaterThan(0);
  });

  it("matches entry/exit records exactly against parent stations", async () => {
    const records = await readEntryExitRecords(
      bufferToTextStream(
        Buffer.from("MonthYear,Station,Station_Type,Entry_Exit,Trip\nJul-2026,Harbour Junction,Metro,Entry,120\n"),
      ),
    );
    const match = matchEntryExitStation(records[0]!.stationName, [
      { stationId: "station-junction", name: "Harbour Junction" },
    ]);

    expect(records[0]?.trip).toEqual({ kind: "exact", value: 120 });
    expect(match.candidates[0]?.matchType).toBe("exact");
    expect(match.requiresManualReview).toBe(false);
  });

  it("reports ambiguous entry/exit fuzzy matches for manual review", () => {
    const match = matchEntryExitStation("Harbour Jn", [
      { stationId: "station-harbour-junction", name: "Harbour Junction" },
      { stationId: "station-harbour-junction-east", name: "Harbour Junction East" },
    ]);

    expect(match.candidates.length).toBeGreaterThan(1);
    expect(match.requiresManualReview).toBe(true);
  });

  it("preserves 'Less than 50' as censored data", async () => {
    const records = await readEntryExitRecords(
      bufferToTextStream(
        Buffer.from(
          "MonthYear,Station,Station_Type,Entry_Exit,Trip\nJul-2026,Quiet Stop,Metro,Exit,Less than 50\n",
        ),
      ),
    );

    expect(records[0]?.trip).toEqual({
      kind: "censored-less-than",
      upperBoundExclusive: 50,
      raw: "Less than 50",
    });
  });

  it("applies route type and geographic bounding filters", async () => {
    const directory = path.join(tmpRoot, "filtered");
    await writeFixtureDirectory(directory, createFixtureFeed());
    const pack = await importGtfs(new DirectoryGtfsSource(directory), {
      ...baseOptions,
      routeTypes: [2],
      bbox: { minLon: 151.199, minLat: -33.881, maxLon: 151.211, maxLat: -33.869 },
    });

    expect(pack.services.routes.map((route) => route.routeId)).toEqual(["R1"]);
    expect(pack.network.stations.map((station) => station.sourceStopId).sort()).toEqual([
      "junction",
      "north",
      "south",
    ]);
  });
});

async function importFixture(files = createFixtureFeed()) {
  const directory = path.join(tmpRoot, "feed");
  await writeFixtureDirectory(directory, files);

  return importGtfs(new DirectoryGtfsSource(directory), baseOptions);
}
