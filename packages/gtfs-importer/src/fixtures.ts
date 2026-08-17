import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { deflateRawSync } from "node:zlib";

export interface FixtureFeedOptions {
  malformedReference?: boolean;
  missingRequiredFile?: string;
}

export function createFixtureFeed(options: FixtureFeedOptions = {}): Record<string, string> {
  const files: Record<string, string> = {
    "agency.txt": csv([
      ["agency_id", "agency_name", "agency_url", "agency_timezone"],
      ["A1", "BranchLab Transit", "https://example.test", "Australia/Sydney"],
    ]),
    "stops.txt": csv([
      [
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
        "location_type",
        "parent_station",
        "platform_code",
      ],
      ["north", "North Central", "-33.8700", "151.2000", "1", "", ""],
      ["north-p1", "North Central Platform 1", "-33.8701", "151.2001", "0", "north", "1"],
      ["north-p2", "North Central Platform 2", "-33.8702", "151.2002", "0", "north", "2"],
      ["junction", "Harbour Junction", "-33.8750", "151.2050", "1", "", ""],
      ["junction-p1", "Harbour Junction Platform 1", "-33.8751", "151.2051", "0", "junction", "1"],
      ["junction-p2", "Harbour Junction Platform 2", "-33.8752", "151.2052", "0", "junction", "2"],
      ["south", "South Park", "-33.8800", "151.2100", "1", "", ""],
      ["south-p1", "South Park Platform 1", "-33.8801", "151.2101", "0", "south", "1"],
      ["west", "West Market", "-33.8760", "151.1900", "1", "", ""],
      ["west-p1", "West Market Platform 1", "-33.8761", "151.1901", "0", "west", "1"],
      ["east", "East Pier", "-33.8760", "151.2200", "1", "", ""],
      ["east-p1", "East Pier Platform 1", "-33.8761", "151.2201", "0", "east", "1"],
    ]),
    "routes.txt": csv([
      [
        "route_id",
        "agency_id",
        "route_short_name",
        "route_long_name",
        "route_desc",
        "route_type",
        "route_color",
        "route_text_color",
      ],
      ["R1", "A1", "B1", "Blue Line, Inner", "", "2", "00AEEF", "FFFFFF"],
      ["R2", "A1", "G1", "Green Cross Line", "", "0", "00AA66", "111111"],
      ["R3", "A1", "Z9", "Inactive Line", "", "2", "999999", "111111"],
    ]),
    "calendar.txt": csv([
      ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
      ["WEEK", "1", "1", "1", "1", "1", "0", "0", "20260701", "20260731"],
      ["INACTIVE", "0", "0", "0", "0", "0", "0", "0", "20260701", "20260731"],
      ["REMOVED", "1", "1", "1", "1", "1", "0", "0", "20260701", "20260731"],
    ]),
    "calendar_dates.txt": csv([
      ["service_id", "date", "exception_type"],
      ["SPECIAL", "20260722", "1"],
      ["REMOVED", "20260722", "2"],
    ]),
    "trips.txt": csv([
      ["route_id", "service_id", "trip_id", "shape_id", "trip_headsign", "direction_id"],
      ["R1", "WEEK", "r1-out-1", "shape-r1", "South", "0"],
      ["R1", "WEEK", "r1-out-2", "shape-r1", "South", "0"],
      ["R1", "WEEK", "r1-in-1", "shape-r1-rev", "North", "1"],
      ["R2", "SPECIAL", "r2-east-1", "shape-r2", "East", "0"],
      ["R3", "INACTIVE", "inactive-1", "shape-r3", "Nowhere", "0"],
      ["R2", "REMOVED", "removed-1", "shape-r2", "Removed", "0"],
    ]),
    "stop_times.txt": csv([
      ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
      ["r1-out-1", "08:00:00", "08:00:30", "north-p1", "1"],
      ["r1-out-1", "08:04:00", "08:04:30", "junction-p1", "2"],
      ["r1-out-1", "08:09:00", "08:09:00", "south-p1", "3"],
      ["r1-out-2", "08:10:00", "08:10:30", "north-p2", "1"],
      ["r1-out-2", "08:14:00", "08:14:30", "junction-p1", "2"],
      ["r1-out-2", "08:19:00", "08:19:00", "south-p1", "3"],
      ["r1-in-1", "08:20:00", "08:20:30", "south-p1", "1"],
      ["r1-in-1", "08:25:00", "08:25:30", "junction-p1", "2"],
      ["r1-in-1", "08:30:00", "08:30:00", "north-p1", "3"],
      ["r2-east-1", "24:10:00", "24:10:30", "west-p1", "1"],
      ["r2-east-1", "24:17:00", "24:17:30", "junction-p2", "2"],
      ["r2-east-1", "24:25:00", "24:25:00", "east-p1", "3"],
      ["inactive-1", "08:00:00", "08:01:00", "north-p1", "1"],
      ["inactive-1", "08:02:00", "08:02:30", "south-p1", "2"],
      ["removed-1", "08:00:00", "08:01:00", "west-p1", "1"],
      ["removed-1", "08:02:00", "08:02:30", "east-p1", "2"],
    ]),
    "shapes.txt": csv([
      ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
      ["shape-r1", "-33.8701", "151.2001", "1"],
      ["shape-r1", "-33.8751", "151.2051", "2"],
      ["shape-r1", "-33.8801", "151.2101", "3"],
      ["shape-r1-rev", "-33.8801", "151.2101", "1"],
      ["shape-r1-rev", "-33.8751", "151.2051", "2"],
      ["shape-r1-rev", "-33.8701", "151.2001", "3"],
      ["shape-r2", "-33.8761", "151.1901", "1"],
      ["shape-r2", "-33.8752", "151.2052", "2"],
      ["shape-r2", "-33.8761", "151.2201", "3"],
      ["shape-r3", "-33.8701", "151.2001", "1"],
      ["shape-r3", "-33.8801", "151.2101", "2"],
    ]),
    "frequencies.txt": csv([["trip_id", "start_time", "end_time", "headway_secs"]]),
    "transfers.txt": csv([["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"]]),
    "pathways.txt": csv([["pathway_id", "from_stop_id", "to_stop_id", "pathway_mode", "is_bidirectional"]]),
    "levels.txt": csv([["level_id", "level_index", "level_name"]]),
  };

  if (options.malformedReference) {
    files["stop_times.txt"] += "ghost-trip,08:00:00,08:01:00,missing-stop,1\n";
  }

  if (options.missingRequiredFile) {
    delete files[options.missingRequiredFile];
  }

  return files;
}

