import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  // Mock authenticated session so routes are accessible
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 200, json: { authenticated: true } }),
  );
});

test("home page loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
});

test("about page loads", async ({ page }) => {
  await page.goto("/about");
  await expect(page.getByRole("heading", { name: "About" })).toBeVisible();
});

test("navigation between pages", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "About" }).click();
  await expect(page.getByRole("heading", { name: "About" })).toBeVisible();

  await page.getByRole("link", { name: "Home" }).click();
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
});
