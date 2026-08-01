import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Team",
  description: "The people behind Cyclops.",
};

/**
 * Roles are only stated where they are known. Guessing an academic title is
 * worse than omitting it, so the remaining entries carry a name and a link.
 */
const TEAM = [
  {
    name: "Subhajit Roy",
    role: "Professor, CSE, IIT Kanpur",
    href: "https://www.cse.iitk.ac.in/users/subhajit/",
    linkLabel: "Homepage",
  },
  {
    name: "Pankaj Kalita",
    role: "",
    href: "https://www.cse.iitk.ac.in/users/pkalita/",
    linkLabel: "Homepage",
  },
  {
    name: "Sumit Lahiri",
    role: "",
    href: "https://www.cse.iitk.ac.in/users/sumitl/",
    linkLabel: "Homepage",
  },
  {
    name: "Shashvat Singham",
    role: "",
    href: "https://shashvat-singham.netlify.app/",
    linkLabel: "Portfolio",
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

      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {TEAM.map((person) => (
          <li key={person.name} className="card flex flex-col p-5">
            <p className="font-medium">{person.name}</p>
            {person.role && (
              <p className="mt-0.5 text-sm text-ink-secondary">{person.role}</p>
            )}
            <a
              href={person.href}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-auto pt-2 text-sm text-accent underline underline-offset-2"
            >
              {person.linkLabel}
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
