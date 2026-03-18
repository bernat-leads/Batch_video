import { test, expect } from "./fixtures";

test.describe("dashboard — empty state", () => {
  test("shows zero stats on empty dashboard", async ({ authedPage: page }) => {
    await page.goto("/app");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });
});

test.describe("dashboard — with data", () => {
  test("shows stats cards with data", async ({ authedPageWithData: { page } }) => {
    await page.goto("/app");

    // Stats cards should render — check for the "Total" heading
    await expect(page.getByText("Total Videos")).toBeVisible();
    await expect(page.getByText("Generated")).toBeVisible();
  });

  test("recent batches table shows batch names", async ({ authedPageWithData: { page, data } }) => {
    await page.goto("/app");

    for (const batch of data.batches) {
      await expect(page.getByText(batch.name)).toBeVisible();
    }
  });

  test("'View all' link for batches navigates to batches page", async ({ authedPageWithData: { page } }) => {
    await page.goto("/app");

    const viewAllLinks = page.getByRole("link", { name: "View all" });
    // The first "View all" corresponds to batches section
    await viewAllLinks.first().click();

    await expect(page).toHaveURL(/\/app\/batches/);
    await expect(page.getByRole("heading", { name: "Batches" })).toBeVisible();
  });

  test("'View all' link for videos navigates to videos page", async ({ authedPageWithData: { page } }) => {
    await page.goto("/app");

    const viewAllLinks = page.getByRole("link", { name: "View all" });
    // The last "View all" corresponds to videos section
    await viewAllLinks.last().click();

    await expect(page).toHaveURL(/\/app\/videos/);
    await expect(page.getByRole("heading", { name: "Videos", exact: true })).toBeVisible();
  });
});
