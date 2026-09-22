import { Page } from "@playwright/test";

export async function loginAs(page: Page, staffId: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("担当者ID").fill(staffId);
  await page.getByLabel("パスワード").fill(password);
  // 注意: page.goto("/login")直後は既にURLが/loginと一致するため、
  // waitForURL(/\/(pos|login)$/)のような「現在値も満たす」パターンは
  // クリック後の実ナビゲーションを待たずに即座に解決してしまう。
  // 遷移先を/posに固定して確実にログイン完了を待つ。
  await Promise.all([page.waitForURL("**/pos", { timeout: 10_000 }), page.getByRole("button", { name: "ログイン" }).click()]);
}
