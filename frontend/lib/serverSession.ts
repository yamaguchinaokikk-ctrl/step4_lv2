import { cookies } from "next/headers";

import { ACCESS_COOKIE, BACKEND_API_BASE_URL } from "./constants";

export type ServerSession = { staff_id: string; staff_name: string | null };

/**
 * アクセストークンのroleクレームを画面表示制御用に読み取る（4.2.4節：一般ロールはSC-04非表示）。
 * 署名検証は行わない（UI出し分け専用の参考情報であり、実際のアクセス制御はFastAPI側の403判定が担う、7.4.1節の多層防御）。
 */
export function getAccessTokenRole(): string | null {
  const token = cookies().get(ACCESS_COOKIE)?.value;
  if (!token) return null;
  try {
    const payloadSegment = token.split(".")[1];
    const json = Buffer.from(payloadSegment, "base64").toString("utf-8");
    const payload = JSON.parse(json);
    return payload.role ?? null;
  } catch {
    return null;
  }
}

/** サーバーコンポーネントからログイン状態を確認する（GET /api/session、SCR-011）。 */
export async function getServerSession(): Promise<ServerSession | null> {
  const accessToken = cookies().get(ACCESS_COOKIE)?.value;
  if (!accessToken) return null;

  const r = await fetch(`${BACKEND_API_BASE_URL}/api/session`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!r.ok) return null;
  return r.json();
}
