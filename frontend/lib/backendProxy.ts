import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, BACKEND_API_BASE_URL, REFRESH_COOKIE } from "./constants";

/**
 * BFF（Next.js API Routes）からFastAPIへのプロキシ共通処理。
 * 設計仕様書7.4.1/7.4.2(1)節：ブラウザはFastAPIへ直接通信せず、必ずBFFを経由する。
 * アクセストークンはCookie（httpOnly）から取り出し、Authorizationヘッダーへ詰め替える。
 * アクセストークン期限切れ（401）時は、リフレッシュトークンで自動的に再試行する。
 */

const cookieOptions = (maxAgeSeconds: number) => ({
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "strict" as const,
  path: "/",
  maxAge: maxAgeSeconds,
});

export function setAuthCookies(
  res: NextResponse,
  accessToken: string,
  expiresIn: number,
  refreshToken?: string,
) {
  res.cookies.set(ACCESS_COOKIE, accessToken, cookieOptions(expiresIn));
  if (refreshToken) {
    // リフレッシュトークン有効期限8時間（設計仕様書6.2節）
    res.cookies.set(REFRESH_COOKIE, refreshToken, cookieOptions(60 * 60 * 8));
  }
}

export function clearAuthCookies(res: NextResponse) {
  res.cookies.delete(ACCESS_COOKIE);
  res.cookies.delete(REFRESH_COOKIE);
}

async function refreshAccessToken(
  refreshToken: string,
): Promise<{ accessToken: string; expiresIn: number } | null> {
  const r = await fetch(`${BACKEND_API_BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  if (!r.ok) return null;
  const data = await r.json();
  return { accessToken: data.access_token, expiresIn: data.expires_in };
}

export async function proxyToBackend(
  path: string,
  init: RequestInit = {},
  options: { requireAuth?: boolean } = {},
): Promise<NextResponse> {
  const requireAuth = options.requireAuth !== false;
  const cookieStore = cookies();
  const accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  const doFetch = (token?: string) => {
    const headers = new Headers(init.headers);
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(`${BACKEND_API_BASE_URL}${path}`, { ...init, headers, cache: "no-store" });
  };

  let backendRes = await doFetch(accessToken);
  let refreshed: { accessToken: string; expiresIn: number } | null = null;

  if (backendRes.status === 401 && requireAuth && refreshToken) {
    refreshed = await refreshAccessToken(refreshToken);
    if (refreshed) {
      backendRes = await doFetch(refreshed.accessToken);
    }
  }

  const contentType = backendRes.headers.get("Content-Type") || "application/json";
  const bodyText = backendRes.status === 204 ? null : await backendRes.text();

  const res = new NextResponse(bodyText, {
    status: backendRes.status,
    headers: { "Content-Type": contentType },
  });

  if (refreshed) {
    res.cookies.set(ACCESS_COOKIE, refreshed.accessToken, cookieOptions(refreshed.expiresIn));
  }

  return res;
}
