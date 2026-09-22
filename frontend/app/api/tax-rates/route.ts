import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.15/6.4.16節：消費税率一覧・新規登録（4章SC-04、管理者ロール限定）。 */
export async function GET() {
  return proxyToBackend("/api/tax-rates", { method: "GET" });
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  return proxyToBackend("/api/tax-rates", { method: "POST", body });
}
