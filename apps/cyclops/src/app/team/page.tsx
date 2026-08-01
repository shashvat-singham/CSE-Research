import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Team",
  description: "The people behind Cyclops.",
};

const TEAM = [
  {
    name: "Pankaj Kalita",
    href: "https://www.cse.iitk.ac.in/users/pkalita/",
  },
  {
    name: "Sumit Lahiri",
    href: "https://www.cse.iitk.ac.in/users/sumitl/",
  },
  {
    name: "Subhajit Roy",
    href: "https://www.cse.iitk.ac.in/users/subhajit/",
  },
];

export default function TeamPage() {
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Team</h1>
        <p className="mt-2 max-w-2xl text-ink-secondary">
          Cyclops comes out of the compilers and program-analysis group in the
          Department of Computer Science and Engineering at IIT Kanpur.
        </p>
      </header>

      <ul className="grid gap-4 sm:grid-cols-3">
        {TEAM.map((person) => (
          <li key={person.name} className="card p-5">
            <p className="font-medium">{person.name}</p>
            <a
              href={person.href}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-1 inline-block text-sm text-accent underline underline-offset-2"
            >
              Homepage
            </a>
          </li>
        ))}
      </ul>

      <section className="card p-6" aria-labelledby="paper-heading">
        <h2 id="paper-heading" className="text-lg font-semibold">
          Background reading
        </h2>
        <p className="mt-2 text-sm text-ink-secondary">
          The symbolic encoding behind Cyclops is described in{" "}
          <a
            href="https://easychair.org/publications/paper/DtjZ"
            target="_blank"
            rel="noreferrer noopener"
            className="text-accent underline underline-offset-2"
          >
            Parse Condition: Symbolic Encoding of LL(1) Parsing
          </a>
          .
        </p>
      </section>
    </div>
  );
}
