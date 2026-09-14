import { test, expect } from "@playwright/test";
test.beforeEach(async ({ request }) => {
  const health = await (await request.get("/api/v1/health")).json();
  test.skip(!health.demo_mode, "Fictional-fixture suite requires DEMO_MODE=true. Live news has a separate suite.");
});
test("public browsing, detail, search, pagination and themes", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A clearer view of your world." }),
  ).toBeVisible();
  await expect(page.getByText("Demo edition", { exact: true })).toBeVisible();
  await expect(page.locator(".lead-story")).toBeVisible();
  await expect(page.locator(".lead-story img")).toBeVisible();
  await page
    .locator(".lead-story img")
    .evaluate((img: HTMLImageElement) => img.decode());
  await page.screenshot({
    path: `../test-results/${testInfo.project.name}-light.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: /Theme: system/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator(".lead-story")).toBeVisible();
  await page.screenshot({
    path: `../test-results/${testInfo.project.name}-dark.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: /Theme: dark/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("link", { name: "Read the story", exact: true }).click();
  await expect(page).toHaveURL(/\/article\//);
  await expect(
    page.getByRole("link", { name: /Back to Tamilnadu/ }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "There is no original report for this fictional demo story.",
    ),
  ).toBeVisible();
  await page.goto("/category/software-ai");
  await expect(
    page.getByRole("heading", { name: "Software & AI", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".article-card")).toHaveCount(3);
  await page.goto("/search?q=cricket");
  await expect(
    page.getByRole("heading", { name: /1 stories found/ }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Region", exact: true })
    .selectOption("Regional");
  await expect(
    page.getByRole("heading", { name: "No stories in this view yet." }),
  ).toBeVisible();
  await page.goto("/search");
  await expect(
    page.getByRole("heading", { name: "16 stories found" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Page 2 of 2")).toBeVisible();
  expect(page.url()).toContain("page=2");
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Accounts are not configured yet." }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("provider failure stays a failure", async ({ page }) => {
  await page.route("**/api/v1/articles?**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Provider unavailable" }),
    }),
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "We couldn't load this edition." }),
  ).toBeVisible();
  await expect(page.locator(".lead-story")).toHaveCount(0);
});
