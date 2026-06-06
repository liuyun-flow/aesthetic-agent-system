/** Safely parse a JSON string. Returns the parsed value, or the original string on failure. */
export function parseMaybeJson(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

/** Format a value for display. Never returns "undefined" or "null". */
export function formatDisplayValue(value: unknown): string {
  if (value === null || value === undefined) return "暂无";
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed === "") return "暂无";
    // Try to parse as JSON first
    const parsed = parseMaybeJson(trimmed);
    if (typeof parsed === "string") return parsed;
    if (Array.isArray(parsed)) return parsed.join("\n");
    if (typeof parsed === "object") return JSON.stringify(parsed, null, 2);
    return String(parsed);
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return "暂无";
    return value.map((v) => String(v)).join("\n");
  }
  return String(value);
}

/** Convert any value to a string array for list display. */
export function toDisplayList(value: unknown): string[] {
  if (value === null || value === undefined) return [];
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed === "") return [];
    const parsed = parseMaybeJson(trimmed);
    if (Array.isArray(parsed)) return parsed.map((v) => String(v));
    return [trimmed];
  }
  if (Array.isArray(value)) return value.map((v) => String(v));
  return [String(value)];
}

/** Check if a value is "empty" for display purposes. */
export function isEmptyValue(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string" && value.trim() === "") return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
}
