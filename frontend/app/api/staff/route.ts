import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.10節：担当者簡易登録（SC-03）。バックエンドの実装判断により認証不要。 */
export async function POST(request: NextRequest) {
  const body = await request.text();
  return proxyToBackend("/api/staff", { method: "POST", body }, { requireAuth: false });
}
