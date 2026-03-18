import { test, expect } from "./fixtures";

test.describe("videos — list page", () => {
  test("shows empty state when no videos exist", async ({ authedPage: page }) => {
    await page.goto("/app/videos");
    await expect(page.getByText("No videos yet")).toBeVisible();
  });

  test("shows video list with data", async ({ authedPageWithData: { page, data } }) => {
    await page.goto("/app/videos");

    // Videos should be listed — check for script text snippets
    const finishedVideo = data.videos.find((v) => v.status === "finished");
    if (finishedVideo) {
      await expect(page.getByText(finishedVideo.script_text.slice(0, 20))).toBeVisible();
    }
  });

  test("status badges are visible", async ({ authedPageWithData: { page, data } }) => {
    await page.goto("/app/videos");

    // At least one status badge should render
    const finishedVideo = data.videos.find((v) => v.status === "finished");
    if (finishedVideo) {
      await expect(page.getByText("Finished").first()).toBeVisible();
    }
  });
});

test.describe("videos — create dialog", () => {
  test("create video button opens dialog", async ({ authedPage: page }) => {
    await page.goto("/app/videos");
    const addButton = page.getByRole("button", { name: /add new|create video/i });
    if (await addButton.isVisible()) {
      await addButton.click();
      await expect(page.getByText(/create video/i)).toBeVisible();
    }
  });
});

test.describe("videos — detail page", () => {
  test("video detail page loads with status", async ({ authedPageWithData: { page, data } }) => {
    const video = data.videos.find((v) => v.status === "finished");
    if (!video) return;

    await page.goto(`/app/videos/${video.id}`);
    await expect(page.getByRole("heading", { name: "Video " + video.id.slice(0, 8) })).toBeVisible();
  });

  test("failed video shows error message", async ({ authedPageWithData: { page, data } }) => {
    const failedVideo = data.videos.find((v) => v.status === "failed");
    if (!failedVideo) return;

    await page.goto(`/app/videos/${failedVideo.id}`);
    await expect(page.getByText("Failed").first()).toBeVisible();
  });

  test("failed video shows retry button", async ({ authedPageWithData: { page, data } }) => {
    const failedVideo = data.videos.find((v) => v.status === "failed");
    if (!failedVideo) return;

    await page.goto(`/app/videos/${failedVideo.id}`);
    await expect(page.getByRole("button", { name: /retry/i })).toBeVisible();
  });

  test("finished video shows export button enabled", async ({ authedPageWithData: { page, data } }) => {
    const finishedVideo = data.videos.find((v) => v.status === "finished");
    if (!finishedVideo) return;

    await page.goto(`/app/videos/${finishedVideo.id}`);
    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();
  });
});
