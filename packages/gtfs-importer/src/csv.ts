export type CsvRow = Record<string, string>;

export async function* parseCsvRows(stream: NodeJS.ReadableStream): AsyncGenerator<CsvRow> {
  let header: string[] | undefined;

  for await (const record of parseCsvRecords(stream)) {
    if (record.length === 1 && record[0] === "") {
      continue;
    }

    if (!header) {
      header = record.map((field, index) => (index === 0 ? field.replace(/^\uFEFF/, "") : field));
      continue;
    }

    const row: CsvRow = {};

    for (const [index, key] of header.entries()) {
      row[key] = record[index] ?? "";
    }

    yield row;
  }
}

async function* parseCsvRecords(stream: NodeJS.ReadableStream): AsyncGenerator<string[]> {
  let field = "";
  let row: string[] = [];
  let inQuotes = false;

  for await (const chunk of stream as AsyncIterable<Buffer | string>) {
    const text = typeof chunk === "string" ? chunk : chunk.toString("utf8");

    for (let index = 0; index < text.length; index += 1) {
      const character = text[index];

      if (character === '"') {
        if (inQuotes && text[index + 1] === '"') {
          field += '"';
          index += 1;
        } else {
          inQuotes = !inQuotes;
        }
        continue;
      }

      if (character === "," && !inQuotes) {
        row.push(field);
        field = "";
        continue;
      }

      if (character === "\n" && !inQuotes) {
        row.push(field);
        yield row;
        row = [];
        field = "";
        continue;
      }

      if (character === "\r" && !inQuotes) {
        continue;
      }

      field += character;
    }
  }

  if (inQuotes) {
    throw new Error("Malformed CSV: unclosed quoted field");
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    yield row;
  }
}
