import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.7節：購入確定。 */
export async function POST(request: NextRequest) {
  const body = await request.text();
  return proxyToBackend("/api/transactions", { method: "POST", body });
}
