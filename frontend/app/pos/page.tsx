import { redirect } from "next/navigation";

import PosMain from "@/components/pos/PosMain";
import { getServerSession } from "@/lib/serverSession";

/** SC-02 POSメイン画面（設計仕様書4.2.2節）。 */
export default async function PosPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");

  return <PosMain staffId={session.staff_id} staffName={session.staff_name} />;
}
