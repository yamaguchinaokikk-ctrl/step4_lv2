import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.9節：ログイン中の担当者情報取得（SCR-011）。 */
export async function GET() {
  return proxyToBackend("/api/session", { method: "GET" });
}
