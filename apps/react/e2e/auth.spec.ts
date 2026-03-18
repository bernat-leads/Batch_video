import { test, expect, mockAuthenticated, mockUnauthenticated, mockEmptyDashboard } from "./fixtures";

test.describe("unauthenticated — redirects to login", () => {
  const protectedRoutes = ["/", "/app", "/app/settings", "/app/videos", "/app/batches"];

  for (const route of protectedRoutes) {
    test(`${route} redirects to /login`, async ({ page }) => {
      await mockUnauthenticated(page);
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/);
    });
  }

  test("login page is accessible directly", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
    await expect(page.getByPlaceholder("Enter team password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });
});

test.describe("login flow", () => {
  test("successful login redirects to /app", async ({ page }) => {
    // Start unauthenticated — track state so /me handler can switch
    let authenticated = false;

    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: authenticated ? 200 : 401,
        json: authenticated ? { authenticated: true } : { detail: "Not authenticated" },
      }),
    );

    await page.goto("/login");
    await expect(page.getByPlaceholder("Enter team password")).toBeVisible();

    // Mock login success — flip auth state when login succeeds
    await page.route("**/api/v1/auth/login", async (route) => {
      authenticated = true;
      await route.fulfill({ status: 200, json: { authenticated: true } });
    });
    await mockEmptyDashboard(page);

    await page.getByPlaceholder("Enter team password").fill("correct-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL("/app");
  });

  test("failed login shows error message", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");

    await page.route("**/api/v1/auth/login", (route) =>
      route.fulfill({ status: 401, json: { detail: "Invalid password" } }),
    );

    await page.getByPlaceholder("Enter team password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("Invalid password")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("shows loading state while logging in", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");

    await page.route("**/api/v1/auth/login", async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      await route.fulfill({ status: 200, json: { authenticated: true } });
    });

    await page.getByPlaceholder("Enter team password").fill("test");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByRole("button", { name: "Signing in..." })).toBeVisible();
  });
});

test.describe("session management", () => {
  test("expired session redirects to login on navigation", async ({ page }) => {
    let authenticated = true;

    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: authenticated ? 200 : 401,
        json: authenticated ? { authenticated: true } : { detail: "Not authenticated" },
      }),
    );
    await mockEmptyDashboard(page);

    await page.goto("/app");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // Session expires
    authenticated = false;

    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  test("leave button is visible in sidebar", async ({ page }) => {
    let authenticated = true;

    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: authenticated ? 200 : 401,
        json: authenticated ? { authenticated: true } : { detail: "Not authenticated" },
      }),
    );
    await mockEmptyDashboard(page);

    await page.goto("/app");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Leave" })).toBeAttached();
  });
});
