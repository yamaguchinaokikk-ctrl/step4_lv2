import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.11/6.4.12節：値引き一覧・新規登録（4章SC-04、管理者ロール限定）。 */
export async function GET() {
  return proxyToBackend("/api/discounts", { method: "GET" });
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  return proxyToBackend("/api/discounts", { method: "POST", body });
}
