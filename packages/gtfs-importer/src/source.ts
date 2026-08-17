import { createReadStream } from "node:fs";
import { open, opendir, stat } from "node:fs/promises";
import path from "node:path";
import { PassThrough } from "node:stream";
import { createInflateRaw } from "node:zlib";

export interface GtfsSource {
  readonly kind: "directory" | "zip";
  hasFile(name: string): Promise<boolean>;
  listFiles(): Promise<string[]>;
  openTextStream(name: string): Promise<NodeJS.ReadableStream>;
}

interface ZipEntry {
  name: string;
  compressedSize: number;
  compressionMethod: number;
  localHeaderOffset: number;
}

export class DirectoryGtfsSource implements GtfsSource {
  readonly kind = "directory" as const;

  constructor(private readonly rootDirectory: string) {}

  async hasFile(name: string): Promise<boolean> {
    try {
      const fileStat = await stat(this.resolveFile(name));
      return fileStat.isFile();
    } catch {
      return false;
    }
  }

  async listFiles(): Promise<string[]> {
    const files: string[] = [];
    const directory = await opendir(this.rootDirectory);

    for await (const entry of directory) {
      if (entry.isFile()) {
        files.push(entry.name);
      }
    }

    return files.sort();
  }

  async openTextStream(name: string): Promise<NodeJS.ReadableStream> {
    if (!(await this.hasFile(name))) {
      throw new Error(`GTFS file not found: ${name}`);
    }

    return createReadStream(this.resolveFile(name), { encoding: "utf8" });
  }

  private resolveFile(name: string): string {
    return path.join(this.rootDirectory, path.basename(name));
  }
}

export class ZipGtfsSource implements GtfsSource {
  readonly kind = "zip" as const;

  private entriesPromise: Promise<Map<string, ZipEntry>> | undefined;

  constructor(private readonly zipPath: string) {}

  async hasFile(name: string): Promise<boolean> {
    const entries = await this.loadEntries();
    return entries.has(path.basename(name));
  }

  async listFiles(): Promise<string[]> {
    const entries = await this.loadEntries();
    return [...entries.keys()].sort();
  }

  async openTextStream(name: string): Promise<NodeJS.ReadableStream> {
    const entries = await this.loadEntries();
    const entry = entries.get(path.basename(name));

    if (!entry) {
      throw new Error(`GTFS file not found in ZIP: ${name}`);
    }

    const handle = await open(this.zipPath, "r");

    try {
      const localHeader = Buffer.alloc(30);
      await handle.read(localHeader, 0, localHeader.length, entry.localHeaderOffset);

      if (localHeader.readUInt32LE(0) !== 0x04034b50) {
        throw new Error(`Invalid ZIP local header for ${entry.name}`);
      }

      const fileNameLength = localHeader.readUInt16LE(26);
      const extraLength = localHeader.readUInt16LE(28);
      const dataStart = entry.localHeaderOffset + localHeader.length + fileNameLength + extraLength;
      const compressedStream = createReadStream(this.zipPath, {
        start: dataStart,
        end: dataStart + entry.compressedSize - 1,
      });

      if (entry.compressionMethod === 0) {
        return compressedStream;
      }

      if (entry.compressionMethod === 8) {
        return compressedStream.pipe(createInflateRaw());
      }

      throw new Error(`Unsupported ZIP compression method ${entry.compressionMethod} for ${entry.name}`);
    } finally {
      await handle.close();
    }
  }

  private loadEntries(): Promise<Map<string, ZipEntry>> {
    this.entriesPromise ??= this.readEntries();
    return this.entriesPromise;
  }

  private async readEntries(): Promise<Map<string, ZipEntry>> {
    const handle = await open(this.zipPath, "r");

    try {
      const { size } = await handle.stat();
      const tailLength = Math.min(size, 65_557);
      const tail = Buffer.alloc(tailLength);
      await handle.read(tail, 0, tail.length, size - tailLength);

      const eocdOffset = findEndOfCentralDirectory(tail);
      const centralDirectorySize = tail.readUInt32LE(eocdOffset + 12);
      const centralDirectoryOffset = tail.readUInt32LE(eocdOffset + 16);
      const centralDirectory = Buffer.alloc(centralDirectorySize);
      await handle.read(centralDirectory, 0, centralDirectory.length, centralDirectoryOffset);

      return parseCentralDirectory(centralDirectory);
    } finally {
      await handle.close();
    }
  }
}

export async function createGtfsSource(inputPath: string): Promise<GtfsSource> {
  const inputStat = await stat(inputPath);

  if (inputStat.isDirectory()) {
    return new DirectoryGtfsSource(inputPath);
  }

  if (inputStat.isFile() && inputPath.toLowerCase().endsWith(".zip")) {
    return new ZipGtfsSource(inputPath);
  }

  throw new Error(`GTFS input must be an extracted directory or .zip file: ${inputPath}`);
}

function findEndOfCentralDirectory(tail: Buffer): number {
  for (let offset = tail.length - 22; offset >= 0; offset -= 1) {
    if (tail.readUInt32LE(offset) === 0x06054b50) {
      return offset;
    }
  }

  throw new Error("ZIP end-of-central-directory record not found");
}

function parseCentralDirectory(centralDirectory: Buffer): Map<string, ZipEntry> {
  const entries = new Map<string, ZipEntry>();
  let offset = 0;

  while (offset < centralDirectory.length) {
    if (centralDirectory.readUInt32LE(offset) !== 0x02014b50) {
      break;
    }

    const compressionMethod = centralDirectory.readUInt16LE(offset + 10);
    const compressedSize = centralDirectory.readUInt32LE(offset + 20);
    const fileNameLength = centralDirectory.readUInt16LE(offset + 28);
    const extraLength = centralDirectory.readUInt16LE(offset + 30);
    const commentLength = centralDirectory.readUInt16LE(offset + 32);
    const localHeaderOffset = centralDirectory.readUInt32LE(offset + 42);
    const rawName = centralDirectory
      .subarray(offset + 46, offset + 46 + fileNameLength)
      .toString("utf8")
      .replaceAll("\\", "/");
    const baseName = path.posix.basename(rawName);

    if (baseName && !entries.has(baseName)) {
      entries.set(baseName, {
        name: rawName,
        compressedSize,
        compressionMethod,
        localHeaderOffset,
      });
    }

    offset += 46 + fileNameLength + extraLength + commentLength;
  }

  return entries;
}

export function bufferToTextStream(buffer: Buffer): NodeJS.ReadableStream {
  const stream = new PassThrough();
  stream.end(buffer);
  return stream;
}
