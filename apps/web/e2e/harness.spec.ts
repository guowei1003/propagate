import { expect, test } from "@playwright/test";

test("landing page renders shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Propagate")).toBeVisible();
  await expect(page.getByText("任务收件箱")).toBeVisible();
});
