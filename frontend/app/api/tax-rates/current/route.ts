import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.6節：現行消費税率の取得。 */
export async function GET(request: NextRequest) {
  return proxyToBackend(`/api/tax-rates/current${request.nextUrl.search}`, { method: "GET" });
}
