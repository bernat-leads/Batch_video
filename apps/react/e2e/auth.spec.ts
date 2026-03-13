import { test, expect, type Page } from "@playwright/test";

/**
 * Mock the /auth/me endpoint to simulate an authenticated session.
 */
async function mockAuthenticated(page: Page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 200, json: { authenticated: true } }),
  );
}

/**
 * Mock the /auth/me endpoint to simulate an unauthenticated session.
 */
async function mockUnauthenticated(page: Page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
}

/**
 * Mock dashboard API calls for authenticated pages.
 */
async function mockDashboardApis(page: Page) {
  await page.route("**/api/v1/videos/batches", (route) =>
    route.fulfill({ status: 200, json: [] }),
  );
  await page.route("**/api/v1/settings*", (route) =>
    route.fulfill({
      status: 200,
      json: { master_prompt: "", retention_days: 7 },
    }),
  );
}

test.describe("unauthenticated", () => {
  test.beforeEach(async ({ page }) => {
    await mockUnauthenticated(page);
  });

  test("redirects to /login when visiting /", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(
      page.getByRole("heading", { name: "Sign In" }),
    ).toBeVisible();
  });

  test("redirects to /login when visiting /app", async ({ page }) => {
    await page.goto("/app");
    await expect(page).toHaveURL(/\/login/);
  });

  test("redirects to /login when visiting /app/settings", async ({ page }) => {
    await page.goto("/app/settings");
    await expect(page).toHaveURL(/\/login/);
  });

  test("login page is accessible directly", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByRole("heading", { name: "Sign In" }),
    ).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Sign In" }),
    ).toBeVisible();
  });
});

test.describe("login flow", () => {
  test("successful login redirects to /app", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");

    // Mock login success — must be set before clicking
    await page.route("**/api/v1/auth/login", (route) =>
      route.fulfill({ status: 200, json: { authenticated: true } }),
    );

    // After login, /me should return authenticated — unroute first to replace mock
    await page.unroute("**/api/v1/auth/me");
    await mockAuthenticated(page);
    await mockDashboardApis(page);

    await page.getByLabel("Password").fill("correct-password");
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page).toHaveURL("/app");
    await expect(
      page.getByRole("heading", { name: "Videos" }),
    ).toBeVisible();
  });

  test("failed login shows error message", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");

    // Mock login failure
    await page.route("**/api/v1/auth/login", (route) =>
      route.fulfill({ status: 401, json: { detail: "Invalid password" } }),
    );

    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page.getByText("Invalid password")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("shows loading state while logging in", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");

    // Delay the login response so we can observe the pending state
    await page.route("**/api/v1/auth/login", async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      await route.fulfill({ status: 200, json: { authenticated: true } });
    });
    await page.unroute("**/api/v1/auth/me");
    await mockAuthenticated(page);

    await page.getByLabel("Password").fill("test");
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(
      page.getByRole("button", { name: "Signing in..." }),
    ).toBeVisible();
  });
});

test.describe("expired session", () => {
  test("redirects to login when session expires on navigation", async ({
    page,
  }) => {
    await mockAuthenticated(page);
    await mockDashboardApis(page);
    await page.goto("/app");
    await expect(
      page.getByRole("heading", { name: "Videos" }),
    ).toBeVisible();

    // Session expires — /me now returns 401
    await page.unroute("**/api/v1/auth/me");
    await mockUnauthenticated(page);

    // Navigate to trigger beforeLoad auth check
    await page.getByRole("link", { name: "Settings" }).click();

    await expect(page).toHaveURL(/\/login/);
  });

  test("redirects to login when API call returns 401 mid-session", async ({
    page,
  }) => {
    await mockAuthenticated(page);
    await mockDashboardApis(page);

    await page.goto("/app");
    await expect(
      page.getByRole("heading", { name: "Videos" }),
    ).toBeVisible();

    // Session expires — any API call now returns 401
    await page.unroute("**/api/v1/auth/me");
    await page.unroute("**/api/v1/videos/batches");
    await page.route("**/api/v1/videos/batches", (route) =>
      route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
    );
    await mockUnauthenticated(page);

    // Trigger an API call by navigating (beforeLoad calls /me which is now 401)
    await page.getByRole("link", { name: "Settings" }).click();

    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe("authenticated", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticated(page);
    await mockDashboardApis(page);
  });

  test("root redirects to /app when authenticated", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL("/app");
    await expect(
      page.getByRole("heading", { name: "Videos" }),
    ).toBeVisible();
  });

  test("home page loads when authenticated", async ({ page }) => {
    await page.goto("/app");
    await expect(
      page.getByRole("heading", { name: "Videos" }),
    ).toBeVisible();
  });

  test("navigation works when authenticated", async ({ page }) => {
    await page.goto("/app");
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(
      page.getByRole("heading", { name: "Settings" }),
    ).toBeVisible();
  });

  test("sign out button is visible", async ({ page }) => {
    await page.goto("/app");
    await expect(
      page.getByRole("button", { name: "Sign out" }),
    ).toBeVisible();
  });

  test("sign out redirects to login", async ({ page }) => {
    await page.goto("/app");

    // Mock logout success
    await page.route("**/api/v1/auth/logout", (route) =>
      route.fulfill({ status: 200, json: { authenticated: false } }),
    );

    // After logout, /me should return 401
    await page.unroute("**/api/v1/auth/me");
    await mockUnauthenticated(page);

    await page.getByRole("button", { name: "Sign out" }).click();

    await expect(page).toHaveURL(/\/login/);
    await expect(
      page.getByRole("heading", { name: "Sign In" }),
    ).toBeVisible();
  });
});
