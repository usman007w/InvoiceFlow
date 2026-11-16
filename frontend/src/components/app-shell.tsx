"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

type Me = { id: number; email: string; role: string; company_id: number };

const NAV = [
  { href: "/invoices", label: "Invoices" },
  { href: "/upload", label: "Upload" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
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

  if (!me) {
    return <main className="p-8 text-sm text-muted-foreground">Loading...</main>;
  }

  return (
    <div className="px-4 pb-10">
      <header className="sticky top-3 z-20 mx-auto mt-3 flex max-w-5xl items-center justify-between gap-4 rounded-md border-b-2 border-primary bg-background/70 px-5 py-3 shadow-lg backdrop-blur-md">
        <Link href="/invoices" className="text-lg font-bold tracking-tight">
          Invoice<span className="text-primary">Flow</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={
                pathname.startsWith(item.href)
                  ? "font-semibold text-primary"
                  : "text-muted-foreground transition-colors hover:text-foreground"
              }
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-1">
          <span className="mr-2 hidden text-xs text-muted-foreground sm:block">
            {me.email} · {me.role}
          </span>
          <ThemeToggle />
          <Button variant="ghost" size="icon" onClick={logout} aria-label="Log out">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl pt-8">{children}</main>
    </div>
  );
}