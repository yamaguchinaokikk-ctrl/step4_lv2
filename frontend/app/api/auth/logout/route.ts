import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { clearAuthCookies } from "@/lib/backendProxy";
import { ACCESS_COOKIE, BACKEND_API_BASE_URL, REFRESH_COOKIE } from "@/lib/constants";

/** 6.4.3節：ログアウト（ISS-010）。REFRESH_TOKENSのrevoked_atをセットして失効させる。 */
export async function POST() {
  const cookieStore = cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  if (accessToken && refreshToken) {
    await fetch(`${BACKEND_API_BASE_URL}/api/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    }).catch(() => undefined);
  }

  const res = NextResponse.json({ ok: true });
  clearAuthCookies(res);
  return res;
}
