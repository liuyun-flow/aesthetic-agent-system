import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Default stub so components that fetch on mount (e.g. /vision/status) don't hit
// the network. Individual tests can override global.fetch as needed.
global.fetch = vi.fn(() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
) as unknown as typeof fetch;

afterEach(() => {
  cleanup();
});
