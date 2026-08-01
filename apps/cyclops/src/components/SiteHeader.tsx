"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/reference", label: "Reference" },
  { href: "/workbench", label: "Workbench" },
  { href: "/team", label: "Team" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const linkClass = (href: string) => {
    const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
    return [
      "rounded-md px-3 py-2 text-sm font-medium transition-colors",
      active ? "bg-accent-soft text-accent-ink" : "text-ink-secondary hover:text-ink",
    ].join(" ");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-ink">
          <span aria-hidden className="text-lg">◉</span>
          Cyclops
        </Link>

        <nav className="hidden items-center gap-1 sm:flex" aria-label="Main">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className={linkClass(item.href)}>
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          type="button"
          className="btn-secondary px-3 py-1.5 sm:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? "Close" : "Menu"}
        </button>
      </div>

      {open && (
        <nav
          id="mobile-nav"
          aria-label="Main"
          className="border-t border-line px-4 pb-3 sm:hidden"
        >
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block ${linkClass(item.href)}`}
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
