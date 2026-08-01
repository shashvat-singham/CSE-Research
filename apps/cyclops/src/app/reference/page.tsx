import type { Metadata } from "next";
import Link from "next/link";

import { RULE_DESCRIPTIONS } from "@/lib/ll1";

export const metadata: Metadata = {
  title: "Learn",
  description:
    "The rules behind FIRST sets, FOLLOW sets and the LL(1) parse table, and " +
    "what makes a grammar fail to be LL(1).",
};

const SECTIONS = [
  {
    id: "first",
    heading: "FIRST sets",
    lead:
      "FIRST(X) is the set of terminals that can begin a string derived from X. " +
      "If X can derive the empty string, ε is in FIRST(X) too.",
    rules: ["First_1", "First_2", "First_3"] as const,
    note:
      "Rule 2 is the one people get wrong: you take FIRST of the next symbol " +
      "minus ε, and you only move on to the symbol after it if the current one " +
      "is nullable.",
  },
  {
    id: "follow",
    heading: "FOLLOW sets",
    lead:
      "FOLLOW(A) is the set of terminals that can appear immediately after A in " +
      "some derivation. It is about the grammar as a whole, not about A's own " +
      "productions.",
    rules: ["Follow_1", "Follow_2", "Follow_3"] as const,
    note:
      "Rule 3 catches the case people miss: if A is at the end of a production, " +
      "or everything after it can vanish, then whatever follows the head also " +
      "follows A.",
  },
  {
    id: "table",
    heading: "The parse table",
    lead:
      "The table says which production to apply given a non-terminal on the " +
      "stack and one terminal of lookahead.",
    rules: ["PT_1", "PT_2"] as const,
    note:
      "A cell with two productions means one token of lookahead is not enough " +
      "to choose, and the grammar is not LL(1).",
  },
];

export default function LearnPage() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">The method</h1>
        <p className="mt-2 max-w-2xl text-ink-secondary">
          Eight rules produce an LL(1) parser. Cyclops tags every set member and
          table entry with the rule that put it there, so the feedback can point
          at the specific step you missed.
        </p>
      </header>

      {SECTIONS.map((section) => (
        <section key={section.id} className="card p-6" aria-labelledby={`${section.id}-heading`}>
          <h2 id={`${section.id}-heading`} className="text-lg font-semibold">
            {section.heading}
          </h2>
          <p className="mt-2 text-ink-secondary">{section.lead}</p>

          <ol className="mt-4 space-y-3">
            {section.rules.map((rule) => {
              const [name, description] = RULE_DESCRIPTIONS[rule].split(" — ");
              return (
                <li key={rule} className="border-l-2 border-accent pl-4">
                  <p className="font-medium">{name}</p>
                  <p className="text-sm text-ink-secondary">{description}</p>
                </li>
              );
            })}
          </ol>

          <p className="mt-4 rounded-md bg-accent-soft p-3 text-sm text-accent-ink">
            {section.note}
          </p>
        </section>
      ))}

      <section className="card p-6" aria-labelledby="conflicts-heading">
        <h2 id="conflicts-heading" className="text-lg font-semibold">
          Why a grammar fails to be LL(1)
        </h2>
        <dl className="mt-4 space-y-4">
          <div>
            <dt className="font-medium">Left recursion</dt>
            <dd className="text-sm text-ink-secondary">
              <code>E → E + T</code> means the parser would expand E to E forever
              without consuming a token. No left-recursive grammar is LL(1);
              rewrite it as <code>E → T E&apos;</code> with{" "}
              <code>E&apos; → + T E&apos; | ε</code> first.
            </dd>
          </div>
          <div>
            <dt className="font-medium">A FIRST/FIRST clash</dt>
            <dd className="text-sm text-ink-secondary">
              Two alternatives begin with the same terminal, as in{" "}
              <code>S → a b | a c</code>. Left-factor them into{" "}
              <code>S → a S&apos;</code> with <code>S&apos; → b | c</code>.
            </dd>
          </div>
          <div>
            <dt className="font-medium">A FIRST/FOLLOW clash</dt>
            <dd className="text-sm text-ink-secondary">
              A nullable non-terminal can start with the same terminal that can
              follow it, so the parser cannot tell whether to expand it or skip
              past it. The dangling-else grammar is the standard example.
            </dd>
          </div>
        </dl>
        <p className="mt-5 text-sm">
          <Link href="/workbench" className="text-accent underline underline-offset-2">
            Try each of these in the workbench
          </Link>{" "}
          — the example picker has a left-recursive grammar and a dangling-else
          grammar ready to load.
        </p>
      </section>
    </div>
  );
}
