import { test, expect } from "@playwright/test";

test("customer page loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Ask FixIt AI")).toBeVisible();
});
