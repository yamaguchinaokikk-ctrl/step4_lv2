import { proxyToBackend } from "@/lib/backendProxy";

/** 6.4.4節：商品マスタ照合。 */
export async function GET(_request: Request, { params }: { params: { productCode: string } }) {
  return proxyToBackend(`/api/products/${encodeURIComponent(params.productCode)}`, { method: "GET" });
}
