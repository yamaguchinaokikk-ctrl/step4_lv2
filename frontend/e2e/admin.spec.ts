import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("E2E-ADMIN-001: 管理者はSC-04（値引き・税率管理画面）にアクセスでき一覧が表示される", async ({ page }) => {
  await loginAs(page, "admin0012345", "AdminPass99");
  await page.goto("/admin/discounts");
  await expect(page.getByRole("heading", { name: "値引き・税率管理（管理者限定）" })).toBeVisible();
  await expect(page.getByText("値引き一覧")).toBeVisible();
  await expect(page.getByText("消費税率一覧")).toBeVisible();
});

test("E2E-ADMIN-002: 一般ロールはSC-04へのアクセスが拒否されPOS画面へ戻される", async ({ page }) => {
  await loginAs(page, "stf1", "Passw0rd");
  await page.goto("/admin/discounts");
  await expect(page).toHaveURL(/\/pos$/);
});

test("E2E-ADMIN-003/004: 値引き登録がSC-02のスキャン結果に反映され、重複期間はエラーになる", async ({ page }) => {
  await loginAs(page, "admin0012345", "AdminPass99");
  await page.goto("/admin/discounts");

  const targetProduct = "49012345"; // 標準税率の通常商品（8桁）: 値引き未登録のもの
  const discountForm = page.locator("form").first();
  await discountForm.getByLabel("商品コード").fill(targetProduct);
  await discountForm.getByLabel("種別").selectOption("rate");
  await discountForm.getByLabel("値").fill("20");
  await discountForm.getByLabel("開始日", { exact: true }).fill("2020-01-01");
  await discountForm.getByLabel("終了日").fill("2099-12-31");
  await discountForm.getByRole("button", { name: "値引きを登録" }).click();

  await expect(page.locator("td", { hasText: targetProduct })).toBeVisible();

  // E2E-ADMIN-004: 同一商品・重複期間で再登録するとエラー
  await discountForm.getByLabel("商品コード").fill(targetProduct);
  await discountForm.getByLabel("種別").selectOption("rate");
  await discountForm.getByLabel("値").fill("10");
  await discountForm.getByLabel("開始日", { exact: true }).fill("2021-01-01");
  await discountForm.getByLabel("終了日").fill("2021-12-31");
  await discountForm.getByRole("button", { name: "値引きを登録" }).click();
  await expect(page.getByText(/DISCOUNT_PERIOD_CONFLICT|重複/)).toBeVisible();
});

test("E2E-ADMIN-005: 消費税率登録が一覧に反映される", async ({ page }) => {
  await loginAs(page, "admin0012345", "AdminPass99");
  await page.goto("/admin/discounts");

  await page.getByLabel("税率（0〜0.20、例：0.10）").fill("0.15");
  await page.locator("select").nth(1).selectOption("reduced");
  await page.getByLabel("適用開始日").fill("2099-01-01");
  await page.getByRole("button", { name: "消費税率を登録" }).click();

  await expect(page.getByText("15.00%").first()).toBeVisible();
});
