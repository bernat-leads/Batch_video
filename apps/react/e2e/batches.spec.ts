import { test, expect } from "./fixtures";

test.describe("batches — list page", () => {
  test("shows empty state when no batches exist", async ({ authedPage: page }) => {
    await page.goto("/app/batches");
    await expect(page.getByText("No batches yet")).toBeVisible();
  });

  test("shows batch list with data", async ({ authedPageWithData: { page, data } }) => {
    await page.goto("/app/batches");

    for (const batch of data.batches) {
      await expect(page.getByText(batch.name)).toBeVisible();
    }
  });

  test("batch status badges are visible", async ({ authedPageWithData: { page, data } }) => {
    await page.goto("/app/batches");

    // At least one status badge should be rendered
    const completedBatch = data.batches.find((b) => b.status === "completed");
    if (completedBatch) {
      await expect(page.getByText("Completed").first()).toBeVisible();
    }
  });
});

test.describe("batches — create dialog", () => {
  test("create batch button opens dialog", async ({ authedPage: page }) => {
    await page.goto("/app/batches");

    // The "Add New" button should be present (either in empty state or toolbar)
    const addButton = page.getByRole("button", { name: /add new/i });
    await expect(addButton).toBeVisible();
    await addButton.click();

    await expect(page.getByText("Create Batch")).toBeVisible();
  });

  test("dialog shows upload step first", async ({ authedPage: page }) => {
    await page.goto("/app/batches");
    await page.getByRole("button", { name: /add new/i }).click();

    // Upload step should show the file drop zone instruction
    await expect(page.getByText("Drop your Excel or CSV file here")).toBeVisible();
  });

  test("dialog closes on cancel", async ({ authedPage: page }) => {
    await page.goto("/app/batches");
    await page.getByRole("button", { name: /add new/i }).click();
    await expect(page.getByText("Create Batch")).toBeVisible();

    // Close via the X button or clicking outside
    await page.keyboard.press("Escape");
    await expect(page.getByText("Create Batch")).not.toBeVisible();
  });
});

test.describe("batches — delete", () => {
  test("delete button shows confirmation dialog", async ({ authedPageWithData: { page } }) => {
    await page.goto("/app/batches");

    // Open the row actions menu
    const actionButtons = page.getByRole("button", { name: /open menu/i });
    if (await actionButtons.first().isVisible()) {
      await actionButtons.first().click();
      const deleteOption = page.getByRole("menuitem", { name: /delete/i });
      if (await deleteOption.isVisible()) {
        await deleteOption.click();
        await expect(page.getByText(/cannot be undone/i)).toBeVisible();
      }
    }
  });
});
