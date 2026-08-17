#!/usr/bin/env node
import {
  buildCandidateSubsetReport,
  createGtfsSource,
  exportCandidateReport,
  exportWorldPack,
  importGtfs,
  type ImportGtfsOptions,
} from "./index";

interface ParsedArgs {
  command: "import" | "candidates";
  input: string;
  serviceDate: string;
  from: string;
  to: string;
  output: string;
  bbox?: ImportGtfsOptions["bbox"];
  routeIds?: string[];
  routeTypes?: number[];
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const source = await createGtfsSource(args.input);
  const importOptions: ImportGtfsOptions = {
    serviceDate: args.serviceDate,
    from: args.from,
    to: args.to,
  };

  if (args.bbox) {
    importOptions.bbox = args.bbox;
  }

  if (args.routeIds) {
    importOptions.routeIds = args.routeIds;
  }

  if (args.routeTypes) {
    importOptions.routeTypes = args.routeTypes;
  }

  const pack = await importGtfs(source, importOptions);

  if (args.command === "import") {
    await exportWorldPack(pack, args.output);
    console.log(`Wrote world pack to ${args.output}`);
    return;
  }

  const report = await buildCandidateSubsetReport(pack);
  await exportCandidateReport(report, args.output);
  console.log(`Wrote candidate report to ${args.output}`);
}

function parseArgs(argv: string[]): ParsedArgs {
  const [command, ...rest] = argv;

  if (command !== "import" && command !== "candidates") {
    throw new Error("Usage: branchlab-gtfs <import|candidates> --input PATH --service-date YYYY-MM-DD --from HH:MM:SS --to HH:MM:SS --output PATH");
  }

  const values = new Map<string, string>();

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];

    if (!token?.startsWith("--")) {
      continue;
    }

    const value = rest[index + 1];

    if (value === undefined || value.startsWith("--")) {
      throw new Error(`Missing value for ${token}`);
    }

    values.set(token.slice(2), value);
    index += 1;
  }

  const input = requireArg(values, "input");
  const serviceDate = requireArg(values, "service-date");
  const from = requireArg(values, "from");
  const to = requireArg(values, "to");
  const output = requireArg(values, "output");

  const parsed: ParsedArgs = {
    command,
    input,
    serviceDate,
    from,
    to,
    output,
  };

  if (values.has("bbox")) {
    parsed.bbox = parseBbox(values.get("bbox")!);
  }

  if (values.has("route-ids")) {
    parsed.routeIds = splitCsv(values.get("route-ids")!);
  }

  if (values.has("route-types")) {
    parsed.routeTypes = splitCsv(values.get("route-types")!).map(Number);
  }

  return parsed;
}

function requireArg(values: Map<string, string>, key: string): string {
  const value = values.get(key);

  if (!value) {
    throw new Error(`Missing required --${key}`);
  }

  return value;
}

function parseBbox(value: string): ParsedArgs["bbox"] {
  const [minLon, minLat, maxLon, maxLat] = value.split(",").map(Number);

  if ([minLon, minLat, maxLon, maxLat].some((coordinate) => Number.isNaN(coordinate))) {
    throw new Error("--bbox must be minLon,minLat,maxLon,maxLat");
  }

  return { minLon: minLon!, minLat: minLat!, maxLon: maxLon!, maxLat: maxLat! };
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
