import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

/**
 * 値引き対象商品として、Phase3のAPI動作確認時にadminが登録した実データ
 * （product_code=4904567890123, discount_type=rate, discount_value=5, 2026-09-01〜2026-12-31）を利用する。
 * このデータが存在しない環境で再実行する場合は、事前にSC-04（/admin/discounts）で同等の値引きを登録すること。
 */
const DISCOUNT_PRODUCT_CODE = "4904567890123";

test.beforeEach(async ({ page }) => {
  await loginAs(page, "stf1", "Passw0rd");
});

test("E2E-MEMBER-001: 会員ID読込後に対象商品を登録すると値引きが適用される", async ({ page }) => {
  await page.getByPlaceholder("会員ID").fill("M001");
  await page.getByRole("button", { name: "お客様ID読み込み" }).click();
  await expect(page.getByText("会員：テスト太郎")).toBeVisible();

  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill(DISCOUNT_PRODUCT_CODE);
  await codeInput.press("Enter");
  await page.getByRole("button", { name: "追加" }).click();

  const row = page.locator("tr", { hasText: "端数計算確認用商品" });
  await expect(row).not.toContainText("-¥0");
  await expect(row.getByText(/^-¥/)).toBeVisible();
});

test("E2E-MEMBER-002 (BR-002/ISS-006): 会員ID読込前に登録した商品へ値引きは遡及適用されない", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill(DISCOUNT_PRODUCT_CODE);
  await codeInput.press("Enter");
  await page.getByRole("button", { name: "追加" }).click();

  const row = page.locator("tr", { hasText: "端数計算確認用商品" });
  await expect(row.locator("td").nth(3)).toHaveText("-"); // 値引き列：まだ会員未読込のため値引きなし

  await page.getByPlaceholder("会員ID").fill("M001");
  await page.getByRole("button", { name: "お客様ID読み込み" }).click();
  await expect(page.getByText("会員：テスト太郎")).toBeVisible();

  // 会員読込後も、既にリストにある行の値引き表示は変化しない（遡及なし）
  await expect(row.locator("td").nth(3)).toHaveText("-");
});

test("E2E-MEMBER-003: 会員IDなしでも購入確定できる", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill("49012345");
  await codeInput.press("Enter");
  await page.getByRole("button", { name: "追加" }).click();

  await page.getByRole("button", { name: "購入確定" }).click();
  await expect(page.getByText("合計（税込）：")).toBeVisible();
});

test("E2E-MEMBER-004: 存在しない会員IDはエラーとして拒否される", async ({ page }) => {
  await page.getByPlaceholder("会員ID").fill("M9999");
  await page.getByRole("button", { name: "お客様ID読み込み" }).click();
  await expect(page.getByText("会員IDが見つかりません")).toBeVisible();
  await expect(page.getByText("会員：")).not.toBeVisible();
});
