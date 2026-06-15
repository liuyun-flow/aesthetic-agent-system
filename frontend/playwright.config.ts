import { defineConfig, devices } from "@playwright/test";

// Backend command is env-configurable: locally pass the Python 3.11 interpreter
// (bare `python` here lacks deps); CI uses plain `python` after pip install.
const BACKEND_CMD =
  process.env.E2E_BACKEND_CMD ||
  "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: BACKEND_CMD,
      cwd: "../backend",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      // Isolated DB so the smoke run never touches dev data.
      env: { DATABASE_URL: "sqlite:///./data/database/e2e.db" },
    },
    {
      command: "npm run dev -- -p 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
