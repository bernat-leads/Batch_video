import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  // Mock authenticated session so routes are accessible
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 200, json: { authenticated: true } }),
  );
  // Mock batches list for dashboard
  await page.route("**/api/v1/videos/batches", (route) =>
    route.fulfill({ status: 200, json: [] }),
  );
});

test("home page loads", async ({ page }) => {
  await page.goto("/app");
  await expect(
    page.getByRole("heading", { name: "Videos" }),
  ).toBeVisible();
});

test("settings page loads", async ({ page }) => {
  // Mock settings endpoint
  await page.route("**/api/v1/settings*", (route) =>
    route.fulfill({
      status: 200,
      json: { master_prompt: "", retention_days: 7 },
    }),
  );
  await page.goto("/app/settings");
  await expect(
    page.getByRole("heading", { name: "Settings" }),
  ).toBeVisible();
});

test("navigation between pages", async ({ page }) => {
  // Mock settings endpoint
  await page.route("**/api/v1/settings*", (route) =>
    route.fulfill({
      status: 200,
      json: { master_prompt: "", retention_days: 7 },
    }),
  );

  await page.goto("/app");
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(
    page.getByRole("heading", { name: "Settings" }),
  ).toBeVisible();

  await page.getByRole("link", { name: "Videos" }).click();
  await expect(
    page.getByRole("heading", { name: "Videos" }),
  ).toBeVisible();
});
