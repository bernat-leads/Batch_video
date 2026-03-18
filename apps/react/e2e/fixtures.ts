/**
 * Shared Playwright fixtures — auth, API mocking, and test data factories.
 *
 * Design principles (from community best practices):
 * - Data isolation: each test gets unique IDs, no shared state between tests
 * - route.fulfill() for all API calls: tests run without a real backend
 * - Push specifics down: only mock what the test actually needs
 * - Accessibility-first selectors: getByRole, getByLabel, getByText
 */

import { test as base, type Page } from "@playwright/test";
import { mockFactories, type MockData } from "./mock-data";

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

async function mockAuthenticated(page: Page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 200, json: { authenticated: true } }),
  );
}

async function mockUnauthenticated(page: Page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
}

// ---------------------------------------------------------------------------
// API mock helpers
// ---------------------------------------------------------------------------

const EMPTY_PAGE = { items: [], page: 1, page_size: 50, total: 0, total_pages: 0 };

function pageResponse<T>(items: T[]) {
  return { items, page: 1, page_size: 50, total: items.length, total_pages: items.length > 0 ? 1 : 0 };
}

async function mockAllApis(page: Page, data?: MockData) {
  const batches = data?.batches ?? [];
  const videos = data?.videos ?? [];
  const dashboard = data?.dashboardResponse ?? mockFactories.dashboardResponse();
  const settings = mockFactories.settings();

  // Dashboard stats
  await page.route("**/api/v1/dashboard/**", (route) =>
    route.fulfill({ status: 200, json: dashboard }),
  );

  // Settings
  await page.route("**/api/v1/settings/**", (route) =>
    route.fulfill({ status: 200, json: settings }),
  );
  await page.route("**/api/v1/settings", (route) =>
    route.fulfill({ status: 200, json: settings }),
  );

  // Batches — single route handler for all batch URLs
  await page.route(/\/api\/v1\/batches/, (route) => {
    const url = route.request().url();
    const detailMatch = url.match(/batches\/([0-9a-f-]{36})/);
    if (detailMatch) {
      const batch = batches.find((b) => b.id === detailMatch[1]);
      return route.fulfill({
        status: batch ? 200 : 404,
        json: batch ?? { message: "Not found" },
      });
    }
    return route.fulfill({ status: 200, json: pageResponse(batches) });
  });

  // Videos — single route handler for all video URLs
  await page.route(/\/api\/v1\/videos/, (route) => {
    const url = route.request().url();
    const detailMatch = url.match(/videos\/([0-9a-f-]{36})/);
    if (detailMatch) {
      const video = videos.find((v) => v.id === detailMatch[1]);
      return route.fulfill({
        status: video ? 200 : 404,
        json: video ? { ...video, shots: [] } : { message: "Not found" },
      });
    }
    return route.fulfill({ status: 200, json: pageResponse(videos) });
  });
}

// ---------------------------------------------------------------------------
// Custom test fixture
// ---------------------------------------------------------------------------

type Fixtures = {
  authedPage: Page;
  authedPageWithData: { page: Page; data: MockData };
  mocks: typeof mockFactories;
};

export const test = base.extend<Fixtures>({
  authedPage: async ({ page }, use) => {
    await mockAuthenticated(page);
    await mockAllApis(page);
    await use(page);
  },

  authedPageWithData: async ({ page }, use) => {
    await mockAuthenticated(page);
    const data = mockFactories.fullDataset();
    await mockAllApis(page, data);
    await use({ page, data });
  },

  mocks: async ({}, use) => {
    await use(mockFactories);
  },
});

export { expect } from "@playwright/test";
export { mockAuthenticated, mockUnauthenticated, mockAllApis };

/** Shorthand for tests that need to set up their own empty dashboard */
export async function mockEmptyDashboard(page: Page) {
  await mockAllApis(page);
}
