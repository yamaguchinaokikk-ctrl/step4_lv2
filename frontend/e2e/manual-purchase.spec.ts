import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

/**
 * カメラ（バーコードスキャン）は本テスト環境で利用できないため、E2E-PURCHASE系のシナリオは
 * 商品登録の起点を手入力（E2E-MANUAL、FR-005）に置き換えて検証する。
 * 商品マスタ照合以降の処理はスキャン・手入力で共通（3.2.1節）のため、業務ロジックの検証としては同等。
 */

test.beforeEach(async ({ page }) => {
  await loginAs(page, "stf1", "Passw0rd");
});

test("E2E-MANUAL-001/002: 手入力の2段階フロー（Enterで一時表示→追加ボタンでリスト反映）", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill("4901301234567");
  await codeInput.press("Enter");

  await expect(page.getByText(/名称：標準税率の通常商品/)).toBeVisible();
  await expect(page.getByText("単価：¥1,000")).toBeVisible();

  // まだ購入リストには反映されていない
  await expect(page.getByText("購入リストは空です")).toBeVisible();

  await page.getByRole("button", { name: "追加" }).click();
  await expect(page.getByText("購入リストは空です")).not.toBeVisible();
  await expect(page.getByText("1件追加されました")).toBeVisible();
});

test("E2E-MANUAL-004 / E2E-PURCHASE-004相当: 未登録商品コードの手入力はエラー表示され追加されない", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill("4909999999999");
  await codeInput.press("Enter");

  await expect(page.getByText("商品がマスタ未登録です")).toBeVisible();
  await expect(page.getByText("購入リストは空です")).toBeVisible();
});

test("E2E-PURCHASE-002相当: 同一商品の連続登録で数量が加算される", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");

  for (let i = 0; i < 2; i++) {
    await codeInput.fill("4901301234567");
    await codeInput.press("Enter");
    await page.getByRole("button", { name: "追加" }).click();
  }

  const row = page.locator("tr", { hasText: "標準税率の通常商品" });
  await expect(row).toHaveCount(1); // 新規行が作られず1行のまま
  await expect(row.getByText("2", { exact: true })).toBeVisible();
});

test("E2E-PURCHASE-003相当: 複数商品の購入で合計金額が正しく計算される", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");

  for (const code of ["4901301234567", "49012345"]) {
    await codeInput.fill(code);
    await codeInput.press("Enter");
    await page.getByRole("button", { name: "追加" }).click();
  }

  // 1000円 + 500円 = 1500円（値引きなし前提）
  await expect(page.getByText("小計（税抜・値引後）：¥1,500")).toBeVisible();
});

test("E2E-PURCHASE-001: 購入確定でポップアップに税込・税抜合計が表示され、確定後に画面がクリアされる", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill("4901301234567");
  await codeInput.press("Enter");
  await page.getByRole("button", { name: "追加" }).click();

  await page.getByRole("button", { name: "購入確定" }).click();

  await expect(page.getByText("合計（税込）：¥1,100")).toBeVisible();
  await expect(page.getByText("合計（税抜）：¥1,000")).toBeVisible();

  await page.getByRole("button", { name: "次の取引へ" }).click();

  // ISS-025：確定後は購入リスト・会員ID・コード入力欄を全てクリアする
  await expect(page.getByText("購入リストは空です")).toBeVisible();
  await expect(codeInput).toHaveValue("");
});

test("E2E-PURCHASE-006: 購入リスト0件では購入確定ボタンが無効化されている", async ({ page }) => {
  await expect(page.getByRole("button", { name: "購入確定" })).toBeDisabled();
});

test("E2E-CARTOPS-001/002/003: 選択・数量変更・削除で小計が再計算される", async ({ page }) => {
  const codeInput = page.getByPlaceholder("商品コードを入力してEnter");
  await codeInput.fill("4901301234567");
  await codeInput.press("Enter");
  await page.getByRole("button", { name: "追加" }).click();

  const row = page.locator("tr", { hasText: "標準税率の通常商品" });
  await row.click(); // E2E-CARTOPS-001: 選択
  await expect(row).toHaveClass(/selected-row/);

  await row.getByRole("button", { name: "+" }).click(); // E2E-CARTOPS-002: 数量変更 1->2
  await expect(page.getByText("小計（税抜・値引後）：¥2,000")).toBeVisible();

  await page.getByRole("button", { name: "選択商品を削除" }).click(); // E2E-CARTOPS-003
  await expect(page.getByText("購入リストは空です")).toBeVisible();
  await expect(page.getByText("小計（税抜・値引後）：¥0")).toBeVisible();
});
