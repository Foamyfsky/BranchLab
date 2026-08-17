export function parseGtfsTimeToSeconds(value: string): number {
  const match = /^(\d+):([0-5]\d):([0-5]\d)$/.exec(value);

  if (!match) {
    throw new Error(`Invalid GTFS time: ${value}`);
  }

  return Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]);
}

export function toGtfsDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);

  if (!match) {
    throw new Error(`Expected service date as YYYY-MM-DD: ${value}`);
  }

  return `${match[1]}${match[2]}${match[3]}`;
}

export function weekdayFieldForDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);

  if (!match) {
    throw new Error(`Expected service date as YYYY-MM-DD: ${value}`);
  }

  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  const fields = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

  return fields[date.getUTCDay()] ?? "sunday";
}

export function median(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }

  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);

  if (sorted.length % 2 === 1) {
    return sorted[middle] ?? null;
  }

  const left = sorted[middle - 1] ?? 0;
  const right = sorted[middle] ?? 0;

  return Math.round((left + right) / 2);
}
