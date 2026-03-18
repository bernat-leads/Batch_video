import { test, expect } from "./fixtures";

test.describe("smoke — basic page loads", () => {
  test("home page loads", async ({ authedPage: page }) => {
    await page.goto("/app");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("settings page loads", async ({ authedPage: page }) => {
    await page.goto("/app/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  });

  test("videos page loads", async ({ authedPage: page }) => {
    await page.goto("/app/videos");
    await expect(page.getByRole("heading", { name: "Videos" })).toBeVisible();
  });

  test("batches page loads", async ({ authedPage: page }) => {
    await page.goto("/app/batches");
    await expect(page.getByRole("heading", { name: "Batches" })).toBeVisible();
  });

  test("navigation between pages", async ({ authedPage: page }) => {
    await page.goto("/app");
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();

    await page.getByRole("link", { name: "Videos" }).click();
    await expect(page.getByRole("heading", { name: "Videos", exact: true })).toBeVisible();
  });
});
