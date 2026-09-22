import { expect, test } from "@playwright/test";

test("E2E-LOGIN-001: 正常ログインでPOSメイン画面に遷移し担当者情報が表示される", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("担当者ID").fill("stf1");
  await page.getByLabel("パスワード").fill("Passw0rd");
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/pos$/);
  await expect(page.getByText("山田一般")).toBeVisible();
});

test("E2E-LOGIN-002: 認証失敗時はログイン画面に留まりエラーが表示される", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("担当者ID").fill("stf1");
  await page.getByLabel("パスワード").fill("WrongPass1");
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText("担当者IDまたはパスワードが正しくありません")).toBeVisible();
});

test("E2E-LOGIN-005: ログアウトでログイン画面に戻る", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("担当者ID").fill("stf1");
  await page.getByLabel("パスワード").fill("Passw0rd");
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/pos$/);

  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("未ログインでPOS画面に直接アクセスするとログイン画面へリダイレクトされる", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/pos");
  await expect(page).toHaveURL(/\/login$/);
});
