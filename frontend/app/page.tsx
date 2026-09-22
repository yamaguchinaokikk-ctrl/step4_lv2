import { redirect } from "next/navigation";

import { getServerSession } from "@/lib/serverSession";

export default async function RootPage() {
  const session = await getServerSession();
  redirect(session ? "/pos" : "/login");
}
