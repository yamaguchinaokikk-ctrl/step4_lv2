import { redirect } from "next/navigation";

import AdminDiscounts from "@/components/pos/AdminDiscounts";
import { getAccessTokenRole, getServerSession } from "@/lib/serverSession";

/** SC-04 値引き・税率管理画面（設計仕様書4.2.4節）。管理者ロール（admin）限定。 */
export default async function AdminDiscountsPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");

  const role = getAccessTokenRole();
  if (role !== "admin") redirect("/pos");

  return <AdminDiscounts />;
}