export async function writeFixtureDirectory(directory: string, files = createFixtureFeed()): Promise<void> {
  await mkdir(directory, { recursive: true });

  await Promise.all(
    Object.entries(files).map(([fileName, content]) => writeFile(path.join(directory, fileName), content, "utf8")),
  );
}

export async function writeFixtureZip(zipPath: string, files = createFixtureFeed()): Promise<void> {
  await mkdir(path.dirname(zipPath), { recursive: true });
  await writeFile(zipPath, createZipBuffer(files));
}

function csv(rows: string[][]): string {
  return `${rows.map((row) => row.map(escapeCsvField).join(",")).join("\n")}\n`;
}

function escapeCsvField(value: string): string {
  if (!/[",\n\r]/.test(value)) {
    return value;
  }

  return `"${value.replaceAll('"', '""')}"`;
}

function createZipBuffer(files: Record<string, string>): Buffer {
  const localParts: Buffer[] = [];
  const centralParts: Buffer[] = [];
  let offset = 0;

  for (const fileName of Object.keys(files).sort()) {
    const name = Buffer.from(fileName, "utf8");
    const content = Buffer.from(files[fileName] ?? "", "utf8");
    const compressed = deflateRawSync(content);
    const checksum = crc32(content);
    const localHeader = Buffer.alloc(30);
    localHeader.writeUInt32LE(0x04034b50, 0);
    localHeader.writeUInt16LE(20, 4);
    localHeader.writeUInt16LE(8, 8);
    localHeader.writeUInt32LE(checksum, 14);
    localHeader.writeUInt32LE(compressed.length, 18);
    localHeader.writeUInt32LE(content.length, 22);
    localHeader.writeUInt16LE(name.length, 26);
    localParts.push(localHeader, name, compressed);

    const centralHeader = Buffer.alloc(46);
    centralHeader.writeUInt32LE(0x02014b50, 0);
    centralHeader.writeUInt16LE(20, 4);
    centralHeader.writeUInt16LE(20, 6);
    centralHeader.writeUInt16LE(8, 10);
    centralHeader.writeUInt32LE(checksum, 16);
    centralHeader.writeUInt32LE(compressed.length, 20);
    centralHeader.writeUInt32LE(content.length, 24);
    centralHeader.writeUInt16LE(name.length, 28);
    centralHeader.writeUInt32LE(offset, 42);
    centralParts.push(centralHeader, name);
    offset += localHeader.length + name.length + compressed.length;
  }

  const centralDirectoryOffset = offset;
  const centralDirectory = Buffer.concat(centralParts);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(Object.keys(files).length, 8);
  end.writeUInt16LE(Object.keys(files).length, 10);
  end.writeUInt32LE(centralDirectory.length, 12);
  end.writeUInt32LE(centralDirectoryOffset, 16);

  return Buffer.concat([...localParts, centralDirectory, end]);
}

function crc32(buffer: Buffer): number {
  let crc = 0xffffffff;

  for (const byte of buffer) {
    crc ^= byte;

    for (let bit = 0; bit < 8; bit += 1) {
      crc = crc & 1 ? (crc >>> 1) ^ 0xedb88320 : crc >>> 1;
    }
  }

  return (crc ^ 0xffffffff) >>> 0;
}
