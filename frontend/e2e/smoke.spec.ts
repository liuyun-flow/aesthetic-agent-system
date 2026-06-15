import { test, expect } from "@playwright/test";

// Thin smoke E2E: the app boots against a live backend and the core routes
// render. Deliberately avoids any LLM-backed flow (analyze/critique) so it
// needs no API key and stays deterministic.

test("home renders the task form", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /运行/ })).toBeVisible();
  await expect(page.getByText(/作品描述/)).toBeVisible();
});

test("help center renders", async ({ page }) => {
  await page.goto("/help");
  await expect(page.getByText(/帮助中心/).first()).toBeVisible();
});

test("settings page renders", async ({ page }) => {
  await page.goto("/settings");
  await expect(page.getByText(/系统设置/).first()).toBeVisible();
});

test("assessment page renders", async ({ page }) => {
  await page.goto("/assessment");
  await expect(page.getByText(/训练效果评估/).first()).toBeVisible();
});
