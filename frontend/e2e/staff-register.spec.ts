import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

/**
 * SC-03（担当者登録、[AI提案]）の付加確認。テスト仕様書に正式なTest ID割当はない。
 * Phase5コードレビュー修正：STAFFが1件以上存在する状態での登録は管理者ロールが必須になったため、
 * 事前に管理者としてログインしてからアクセスする（未ログイン時は初回導入のブートストラップ用途のみ許可）。
 */
test("SC-03: 管理者ログイン後に担当者を新規登録できる", async ({ page }) => {
  await loginAs(page, "admin0012345", "AdminPass99");

  const staffId = `e2e${Date.now().toString().slice(-8)}`;
  await page.goto("/staff/register");
  await page.getByLabel(/担当者ID/).fill(staffId);
  await page.getByLabel(/パスワード/).fill("E2ePass12");
  await page.getByLabel("氏名").fill("E2Eテスト担当者");
  await page.getByRole("button", { name: "登録" }).click();

  await expect(page.getByText(`担当者「E2Eテスト担当者」（${staffId}）を登録しました`)).toBeVisible();
});

test("SC-03: 未ログインでの担当者登録はエラーになる（Phase5修正のアクセス制御確認）", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/staff/register");
  await page.getByLabel(/担当者ID/).fill(`e2eng${Date.now().toString().slice(-6)}`);
  await page.getByLabel(/パスワード/).fill("E2ePass12");
  await page.getByLabel("氏名").fill("拒否確認用");
  await page.getByRole("button", { name: "登録" }).click();

  await expect(page.getByText("認証が必要です")).toBeVisible();
});
