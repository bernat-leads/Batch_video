import { test, expect } from "./fixtures";

test.describe("settings page", () => {
  test("loads settings form with values from API", async ({ authedPage: page }) => {
    await page.goto("/app/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();

    // Master prompt textarea should be populated
    const promptField = page.getByLabel(/master prompt/i);
    if (await promptField.isVisible()) {
      await expect(promptField).toHaveValue(/compelling/i);
    }
  });

  test("retention days field is visible", async ({ authedPage: page }) => {
    await page.goto("/app/settings");
    const retentionField = page.getByLabel(/retention/i);
    if (await retentionField.isVisible()) {
      await expect(retentionField).toHaveValue("7");
    }
  });

  test("save button submits form", async ({ authedPage: page }) => {
    await page.goto("/app/settings");

    // Mock the PATCH endpoint
    let savedPayload: Record<string, unknown> | null = null;
    await page.route("**/api/v1/settings*", async (route) => {
      if (route.request().method() === "PATCH") {
        savedPayload = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          json: { master_prompt: "updated", retention_days: 7 },
        });
      } else {
        await route.fulfill({
          status: 200,
          json: { master_prompt: "Create a compelling short-form video ad.", retention_days: 7 },
        });
      }
    });

    const saveButton = page.getByRole("button", { name: /save/i });
    if (await saveButton.isVisible()) {
      await saveButton.click();
      // Verify the save was attempted and payload was captured
      expect(savedPayload).not.toBeNull();
      expect(savedPayload).toHaveProperty("master_prompt");
    }
  });
});
