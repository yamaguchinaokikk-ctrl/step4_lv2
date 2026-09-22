import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.13/6.4.14節：値引きの編集・削除（管理者ロール限定）。 */
export async function PUT(request: NextRequest, { params }: { params: { discountId: string } }) {
  const body = await request.text();
  return proxyToBackend(`/api/discounts/${encodeURIComponent(params.discountId)}`, { method: "PUT", body });
}

export async function DELETE(_request: NextRequest, { params }: { params: { discountId: string } }) {
  return proxyToBackend(`/api/discounts/${encodeURIComponent(params.discountId)}`, { method: "DELETE" });
}
