import type { Metadata, Viewport } from "next";

import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Cyclops — LL(1) parser workbench",
    template: "%s — Cyclops",
  },
  description:
    "Build FIRST and FOLLOW sets, construct an LL(1) parse table, and get " +
    "rule-level feedback on where your answer went wrong.",
  applicationName: "Cyclops",
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fcfcfb" },
    { media: "(prefers-color-scheme: dark)", color: "#1a1a19" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4
                     focus:z-50 focus:rounded-md focus:bg-accent focus:px-4 focus:py-2
                     focus:text-white"
        >
          Skip to content
        </a>
        <SiteHeader />
        <main id="main" className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
        <footer className="mt-16 border-t border-line">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 text-sm text-ink-muted sm:px-6 lg:px-8">
            Cyclops — from the compilers and program-analysis group at IIT Kanpur.
          </div>
        </footer>
      </body>
    </html>
  );
}
