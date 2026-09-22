import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.5節：会員照会。 */
export async function GET(_request: Request, { params }: { params: { memberId: string } }) {
  return proxyToBackend(`/api/members/${encodeURIComponent(params.memberId)}`, { method: "GET" });
}
