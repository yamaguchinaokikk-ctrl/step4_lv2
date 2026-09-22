import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { setAuthCookies } from "@/lib/backendProxy";
import { BACKEND_API_BASE_URL, REFRESH_COOKIE } from "@/lib/constants";

/** 6.4.2節：アクセストークン再発行。通常はbackendProxyが自動実行するが、明示呼び出し用にも公開する。 */
export async function POST() {
  const refreshToken = cookies().get(REFRESH_COOKIE)?.value;
  if (!refreshToken) {
    return NextResponse.json(
      { error: { type: "business_error", code: "REFRESH_TOKEN_INVALID", message: "再ログインが必要です", details: null } },
      { status: 401 },
    );
  }

  const backendRes = await fetch(`${BACKEND_API_BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  const data = await backendRes.json();

  if (!backendRes.ok) {
    return NextResponse.json(data, { status: backendRes.status });
  }

  const res = NextResponse.json({ expires_in: data.expires_in });
  setAuthCookies(res, data.access_token, data.expires_in);
  return res;
}
