import type { EntryExitRecord, EntryExitStationMatch } from "@branchlab/schemas";
import { EntryExitRecordSchema, EntryExitStationMatchSchema } from "@branchlab/schemas";

import { parseCsvRows } from "./csv";

export interface MatchableStation {
  stationId: string;
  name: string;
}

export async function readEntryExitRecords(stream: NodeJS.ReadableStream): Promise<EntryExitRecord[]> {
  const records: EntryExitRecord[] = [];

  for await (const row of parseCsvRows(stream)) {
    records.push(
      EntryExitRecordSchema.parse({
        monthYear: csvValue(row, "MonthYear"),
        stationName: csvValue(row, "Station"),
        normalizedStationName: normalizeStationName(csvValue(row, "Station")),
        stationType: csvValue(row, "Station_Type"),
        entryExit: csvValue(row, "Entry_Exit"),
        trip: parseTripValue(csvValue(row, "Trip")),
      }),
    );
  }

  return records;
}

function csvValue(row: Record<string, string>, key: string): string {
  return row[key] ?? "";
}

export function matchEntryExitStation(
  sourceStationName: string,
  parentStations: MatchableStation[],
): EntryExitStationMatch {
  const normalizedStationName = normalizeStationName(sourceStationName);
  const exactMatches = parentStations
    .filter((station) => normalizeStationName(station.name) === normalizedStationName)
    .map((station) => ({
      stationId: station.stationId,
      name: station.name,
      confidence: 1,
      matchType: "exact" as const,
    }));

  if (exactMatches.length > 0) {
    return EntryExitStationMatchSchema.parse({
      sourceStationName,
      normalizedStationName,
      candidates: exactMatches.sort((left, right) => left.stationId.localeCompare(right.stationId)),
      requiresManualReview: exactMatches.length > 1,
    });
  }

  const fuzzyMatches = parentStations
    .map((station) => ({
      stationId: station.stationId,
      name: station.name,
      confidence: fuzzyScore(normalizedStationName, normalizeStationName(station.name)),
      matchType: "fuzzy" as const,
    }))
    .filter((candidate) => candidate.confidence >= 0.33)
    .sort((left, right) => right.confidence - left.confidence || left.stationId.localeCompare(right.stationId))
    .slice(0, 3);
  const bestConfidence = fuzzyMatches[0]?.confidence ?? 0;
  const closeBestCount = fuzzyMatches.filter((candidate) => bestConfidence - candidate.confidence <= 0.05).length;

  return EntryExitStationMatchSchema.parse({
    sourceStationName,
    normalizedStationName,
    candidates: fuzzyMatches,
    requiresManualReview: fuzzyMatches.length !== 1 || bestConfidence < 0.8 || closeBestCount > 1,
  });
}

export function normalizeStationName(value: string): string {
  return value
    .toLowerCase()
    .replace(/\bstation\b/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

function parseTripValue(value: string): EntryExitRecord["trip"] {
  const trimmed = value.trim();
  const censoredMatch = /^less than\s+(\d+)$/i.exec(trimmed);

  if (censoredMatch) {
    return {
      kind: "censored-less-than",
      upperBoundExclusive: Number(censoredMatch[1]),
      raw: value,
    };
  }

  return {
    kind: "exact",
    value: Number(trimmed.replaceAll(",", "")),
  };
}

function fuzzyScore(left: string, right: string): number {
  if (left === right) {
    return 1;
  }

  const leftTokens = new Set(left.split(" ").filter(Boolean));
  const rightTokens = new Set(right.split(" ").filter(Boolean));
  const intersection = [...leftTokens].filter((token) => rightTokens.has(token)).length;
  const union = new Set([...leftTokens, ...rightTokens]).size || 1;
  const tokenScore = intersection / union;
  const distanceScore = 1 - levenshtein(left, right) / Math.max(left.length, right.length, 1);

  return Number(Math.max(tokenScore, distanceScore).toFixed(3));
}

function levenshtein(left: string, right: string): number {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);

  for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
    const current = [leftIndex];

    for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
      const cost = left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1;
      current[rightIndex] = Math.min(
        current[rightIndex - 1]! + 1,
        previous[rightIndex]! + 1,
        previous[rightIndex - 1]! + cost,
      );
    }

    previous.splice(0, previous.length, ...current);
  }

  return previous[right.length] ?? 0;
}
