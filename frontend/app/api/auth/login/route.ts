import { NextRequest, NextResponse } from "next/server";

import { setAuthCookies } from "@/lib/backendProxy";
import { BACKEND_API_BASE_URL } from "@/lib/constants";

/** 6.4.1節：ログイン。トークンはブラウザJSに渡さずhttpOnly Cookieへ格納する（7.4.1節）。 */
export async function POST(request: NextRequest) {
  const body = await request.text();

  const backendRes = await fetch(`${BACKEND_API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    cache: "no-store",
  });
  const data = await backendRes.json();

  if (!backendRes.ok) {
    return NextResponse.json(data, { status: backendRes.status });
  }

  const res = NextResponse.json({ staff_id: data.staff_id, staff_name: data.staff_name });
  setAuthCookies(res, data.access_token, data.expires_in, data.refresh_token);
  return res;
}
