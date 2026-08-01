import type { Metadata } from "next";

import { Workbench } from "@/components/Workbench";

export const metadata: Metadata = {
  title: "Workbench",
  description:
    "Analyse a grammar, build its LL(1) parse table, and check your answer " +
    "cell by cell.",
};

export default function WorkbenchPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Workbench</h1>
        <p className="mt-2 max-w-2xl text-ink-secondary">
          Enter a grammar and press <strong>Analyse</strong>. Switch the parse
          table to <strong>Fill it in</strong> to test yourself.
        </p>
      </header>
      <Workbench />
    </div>
  );
}
