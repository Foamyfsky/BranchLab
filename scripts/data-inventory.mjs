import { open, opendir, stat } from "node:fs/promises";
import path from "node:path";

const probableGtfsFiles = new Set([
  "agency.txt",
  "attributions.txt",
  "calendar.txt",
  "calendar_dates.txt",
  "fare_attributes.txt",
  "fare_rules.txt",
  "feed_info.txt",
  "frequencies.txt",
  "levels.txt",
  "pathways.txt",
  "routes.txt",
  "shapes.txt",
  "stop_times.txt",
  "stops.txt",
  "transfers.txt",
  "translations.txt",
  "trips.txt",
]);

const headerExtensions = new Set([".csv", ".txt"]);
const maxHeaderBytes = 64 * 1024;

async function* walk(directory) {
  const entries = await opendir(directory);

  for await (const entry of entries) {
    const entryPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      yield* walk(entryPath);
      continue;
    }

    if (entry.isFile()) {
      yield entryPath;
    }
  }
}

async function readHeader(filePath) {
  if (!headerExtensions.has(path.extname(filePath).toLowerCase())) {
    return null;
  }

  const handle = await open(filePath, "r");

  try {
    const buffer = Buffer.alloc(maxHeaderBytes);
    const { bytesRead } = await handle.read(buffer, 0, buffer.length, 0);
    const firstLine = buffer.subarray(0, bytesRead).toString("utf8").split(/\r?\n/, 1)[0] ?? "";

    return firstLine.replace(/^\uFEFF/, "");
  } finally {
    await handle.close();
  }
}

async function main() {
  const input = process.argv[2] ?? "data/raw/tfnsw";
  const root = path.resolve(process.cwd(), input);
  const rootStat = await stat(root);

  if (!rootStat.isDirectory()) {
    throw new Error(`Inventory root is not a directory: ${root}`);
  }

  const files = [];

  for await (const filePath of walk(root)) {
    const fileStat = await stat(filePath);
    const basename = path.basename(filePath).toLowerCase();

    files.push({
      path: path.relative(process.cwd(), filePath).replaceAll(path.sep, "/"),
      sizeBytes: fileStat.size,
      probableGtfsFile: probableGtfsFiles.has(basename),
      csvHeader: await readHeader(filePath),
    });
  }

  files.sort((left, right) => left.path.localeCompare(right.path));

  const report = {
    root: path.relative(process.cwd(), root).replaceAll(path.sep, "/"),
    fileCount: files.length,
    files,
  };

  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
