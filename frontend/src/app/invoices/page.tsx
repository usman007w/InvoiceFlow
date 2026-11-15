"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Me = { id: number; email: string; role: string; company_id: number };

export default function InvoicesPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    fetch("/api/auth/me").then(async (res) => {
      if (res.status === 401) router.replace("/login");
      else if (res.ok) setMe(await res.json());
    });
  }, [router]);

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  if (!me) return <main className="p-8">Loading...</main>;

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Invoices</h1>
        <button onClick={logout} className="rounded border border-gray-400 px-3 py-1 text-sm">
          Log out
        </button>
      </div>
      <p className="mt-4 text-sm opacity-70">
        Logged in as {me.email} ({me.role})
      </p>
    </main>
  );
}